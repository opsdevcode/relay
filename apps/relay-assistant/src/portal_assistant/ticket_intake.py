from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import quote, urljoin

import httpx

from portal_assistant.config import Settings, settings
from portal_assistant.user_context import UserContext

ProviderName = Literal["github_issue", "jira", "servicenow", "url_template"]


@dataclass(frozen=True)
class SandboxHandoff:
    status: str
    message: str
    intake_url: str
    provider: str
    ticket_id: str | None = None

    def as_response(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "status": self.status,
            "message": self.message,
            "intake_url": self.intake_url,
            "provider": self.provider,
        }
        if self.ticket_id:
            body["ticket_id"] = self.ticket_id
        # Backward compatibility for web UI and smoke scripts
        if self.provider == "github_issue":
            body["issue_url"] = self.intake_url
        return body


def resolve_ticket_intake_provider(cfg: Settings | None = None) -> ProviderName:
    raw = ((cfg or settings).ticket_intake_provider or "github_issue").strip().lower()
    if raw in ("github", "github_issue", "issue"):
        return "github_issue"
    if raw == "jira":
        return "jira"
    if raw in ("servicenow", "snow"):
        return "servicenow"
    if raw in ("url_template", "template", "deeplink"):
        return "url_template"
    msg = (
        f"Unknown TICKET_INTAKE_PROVIDER {raw!r}; "
        "use github_issue, jira, servicenow, or url_template"
    )
    raise ValueError(msg)


def _purpose_from_draft(draft: dict[str, Any]) -> str:
    purpose = str(draft.get("purpose") or draft.get("message") or "Sandbox request").strip()
    return purpose[:500] or "Sandbox request"


def _budget_from_draft(draft: dict[str, Any]) -> str:
    return str(draft.get("budget_usd_monthly") or "500").strip()


def _apply_url_template(template: str, draft: dict[str, Any], user: UserContext | None) -> str:
    purpose = _purpose_from_draft(draft)
    budget = _budget_from_draft(draft)
    requester = (user.email or user.subject if user else "").strip()
    replacements = {
        "purpose": quote(purpose, safe=""),
        "purpose_raw": purpose,
        "budget": quote(budget, safe=""),
        "budget_raw": budget,
        "requester": quote(requester, safe=""),
        "requester_raw": requester,
    }

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        return replacements.get(key, match.group(0))

    return re.sub(r"\{(\w+)\}", replacer, template)


def github_issue_handoff(draft: dict[str, Any], cfg: Settings | None = None) -> SandboxHandoff:
    conf = cfg or settings
    purpose = _purpose_from_draft(draft)
    title = quote(purpose[:80], safe="")
    url = (
        f"https://github.com/{conf.github_repo}/issues/new"
        "?template=sandbox-request.md"
        f"&title={title}"
    )
    return SandboxHandoff(
        status="issue_template",
        message="Open the GitHub issue template to file your sandbox request.",
        intake_url=url,
        provider="github_issue",
    )


def url_template_handoff(
    draft: dict[str, Any],
    *,
    user: UserContext | None = None,
    cfg: Settings | None = None,
) -> SandboxHandoff:
    conf = cfg or settings
    template = (conf.ticket_intake_url_template or "").strip()
    if not template:
        raise ValueError("TICKET_INTAKE_URL_TEMPLATE is required for url_template provider")
    url = _apply_url_template(template, draft, user)
    return SandboxHandoff(
        status="ticket_link",
        message="Open the ticket portal link to complete your sandbox request.",
        intake_url=url,
        provider="url_template",
    )


def _basic_auth_header(username: str, token: str) -> dict[str, str]:
    raw = f"{username}:{token}".encode()
    return {"Authorization": f"Basic {base64.b64encode(raw).decode('ascii')}"}


def _jira_deeplink(draft: dict[str, Any], cfg: Settings) -> SandboxHandoff:
    base = (cfg.ticket_intake_base_url or "").rstrip("/")
    project = (cfg.ticket_intake_project or "SANDBOX").strip()
    purpose = _purpose_from_draft(draft)
    summary = quote(f"[sandbox] {purpose[:80]}", safe="")
    url = f"{base}/secure/CreateIssue.jspa?pid=&project={quote(project)}&summary={summary}"
    return SandboxHandoff(
        status="ticket_link",
        message="Open Jira to create the sandbox request (API credentials not configured).",
        intake_url=url,
        provider="jira",
    )


