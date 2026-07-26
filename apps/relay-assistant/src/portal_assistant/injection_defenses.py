"""Prompt-injection defenses, output moderation, and chat kill switch (Phase 2D.3)."""

from __future__ import annotations

import re

from portal_assistant.config import Settings, settings
from portal_assistant.registry import REGISTERED_TOOL_IDS, RegistryConfig

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        r"(?i)ignore (all )?(previous|prior|above) instructions",
        r"(?i)disregard (the )?(system|developer) (prompt|message|instructions)",
        r"(?i)you are now (in )?(\w+ )?mode",
        r"(?i)reveal (the )?(system|hidden) prompt",
        r"(?i)jailbreak",
    )
)

_OUTPUT_BLOCK_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        r"(?i)<script\b",
        r"javascript:",
        r"(?i)ignore (all )?(previous|prior) instructions",
    )
)

_MODERATION_REPLACEMENT = (
    "Response withheld by output moderation. "
    "Rephrase your question or contact the platform team if this seems wrong."
)


def is_chat_enabled(cfg: Settings | None = None) -> bool:
    conf = cfg or settings
    return not bool(conf.chat_kill_switch)


def message_has_injection_risk(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


def guard_tool_selection(
    message: str,
    tool_id: str,
    config: RegistryConfig,
    *,
    cfg: Settings | None = None,
) -> str:
    """Enforce registry tool allow-list and block write routing on injection-shaped prompts."""
    conf = cfg or settings
    if tool_id not in REGISTERED_TOOL_IDS:
        return "docs_search"
    if not conf.injection_defense_enabled:
        return tool_id
    if message_has_injection_risk(message) and config.tool_definition(tool_id).kind == "write":
        return "docs_search"
    return tool_id


def moderate_assistant_output(text: str, *, cfg: Settings | None = None) -> tuple[str, bool]:
    """Return (text, blocked). When blocked, text is a safe replacement."""
    conf = cfg or settings
    if not conf.output_moderation_enabled:
        return text, False
    if not text:
        return text, False
    for pattern in _OUTPUT_BLOCK_PATTERNS:
        if pattern.search(text):
            return _MODERATION_REPLACEMENT, True
    return text, False
