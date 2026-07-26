from __future__ import annotations

from fastapi import HTTPException

from portal_assistant.config import settings
from portal_assistant.registry import RegistryConfig, ToolDefinition, load_registry_config
from portal_assistant.user_context import UserContext


def _allowed_groups_for_tool(tool_def: ToolDefinition) -> frozenset[str]:
    if tool_def.confirm_allowed_groups:
        return frozenset(tool_def.confirm_allowed_groups)
    raw = settings.confirm_allowed_groups.strip()
    if raw:
        return frozenset(part.strip() for part in raw.split(",") if part.strip())
    return frozenset()


def user_may_confirm(
    user: UserContext | None,
    action: str,
    *,
    config: RegistryConfig | None = None,
) -> bool:
    if not settings.confirm_action_authorization_enabled:
        return True
    if user is None:
        return False
    cfg = config or load_registry_config()
    tool_def = cfg.tool_definition(action)
    if tool_def.kind != "write":
        return False
    allowed = _allowed_groups_for_tool(tool_def)
    if not allowed:
        return False
    return bool(set(user.groups) & allowed)


def require_confirm_authorization(
    user: UserContext | None,
    action: str,
    *,
    config: RegistryConfig | None = None,
) -> None:
    if not settings.confirm_action_authorization_enabled:
        return
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to confirm actions",
        )
    cfg = config or load_registry_config()
    tool_def = cfg.tool_definition(action)
    if tool_def.kind != "write":
        raise HTTPException(status_code=400, detail=f"Action {action} is not confirmable")
    allowed = _allowed_groups_for_tool(tool_def)
    if not allowed:
        raise HTTPException(
            status_code=503,
            detail="Confirm authorization is enabled but no allowed groups are configured",
        )
    if not set(user.groups) & allowed:
        raise HTTPException(
            status_code=403,
            detail="Not entitled to confirm this action",
        )