async def jira_handoff(
    draft: dict[str, Any],
    *,
    user: UserContext | None = None,
    cfg: Settings | None = None,
) -> SandboxHandoff:
    conf = cfg or settings
    base = (conf.ticket_intake_base_url or "").rstrip("/")
    if not base:
        raise ValueError("TICKET_INTAKE_BASE_URL is required for jira provider")

    token = (conf.ticket_intake_api_token or "").strip()
    username = (conf.ticket_intake_username or "").strip()
    project = (conf.ticket_intake_project or "").strip()
    if not token or not username or not project:
        return _jira_deeplink(draft, conf)

    purpose = _purpose_from_draft(draft)
    budget = _budget_from_draft(draft)
    requester = user.email or user.subject if user else "unknown"
    description = f"Purpose: {purpose}\nBudget (USD/mo): {budget}\nRequester: {requester}"

    payload = {
        "fields": {
            "project": {"key": project},
            "summary": f"[sandbox] {purpose[:80]}",
            "description": description,
            "issuetype": {"name": conf.ticket_intake_issue_type or "Task"},
        }
    }
    url = urljoin(f"{base}/", "rest/api/2/issue")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={**_basic_auth_header(username, token), "Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    key = str(data.get("key") or "")
    ticket_url = f"{base}/browse/{key}" if key else base
    return SandboxHandoff(
        status="ticket_created",
        message=f"Created Jira issue **{key}** for your sandbox request.",
        intake_url=ticket_url,
        provider="jira",
        ticket_id=key or None,
    )


def _servicenow_deeplink(draft: dict[str, Any], cfg: Settings) -> SandboxHandoff:
    base = (cfg.ticket_intake_base_url or "").rstrip("/")
    purpose = quote(_purpose_from_draft(draft), safe="")
    url = f"{base}/sp?id=sc_cat_item&sysparm_description={purpose}"
    return SandboxHandoff(
        status="ticket_link",
        message="Open ServiceNow to complete the sandbox catalog request (API not configured).",
        intake_url=url,
        provider="servicenow",
    )


async def servicenow_handoff(
    draft: dict[str, Any],
    *,
    user: UserContext | None = None,
    cfg: Settings | None = None,
) -> SandboxHandoff:
    conf = cfg or settings
    base = (conf.ticket_intake_base_url or "").rstrip("/")
    if not base:
        raise ValueError("TICKET_INTAKE_BASE_URL is required for servicenow provider")

    token = (conf.ticket_intake_api_token or "").strip()
    username = (conf.ticket_intake_username or "").strip()
    if not token or not username:
        return _servicenow_deeplink(draft, conf)

    purpose = _purpose_from_draft(draft)
    budget = _budget_from_draft(draft)
    requester = user.email or user.subject if user else "unknown"
    table = (conf.ticket_intake_project or "incident").strip()
    payload = {
        "short_description": f"[sandbox] {purpose[:80]}",
        "description": f"Purpose: {purpose}\nBudget (USD/mo): {budget}\nRequester: {requester}",
        "category": "inquiry",
    }
    url = urljoin(f"{base}/", f"api/now/table/{table}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={**_basic_auth_header(username, token), "Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    result = data.get("result") or {}
    sys_id = str(result.get("sys_id") or "")
    number = str(result.get("number") or "")
    ticket_url = f"{base}/nav_to.do?uri=/{table}.do?sys_id={sys_id}" if sys_id else base
    return SandboxHandoff(
        status="ticket_created",
        message=f"Created ServiceNow record **{number or sys_id}** for your sandbox request.",
        intake_url=ticket_url,
        provider="servicenow",
        ticket_id=number or sys_id or None,
    )


async def handoff_sandbox_request(
    draft: dict[str, Any],
    *,
    user: UserContext | None = None,
    cfg: Settings | None = None,
) -> SandboxHandoff:
    conf = cfg or settings
    provider = resolve_ticket_intake_provider(conf)
    if provider == "github_issue":
        return github_issue_handoff(draft, conf)
    if provider == "url_template":
        return url_template_handoff(draft, user=user, cfg=conf)
    if provider == "jira":
        return await jira_handoff(draft, user=user, cfg=conf)
    return await servicenow_handoff(draft, user=user, cfg=conf)
