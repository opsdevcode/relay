from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urljoin

import httpx

from portal_assistant.config import Settings, settings
from portal_assistant.registry import ObservabilityRegistry, load_registry_config

ProviderName = Literal["mock", "grafana_deeplink", "prometheus"]

DEFAULT_ALERTS_QUERY = 'count(ALERTS{alertstate="firing",service="{service}"})'


def _slug(service_name: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", service_name.lower()).strip("-") or "demo-service"


def resolve_observability_provider(cfg: Settings | None = None) -> ProviderName:
    conf = cfg or settings
    raw = (conf.observability_provider or "").strip().lower()
    if raw in ("mock", "none"):
        return "mock"
    if raw in ("grafana", "grafana_deeplink", "deeplink"):
        return "grafana_deeplink"
    if raw in ("prometheus", "prom"):
        return "prometheus"
    if raw:
        msg = f"Unknown OBSERVABILITY_PROVIDER '{raw}' (use mock, grafana_deeplink, or prometheus)"
        raise ValueError(msg)
    if (conf.grafana_base_url or "").strip():
        return "grafana_deeplink"
    if (conf.prometheus_base_url or "").strip():
        return "prometheus"
    return "mock"


def observability_metrics_configured(cfg: Settings | None = None) -> bool:
    return bool(((cfg or settings).prometheus_base_url or "").strip())


@dataclass(frozen=True)
class LiveMetrics:
    alert_count: int
    burn_rate: str | None
    live: bool
    note: str | None = None


@dataclass(frozen=True)
class ServiceHealthResult:
    service: str
    mode: ProviderName
    status: str
    slo: dict[str, str | None]
    alerts: list[dict[str, Any]]
    grafana_url: str | None
    catalog_match: bool
    metrics_live: bool = False
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "mode": self.mode,
            "status": self.status,
            "slo": self.slo,
            "alerts": self.alerts,
            "grafana_url": self.grafana_url,
            "catalog_match": self.catalog_match,
            "metrics_live": self.metrics_live,
            "note": self.note,
        }


def _catalog_entry(service_slug: str, obs: ObservabilityRegistry | None) -> tuple[bool, str, str]:
    """Return (matched, dashboard_uid, slo_target)."""
    if not obs:
        return False, "", ""
    entry = obs.catalog.get(service_slug)
    if entry:
        uid = (entry.dashboard_uid or "").strip()
        slo = (entry.slo_target or "99.9%").strip()
        return True, uid, slo
    return False, "", ""


def _query_templates(
    conf: Settings,
    obs: ObservabilityRegistry | None,
) -> tuple[str, str]:
    alerts_tpl = (
        (obs.prometheus_alerts_query_template if obs else "")
        or (conf.prometheus_alerts_query_template or "").strip()
        or DEFAULT_ALERTS_QUERY
    )
    burn_tpl = (obs.prometheus_burn_rate_query_template if obs else "") or (
        conf.prometheus_burn_rate_query_template or ""
    ).strip()
    return alerts_tpl, burn_tpl


def build_grafana_url(
    *,
    service_slug: str,
    dashboard_uid: str,
    cfg: Settings | None = None,
    obs: ObservabilityRegistry | None = None,
    path_template: str | None = None,
) -> str | None:
    conf = cfg or settings
    base = (conf.grafana_base_url or "").strip()
    if not base or not dashboard_uid:
        return None
    resolved_template = (
        path_template
        or (obs.grafana_path_template if obs else "")
        or (conf.grafana_dashboard_path_template or "").strip()
        or "/d/{dashboard_uid}?var-service={service}"
    )
    path = resolved_template.format(dashboard_uid=dashboard_uid, service=service_slug)
    if not path.startswith("/"):
        path = f"/{path}"
    return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


