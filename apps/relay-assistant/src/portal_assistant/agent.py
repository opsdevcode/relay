from __future__ import annotations

from portal_assistant.registry import resolve_tool
from portal_assistant.sessions import SessionStore, apply_follow_up_refinement
from portal_assistant.store import DocumentStore
from portal_assistant.tools import dispatch_tool


async def handle_message(
    message: str,
    store: DocumentStore,
    *,
    session_store: SessionStore | None = None,
    thread_id: str | None = None,
) -> dict:
    sessions = session_store
    tid = sessions.ensure_thread_id(thread_id) if sessions else (thread_id or "")

    prior_turns = sessions.get_turns(tid) if sessions else []
    effective_message = apply_follow_up_refinement(message, prior_turns)

    tool_id = resolve_tool(effective_message)
    result = await dispatch_tool(tool_id, effective_message, store)

    if sessions and tid:
        sessions.append_exchange(
            tid,
            user_message=message,
            assistant_message=result.get("answer", ""),
            meta={
                "tool": tool_id,
                "draft": result.get("draft"),
                "effective_message": effective_message
                if effective_message != message
                else None,
            },
        )
        result["thread_id"] = tid

    return result
