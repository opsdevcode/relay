from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx

from portal_assistant.catalog_ownership import OwnershipMatch, resolve_ownership
from portal_assistant.config import Settings, settings
from portal_assistant.registry import OnCallRegistry, OnCallTeamEntry, load_registry_config

ProviderName = str  # deeplink | pagerduty | opsgenie | none


@dataclass(frozen=True)
class OnCallResult:
    provider: str
    entity_name: str
    owner_team: str
    status: str
    on_call_users: tuple[str, ...]
    schedule_url: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "entity_name": self.entity_name,
            "owner_team": self.owner_team,
            "status": self.status,
            "on_call_users": list(self.on_call_users),
            "schedule_url": self.schedule_url,
            "note": self.note,
        }


def resolve_on_call_provider(cfg: Settings | None = None) -> str:
    raw = ((cfg or settings).on_call_provider or "deeplink").strip().lower()
    if raw in ("", "none", "off", "disabled"):
        return "none"
    if raw in ("deeplink", "link", "mock"):
        return "deeplink"
    if raw == "pagerduty":
        return "pagerduty"
    if raw == "opsgenie":
        return "opsgenie"
    msg = f"Unknown ON_CALL_PROVIDER {raw!r}; use deeplink, pagerduty, opsgenie, or none"
    raise ValueError(msg)


def on_call_live_configured(cfg: Settings | None = None) -> bool:
    conf = cfg or settings
    provider = resolve_on_call_provider(conf)
    if provider == "pagerduty":
        return bool((conf.pagerduty_api_token or "").strip())
    if provider == "opsgenie":
        return bool((conf.opsgenie_api_token or "").strip())
    return False


def _normalize_team(owner_ref: str) -> str:
    ref = owner_ref.strip()
    if ":" in ref:
        ref = ref.rsplit("/", 1)[-1]
    return ref.lower()


def _team_entry(owner_ref: str, on_call: OnCallRegistry | None) -> OnCallTeamEntry | None:
    if not on_call or not on_call.teams:
        return None
    key = _normalize_team(owner_ref)
    return on_call.teams.get(key)


def _annotation(entity: dict[str, Any], key: str) -> str:
    annotations = (entity.get("metadata") or {}).get("annotations") or {}
    return str(annotations.get(key) or "").strip()


def _apply_template(template: str, values: dict[str, str]) -> str:
    def replacer(match: re.Match[str]) -> str:
        return values.get(match.group(1), "")

    return re.sub(r"\{(\w+)\}", replacer, template)


def build_schedule_deeplink(
    *,
    owner_ref: str,
    entity: dict[str, Any],
    on_call: OnCallRegistry | None,
    cfg: Settings | None = None,
) -> str:
    conf = cfg or settings
    direct = _annotation(entity, "relay.dev/on-call-url")
    if direct:
        return direct
    team = _team_entry(owner_ref, on_call)
    template = (
        (on_call.url_template if on_call else "")
        or (conf.on_call_url_template or "").strip()
        or "https://example.pagerduty.com/schedules/{schedule_id}"
    )
    values = {
        "schedule_id": (team.schedule_id if team else "")
        or _annotation(entity, "pagerduty.com/service-id"),
        "escalation_policy_id": (team.pagerduty_escalation_policy_id if team else "")
        or _annotation(entity, "pagerduty.com/escalation-policy"),
        "service_id": _annotation(entity, "pagerduty.com/service-id"),
        "team": _normalize_team(owner_ref),
        "entity": str((entity.get("metadata") or {}).get("name") or ""),
    }
    url = _apply_template(template, values).strip()
    if url.startswith("http"):
        return url
    base = (conf.pagerduty_base_url or "").strip().rstrip("/")
    if base:
        return urljoin(base + "/", url.lstrip("/"))
    return url


async def _fetch_pagerduty_oncalls(
    escalation_policy_id: str,
    *,
    token: str,
    api_url: str,
    client: httpx.AsyncClient | None = None,
) -> tuple[str, ...]:
    if not escalation_policy_id or not token:
        return ()
    base = api_url.rstrip("/")
    url = f"{base}/oncalls"
    headers = {
        "Authorization": f"Token token={token}",
        "Accept": "application/vnd.pagerduty+json;version=2",
    }
    params = {
        "escalation_policy_ids[]": escalation_policy_id,
        "include[]": "users",
    }
    own_client = client is None
    http = client or httpx.AsyncClient(timeout=20.0)
    try:
        response = await http.get(url, headers=headers, params=params)
        response.raise_for_status()
        payload = response.json()
        users: list[str] = []
        for entry in payload.get("oncalls") or []:
            if not isinstance(entry, dict):
                continue
            user = entry.get("user")
            if not isinstance(user, dict):
                continue
            summary = str(user.get("summary") or user.get("name") or "").strip()
            email = str(user.get("email") or "").strip()
            if summary and email:
                users.append(f"{summary} <{email}>")
            elif summary:
                users.append(summary)
        return tuple(dict.fromkeys(users))
    finally:
        if own_client:
            await http.aclose()


