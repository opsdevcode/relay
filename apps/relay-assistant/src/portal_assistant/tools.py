from __future__ import annotations

import re

from portal_assistant.llm import synthesize
from portal_assistant.registry import load_registry_config
from portal_assistant.scaffold import build_workflow_dispatch
from portal_assistant.store import DocumentStore
from portal_assistant.user_context import UserContext


def load_registry() -> list[dict]:
    return load_registry_config().services


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


def service_health(service_name: str) -> dict:
    return {
        "service": service_name,
        "status": "mock",
        "slo": {"target": "99.9%", "burn_rate": "0.2", "window": "30d"},
        "alerts": [],
        "note": "Connect observability MCP tool to your metrics stack in production.",
    }


def draft_scaffold(service_name: str, description: str = "") -> dict:
    payload = build_workflow_dispatch(service_name, description)
    return {
        **payload,
        "status": "draft",
        "requires_confirmation": True,
    }


def draft_sandbox_request(purpose: str, budget: str = "500") -> dict:
    return {
        "action": "request_sandbox",
        "status": "draft",
        "purpose": purpose,
        "budget_usd_monthly": budget,
        "message": (
            f"Draft: sandbox request for '{purpose}' (~${budget}/mo). "
            "Confirm to file a GitHub Issue (ticket-system intake in production)."
        ),
        "requires_confirmation": True,
    }


async def dispatch_tool(
    tool_id: str,
    message: str,
    store: DocumentStore,
    *,
    user: UserContext | None = None,
) -> dict:
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
        health = service_health(name)
        return {
            "answer": (
                f"**{health['service']}** (mock insight)\n"
                f"- SLO target: {health['slo']['target']}\n"
                f"- Burn rate: {health['slo']['burn_rate']}\n"
                f"- {health['note']}"
            ),
            "citations": [],
            "draft": None,
        }

    if tool_id == "docs_search":
        hits = store.search(message, user=user)
        citations = [{"source": h["source"], "title": h["title"]} for h in hits]
        answer = await synthesize(message, hits)
        return {"answer": answer, "citations": citations, "draft": None}

    return {
        "answer": f"Unknown tool '{tool_id}' — check platform-service registry routing.",
        "citations": [],
        "draft": None,
    }
