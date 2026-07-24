from __future__ import annotations

from portal_assistant.registry import resolve_tool
from portal_assistant.store import DocumentStore
from portal_assistant.tools import dispatch_tool


async def handle_message(message: str, store: DocumentStore) -> dict:
    tool_id = resolve_tool(message)
    return await dispatch_tool(tool_id, message, store)