def build_grafana_embed_url(
    *,
    service_slug: str,
    dashboard_uid: str,
    cfg: Settings | None = None,
    obs: ObservabilityRegistry | None = None,
) -> str | None:
    embed_template = (
        (obs.grafana_embed_path_template if obs else "")
        or (cfg or settings).grafana_embed_path_template
        or ""
    ).strip()
    if not embed_template and obs:
        embed_template = obs.grafana_path_template
    return build_grafana_url(
        service_slug=service_slug,
        dashboard_uid=dashboard_uid,
        cfg=cfg,
        obs=obs,
        path_template=embed_template or None,
    )


def _expand_query(template: str, service_slug: str) -> str:
    return template.replace("{service_name}", service_slug).replace("{service}", service_slug)


async def _prometheus_scalar(
    *,
    base_url: str,
    token: str,
    query: str,
    timeout: float = 10.0,
) -> float | None:
    url = f"{base_url.rstrip('/')}/api/v1/query"
    headers: dict[str, str] = {}
    if token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, params={"query": query}, headers=headers)
        response.raise_for_status()
        payload = response.json()
    if payload.get("status") != "success":
        return None
    result = payload.get("data", {}).get("result") or []
    if not result:
        return 0.0
    value = result[0].get("value")
    if not isinstance(value, list) or len(value) < 2:
        return None
    try:
        return float(value[1])
    except (TypeError, ValueError):
        return None


async def fetch_live_metrics(
    service_slug: str,
    *,
    cfg: Settings | None = None,
    obs: ObservabilityRegistry | None = None,
) -> LiveMetrics:
    conf = cfg or settings
    prom_base = (conf.prometheus_base_url or "").strip()
    if not prom_base:
        return LiveMetrics(alert_count=0, burn_rate=None, live=False)

    alerts_tpl, burn_tpl = _query_templates(conf, obs)
    token = conf.prometheus_api_token or ""
    alert_count = 0
    burn_rate: str | None = None
    try:
        scalar = await _prometheus_scalar(
            base_url=prom_base,
            token=token,
            query=_expand_query(alerts_tpl, service_slug),
        )
        if scalar is not None:
            alert_count = int(scalar)
        if burn_tpl:
            burn_val = await _prometheus_scalar(
                base_url=prom_base,
                token=token,
                query=_expand_query(burn_tpl, service_slug),
            )
            if burn_val is not None:
                burn_rate = f"{burn_val:.2f}"
    except httpx.HTTPError as exc:
        return LiveMetrics(
            alert_count=0,
            burn_rate=None,
            live=False,
            note=f"Prometheus query failed: {exc}",
        )

    return LiveMetrics(alert_count=alert_count, burn_rate=burn_rate, live=True)


def _status_from_metrics(base_status: str, metrics: LiveMetrics) -> str:
    if not metrics.live:
        return base_status
    if metrics.alert_count > 0:
        return "degraded"
    if base_status in {"mock", "unknown", "unlisted", "catalog"}:
        return "ok"
    return base_status


def _alerts_from_metrics(metrics: LiveMetrics) -> list[dict[str, Any]]:
    if not metrics.live or metrics.alert_count <= 0:
        return []
    return [{"severity": "firing", "count": metrics.alert_count}]


