"""Retrieval ABAC — filter indexed chunks by visibility and user groups (Phase 2D.1)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from portal_assistant.config import Settings, settings
from portal_assistant.user_context import UserContext


class AccessMode(StrEnum):
    NONE = "none"
    PUBLIC_ONLY = "public_only"
    AUTHENTICATED = "authenticated"
    PRINCIPALS = "principals"


def abac_should_filter(user: UserContext | None, cfg: Settings | None = None) -> bool:
    conf = cfg or settings
    return bool(conf.retrieval_abac_enabled) or user is not None


def resolve_access_mode(
    user: UserContext | None,
    *,
    cfg: Settings | None = None,
) -> tuple[AccessMode, list[Any]]:
    conf = cfg or settings
    if not abac_should_filter(user, conf):
        return AccessMode.NONE, []

    principals = user.retrieval_principals() if user else []
    authenticated = user is not None and bool((user.subject or user.email or "").strip())

    if principals:
        return AccessMode.PRINCIPALS, [principals, principals]
    if authenticated:
        return AccessMode.AUTHENTICATED, []
    return AccessMode.PUBLIC_ONLY, []


def access_where_clause(
    user: UserContext | None,
    *,
    cfg: Settings | None = None,
) -> tuple[str, list[Any]]:
    """Return SQL suffix `` AND (...)`` and bind parameters (for tests / introspection)."""
    mode, params = resolve_access_mode(user, cfg=cfg)
    if mode is AccessMode.NONE:
        return "", []
    if mode is AccessMode.PUBLIC_ONLY:
        return " AND (visibility = 'public')", []
    if mode is AccessMode.AUTHENTICATED:
        return " AND (visibility = 'public' OR visibility = 'internal')", []
    return (
        " AND (visibility = 'public' OR visibility = 'internal'"
        " OR (visibility = 'restricted' AND doc_owner = ANY(%s))"
        " OR (visibility = 'restricted' AND allowed_groups && %s::text[]))",
        params,
    )