async def fetch_on_call(
    query: str,
    *,
    cfg: Settings | None = None,
    ownership: OwnershipMatch | None = None,
) -> OnCallResult:
    conf = cfg or settings
    provider = resolve_on_call_provider(conf)
    match = ownership or resolve_ownership(query)
    if match is None:
        return OnCallResult(
            provider=provider,
            entity_name=query,
            owner_team="",
            status="unknown_entity",
            on_call_users=(),
            schedule_url="",
            note="No catalog entity matched; on-call lookup requires a catalog component.",
        )

    entity = match.entity
    entity_name = str((entity.get("metadata") or {}).get("name") or query)
    owner_team = match.owner_ref
    reg = load_registry_config()
    on_call = reg.on_call
    schedule_url = build_schedule_deeplink(
        owner_ref=owner_team,
        entity=entity,
        on_call=on_call,
        cfg=conf,
    )
    team = _team_entry(owner_team, on_call)
    escalation_id = (team.pagerduty_escalation_policy_id if team else "") or _annotation(
        entity, "pagerduty.com/escalation-policy"
    )

    if provider == "none":
        return OnCallResult(
            provider=provider,
            entity_name=entity_name,
            owner_team=owner_team,
            status="disabled",
            on_call_users=(),
            schedule_url=schedule_url,
            note="On-call integration disabled (ON_CALL_PROVIDER=none).",
        )

    if provider == "pagerduty":
        token = (conf.pagerduty_api_token or "").strip()
        if not token or not escalation_id:
            return OnCallResult(
                provider=provider,
                entity_name=entity_name,
                owner_team=owner_team,
                status="deeplink_only",
                on_call_users=(),
                schedule_url=schedule_url,
                note=(
                    "Set PAGERDUTY_API_TOKEN and registry/catalog escalation policy "
                    "for live on-call names."
                ),
            )
        users = await _fetch_pagerduty_oncalls(
            escalation_id,
            token=token,
            api_url=conf.pagerduty_api_url or "https://api.pagerduty.com",
        )
        return OnCallResult(
            provider=provider,
            entity_name=entity_name,
            owner_team=owner_team,
            status="live" if users else "empty",
            on_call_users=users,
            schedule_url=schedule_url,
            note="Live roster from PagerDuty API."
            if users
            else "PagerDuty returned no on-call users.",
        )

    if provider == "opsgenie":
        token = (conf.opsgenie_api_token or "").strip()
        if not token:
            return OnCallResult(
                provider=provider,
                entity_name=entity_name,
                owner_team=owner_team,
                status="deeplink_only",
                on_call_users=(),
                schedule_url=schedule_url,
                note="Set OPSGENIE_API_TOKEN for live Opsgenie roster (deeplink below).",
            )
        return OnCallResult(
            provider=provider,
            entity_name=entity_name,
            owner_team=owner_team,
            status="deeplink_only",
            on_call_users=(),
            schedule_url=schedule_url,
            note="Opsgenie live API hook reserved; use schedule deeplink for now.",
        )

    return OnCallResult(
        provider="deeplink",
        entity_name=entity_name,
        owner_team=owner_team,
        status="deeplink",
        on_call_users=(),
        schedule_url=schedule_url,
        note=(
            "Schedule deeplink from registry/catalog "
            "(set ON_CALL_PROVIDER=pagerduty for live names)."
        ),
    )


def extract_on_call_target(message: str) -> str:
    patterns = [
        (
            r"(?i)\b(?:on[- ]?call for|who(?:'s| is) on call for|paging for|page for)\s+"
            r"['\"]?([a-z0-9][a-z0-9_-]*)"
        ),
        r"(?i)\b([a-z0-9][a-z0-9_-]*)\s+on[- ]?call\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            slug = re.sub(r"[^a-z0-9-]+", "-", match.group(1).lower()).strip("-")
            if slug:
                return slug
    from portal_assistant.catalog_ownership import extract_ownership_target

    return extract_ownership_target(message)


def format_on_call_answer(result: OnCallResult) -> str:
    lines = [
        f"On-call for **{result.entity_name}** (owner **{result.owner_team}**):",
    ]
    if result.on_call_users:
        for user in result.on_call_users:
            lines.append(f"- {user}")
    elif result.status in {"live", "empty"}:
        lines.append("- _(no users returned from paging API)_")
    if result.schedule_url:
        lines.append(f"- Schedule: {result.schedule_url}")
    if result.note:
        lines.append(f"\n{result.note}")
    lines.append("\n(Source: catalog + optional paging API, not document search.)")
    return "\n".join(lines)