async def fetch_service_health(
    service_name: str,
    *,
    cfg: Settings | None = None,
    obs_registry: ObservabilityRegistry | None = None,
) -> ServiceHealthResult:
    conf = cfg or settings
    provider = resolve_observability_provider(conf)
    slug = _slug(service_name)
    reg = load_registry_config()
    obs = obs_registry if obs_registry is not None else reg.observability
    matched, catalog_uid, catalog_slo = _catalog_entry(slug, obs)
    dashboard_uid = catalog_uid or (conf.grafana_default_dashboard_uid or "").strip()
    slo_target = catalog_slo or "99.9%"

    if provider == "mock":
        return ServiceHealthResult(
            service=slug,
            mode="mock",
            status="mock",
            slo={"target": slo_target, "burn_rate": "n/a", "window": "30d"},
            alerts=[],
            grafana_url=None,
            catalog_match=matched,
            note="Set GRAFANA_BASE_URL or PROMETHEUS_BASE_URL for live insight.",
        )

    grafana_url = build_grafana_url(
        service_slug=slug,
        dashboard_uid=dashboard_uid,
        cfg=conf,
        obs=obs,
    )
    metrics = await fetch_live_metrics(slug, cfg=conf, obs=obs)

    if provider == "grafana_deeplink":
        if not grafana_url:
            return ServiceHealthResult(
                service=slug,
                mode="grafana_deeplink",
                status="unknown",
                slo={"target": slo_target, "burn_rate": metrics.burn_rate, "window": "30d"},
                alerts=_alerts_from_metrics(metrics),
                grafana_url=None,
                catalog_match=matched,
                metrics_live=metrics.live,
                note=metrics.note
                or (
                    "Configure GRAFANA_BASE_URL and a dashboard uid "
                    "(observability.catalog or GRAFANA_DEFAULT_DASHBOARD_UID)."
                ),
            )
        base_status = "catalog" if matched else "unlisted"
        note = metrics.note
        if not note and not matched:
            note = "Service not in observability catalog; using default dashboard."
        if not metrics.live and not note:
            note = "Set PROMETHEUS_BASE_URL for live burn rate and alert counts."
        return ServiceHealthResult(
            service=slug,
            mode="grafana_deeplink",
            status=_status_from_metrics(base_status, metrics),
            slo={"target": slo_target, "burn_rate": metrics.burn_rate, "window": "30d"},
            alerts=_alerts_from_metrics(metrics),
            grafana_url=grafana_url,
            catalog_match=matched,
            metrics_live=metrics.live,
            note=note,
        )

    prom_note = metrics.note
    if not prom_note and not metrics.live:
        prom_note = "Set PROMETHEUS_BASE_URL for live metrics."

    return ServiceHealthResult(
        service=slug,
        mode="prometheus",
        status=_status_from_metrics("ok", metrics),
        slo={
            "target": slo_target,
            "burn_rate": metrics.burn_rate,
            "window": "30d",
        },
        alerts=_alerts_from_metrics(metrics),
        grafana_url=grafana_url,
        catalog_match=matched,
        metrics_live=metrics.live,
        note=prom_note,
    )


def format_service_health_answer(health: ServiceHealthResult | dict[str, Any]) -> str:
    data = health.as_dict() if isinstance(health, ServiceHealthResult) else health
    mode = data.get("mode", "")
    metrics_live = bool(data.get("metrics_live"))
    title = f"**{data['service']}**"
    if metrics_live:
        title += " — SLO summary (live)"
    else:
        title += f" ({mode})"
    lines = [title]
    slo = data.get("slo") or {}
    window = slo.get("window") or "30d"
    if slo.get("target"):
        lines.append(f"- SLO target: {slo['target']} ({window})")
    burn = slo.get("burn_rate")
    if metrics_live:
        lines.append(f"- Burn rate: {burn if burn else 'unavailable'}")
        alerts = data.get("alerts") or []
        count = 0
        if alerts:
            count = int(alerts[0].get("count") or 0)
        lines.append(f"- Firing alerts: {count}")
        status = data.get("status")
        if status and status not in {"mock"}:
            lines.append(f"- Status: {status}")
    elif burn and burn != "n/a":
        lines.append(f"- Burn rate: {burn}")
    elif mode == "mock":
        lines.append(f"- Burn rate: {burn or 'n/a'}")
    else:
        alerts = data.get("alerts") or []
        for alert in alerts:
            count = alert.get("count")
            if count is not None:
                lines.append(f"- Firing alerts: {count}")
    url = data.get("grafana_url")
    if url:
        lines.append(f"- Grafana: {url}")
    note = data.get("note")
    if note:
        lines.append(f"- {note}")
    return "\n".join(lines)
