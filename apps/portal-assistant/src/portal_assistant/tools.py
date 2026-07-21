from __future__ import annotations

from pathlib import Path

import yaml

from portal_assistant.scaffold import build_workflow_dispatch


def load_registry() -> list[dict]:
    path = Path(__file__).resolve().parents[4] / "packages" / "platform-services" / "registry.yaml"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or []
    return data if isinstance(data, list) else []


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


def service_health(service_name: str) -> dict:
    # Mock for working model — swap for Grafana/VM integration in prod
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
            "Confirm to file a GitHub Issue (ServiceNow in production)."
        ),
        "requires_confirmation": True,
    }
