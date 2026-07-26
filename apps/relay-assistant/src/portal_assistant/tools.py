from __future__ import annotations

import re

from portal_assistant.audit_log import EVENT_RETRIEVAL, AuditActor, AuditLogStore
from portal_assistant.catalog_ownership import (
    extract_ownership_target,
    format_ownership_answer,
    resolve_ownership,
)
from portal_assistant.llm import synthesize
from portal_assistant.observability import fetch_service_health, format_service_health_answer
from portal_assistant.on_call import extract_on_call_target, fetch_on_call, format_on_call_answer
from portal_assistant.registry import REGISTERED_TOOL_IDS
from portal_assistant.risk_tiers import SCAFFOLD_SERVICE_PATH_PREFIX, draft_risk_metadata
from portal_assistant.scaffold import build_workflow_dispatch
from portal_assistant.store import DocumentStore
from portal_assistant.user_context import UserContext


def load_registry() -> list[dict]:
    from portal_assistant.views import load_platform_services

    return load_platform_services()


def list_platform_services() -> str:
    services = load_registry()
    if not services:
        return "No platform services registered."
    lines = ["Registered platform services:"]
    for svc in services:
        lines.append(f"- **{svc['name']}** ({svc['id']}, phase {svc.get('phase', '?')})")
        lines.append(f"  {svc.get('description', '')}")
        tools = svc.get("tools") or []
        if tools:
            lines.append(f"  Tools: {', '.join(tools)}")
    return "\n".join(lines)


def extract_service_name(message: str) -> str:
    quoted = re.search(r"['\"]([^'\"]+)['\"]", message)
    if quoted:
        return slugify_name(quoted.group(1))
    tokens = re.findall(r"\b[a-z][a-z0-9-]{2,}\b", message.lower())
    skip = {"create", "service", "scaffold", "called", "named", "new", "the", "for", "please"}
    for token in tokens:
        if token not in skip:
            return str(token)
    return "demo-service"


def slugify_name(name: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-") or "demo-service"


def draft_scaffold(service_name: str, description: str = "") -> dict:
    payload = build_workflow_dispatch(service_name, description)
    name = payload["inputs"]["service_name"]
    meta = draft_risk_metadata(
        change_kind="scaffold_service",
        target_paths=[f"{SCAFFOLD_SERVICE_PATH_PREFIX}{name}/"],
    )
    return {
        **payload,
        **meta,
        "status": "draft",
        "requires_confirmation": True,
    }


def draft_sandbox_request(purpose: str, budget: str = "500") -> dict:
    meta = draft_risk_metadata(
        change_kind="request_sandbox",
        target_paths=[".github/ISSUE_TEMPLATE/sandbox-request.md"],
    )
    return {
        "action": "request_sandbox",
        **meta,
        "status": "draft",
        "purpose": purpose,
        "budget_usd_monthly": budget,
        "message": (
            f"Draft: sandbox request for '{purpose}' (~${budget}/mo). "
            f"Confirm to file intake (tier **{meta['risk_tier']}**: {meta['review_requirements']})."
        ),
        "requires_confirmation": True,
    }


async def dispatch_tool(
    tool_id: str,
    message: str,
    store: DocumentStore,
    *,
    user: UserContext | None = None,
    audit: AuditLogStore | None = None,
    thread_id: str | None = None,
) -> dict:
    if tool_id not in REGISTERED_TOOL_IDS:
        return {
            "answer": f"Tool '{tool_id}' is not allow-listed for this assistant.",
            "citations": [],
            "draft": None,
        }

    if tool_id == "list_platform_services":
        return {"answer": list_platform_services(), "citations": [], "draft": None}

    if tool_id == "scaffold_service":
        name = extract_service_name(message)
        draft = draft_scaffold(name)
        return {"answer": draft["message"], "citations": [], "draft": draft}

    if tool_id == "request_sandbox":
        draft = draft_sandbox_request(message[:200])
        return {"answer": draft["message"], "citations": [], "draft": draft}

    if tool_id == "service_health":
        name = extract_service_name(message)
        health = await fetch_service_health(name)
        return {
            "answer": format_service_health_answer(health),
            "citations": [],
            "draft": None,
        }

    if tool_id == "catalog_ownership":
        target = extract_ownership_target(message)
        match = resolve_ownership(target)
        return {
            "answer": format_ownership_answer(match, query=target),
            "citations": [],
            "draft": None,
        }

    if tool_id == "on_call_lookup":
        target = extract_on_call_target(message)
        result = await fetch_on_call(target)
        return {
            "answer": format_on_call_answer(result),
            "citations": [],
            "draft": None,
        }

    if tool_id == "docs_search":
        hits = store.search(message, user=user)
        citations = [{"source": h["source"], "title": h["title"]} for h in hits]
        if audit:
            audit.record(
                EVENT_RETRIEVAL,
                payload={
                    "query_preview": message[:500],
                    "sources": [c["source"] for c in citations],
                    "hit_count": len(citations),
                },
                thread_id=thread_id,
                actor=AuditActor.from_user(user),
                tool_id=tool_id,
            )
        answer = await synthesize(message, hits)
        return {"answer": answer, "citations": citations, "draft": None}

    return {
        "answer": f"Unknown tool '{tool_id}' — check platform-service registry routing.",
        "citations": [],
        "draft": None,
    }
