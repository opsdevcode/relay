from __future__ import annotations

import re

from portal_assistant.config import settings

WORKFLOW_FILE = "scaffold-k8s-service.yml"


def normalize_service_name(raw: str) -> str:
    name = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")
    if not name or not re.match(r"^[a-z][a-z0-9-]{1,62}$", name):
        raise ValueError("service_name must be kebab-case (lowercase letters, numbers, hyphens)")
    return name


def build_workflow_dispatch(service_name: str, description: str = "") -> dict:
    """Return GitHub Actions workflow link + inputs (no tokens required in the portal)."""
    service_name = normalize_service_name(service_name)
    desc = description.strip() or f"Scaffolded service {service_name}"
    repo = settings.github_repo
    workflow_url = f"https://github.com/{repo}/actions/workflows/{WORKFLOW_FILE}"

    inputs = {
        "service_name": service_name,
        "description": desc,
        "github_org": settings.github_org,
    }

    return {
        "action": "scaffold_service",
        "mode": "workflow_dispatch",
        "workflow_url": workflow_url,
        "workflow_name": "Scaffold K8s Service",
        "inputs": inputs,
        "instructions": (
            f"1. Open **Run workflow**: {workflow_url}\n"
            f"2. Set **service_name** to `{service_name}`\n"
            f"3. Set **description** to `{desc}`\n"
            f"4. Click **Run workflow** — Actions opens a PR under "
            f"`examples/services/{service_name}/`"
        ),
        "message": (
            f"Ready to scaffold **`{service_name}`**. "
            "Confirm to get the GitHub Actions **Run workflow** link (no tokens in this app)."
        ),
    }


def confirm_scaffold_draft(draft: dict) -> dict:
    inputs = draft.get("inputs") or {}
    service_name = draft.get("service_name") or inputs.get("service_name") or "demo-service"
    description = draft.get("description") or inputs.get("description") or ""
    payload = build_workflow_dispatch(service_name, description)
    return {
        "status": "workflow_dispatch",
        "message": payload["instructions"],
        "workflow_url": payload["workflow_url"],
        "workflow_name": payload["workflow_name"],
        "inputs": payload["inputs"],
    }
