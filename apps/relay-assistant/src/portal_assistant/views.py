from __future__ import annotations

from typing import Any

from portal_assistant.config import Settings, settings
from portal_assistant.observability import _catalog_entry, build_grafana_embed_url
from portal_assistant.registry import RegistryConfig, load_registry_config

GRAFANA_EMBED_VIEW = "grafana-embed"


def resolve_grafana_embed_view(
    *,
    cfg: Settings | None = None,
    reg: RegistryConfig | None = None,
    service_slug: str | None = None,
) -> dict[str, Any]:
    """Build embed payload for the observability Grafana panel."""
    conf = cfg or settings
    registry = reg or load_registry_config()
    obs = registry.observability
    slug = (service_slug or "").strip().lower()
    if not slug and obs:
        slug = obs.default_embed_service
    if not slug:
        slug = "demo-api"

    matched, catalog_uid, slo_target = _catalog_entry(slug, obs)
    dashboard_uid = catalog_uid or (conf.grafana_default_dashboard_uid or "").strip()
    embed_template = (
        (obs.grafana_embed_path_template if obs else "") or conf.grafana_embed_path_template or ""
    ).strip()

    url = build_grafana_embed_url(
        service_slug=slug,
        dashboard_uid=dashboard_uid,
        cfg=conf,
        obs=obs,
    )
    payload: dict[str, Any] = {
        "service": slug,
        "dashboard_uid": dashboard_uid or None,
        "slo_target": slo_target or None,
        "catalog_match": matched,
        "path_template": embed_template or None,
    }
    if url:
        payload["url"] = url
        payload["configured"] = True
    else:
        payload["configured"] = False
        payload["hint"] = (
            "Set GRAFANA_BASE_URL and a dashboard uid "
            "(observability.catalog or GRAFANA_DEFAULT_DASHBOARD_UID)."
        )
    if obs and obs.catalog:
        payload["catalog_services"] = [
            {"slug": slug, "label": slug} for slug in sorted(obs.catalog.keys())
        ]
    return payload


def enrich_service_views(
    service: dict[str, Any],
    *,
    cfg: Settings | None = None,
    reg: RegistryConfig | None = None,
) -> dict[str, Any]:
    enriched = dict(service)
    views = service.get("views") or []
    if not isinstance(views, list):
        return enriched

    view_urls: dict[str, Any] = {}
    if GRAFANA_EMBED_VIEW in views:
        view_urls["grafana_embed"] = resolve_grafana_embed_view(cfg=cfg, reg=reg)

    if view_urls:
        enriched["view_urls"] = view_urls
    return enriched


def load_platform_services(*, cfg: Settings | None = None) -> list[dict[str, Any]]:
    registry = load_registry_config()
    conf = cfg or settings
    return [enrich_service_views(svc, cfg=conf, reg=registry) for svc in registry.services]
