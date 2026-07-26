from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from portal_assistant.audit_log import AuditLogStore
from portal_assistant.registry import RegistryConfig, load_registry_config, resolve_tool
from portal_assistant.sessions import apply_follow_up_refinement
from portal_assistant.store import DocumentStore
from portal_assistant.tools import dispatch_tool
from portal_assistant.user_context import UserContext

# Draft fields safe to round-trip through /chat → confirm (no live URLs until confirm).
WRITE_DRAFT_CLIENT_KEYS: frozenset[str] = frozenset(
    {
        "action",
        "mode",
        "status",
        "message",
        "requires_confirmation",
        "inputs",
        "purpose",
        "budget_usd_monthly",
        "risk_tier",
        "risk_tier_label",
        "review_requirements",
        "codeowners",
        "change_paths",
    }
)


@dataclass(frozen=True)
class GraphTrace:
    path: str
    tool_id: str


def enforce_write_tool_result(tool_id: str, result: dict[str, Any]) -> dict[str, Any]:
    draft = result.get("draft")
    if not isinstance(draft, dict):
        return {
            "answer": (
                f"Write tool `{tool_id}` must produce a confirmation draft; "
                "no side effects were applied."
            ),
            "citations": [],
            "draft": None,
        }

    sanitized = {k: v for k, v in draft.items() if k in WRITE_DRAFT_CLIENT_KEYS}
    sanitized["requires_confirmation"] = True
    sanitized["status"] = "draft"

    return {
        "answer": result.get("answer", ""),
        "citations": result.get("citations") or [],
        "draft": sanitized,
    }


async def run_chat_graph(
    message: str,
    store: DocumentStore,
    *,
    prior_turns: list[dict[str, Any]] | None = None,
    config: RegistryConfig | None = None,
    user: UserContext | None = None,
    audit: AuditLogStore | None = None,
    thread_id: str | None = None,
) -> tuple[dict[str, Any], GraphTrace]:
    """Deterministic chat pipeline: refine → route → execute → write guard."""
    cfg = config or load_registry_config()
    turns = prior_turns or []

    effective_message = apply_follow_up_refinement(message, turns)
    tool_id = resolve_tool(effective_message, cfg)
    tool_def = cfg.tool_definition(tool_id)

    raw = await dispatch_tool(
        tool_id, effective_message, store, user=user, audit=audit, thread_id=thread_id
    )

    if tool_def.kind == "write":
        guarded = enforce_write_tool_result(tool_id, raw)
        return guarded, GraphTrace(path="write", tool_id=tool_id)

    return raw, GraphTrace(path="read", tool_id=tool_id)
