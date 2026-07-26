from __future__ import annotations

from portal_assistant.audit_log import (
    EVENT_CHAT_PROMPT,
    EVENT_TOOL_INVOKE,
    AuditActor,
    AuditLogStore,
)
from portal_assistant.graph import run_chat_graph
from portal_assistant.sessions import SessionStore
from portal_assistant.store import DocumentStore
from portal_assistant.user_context import UserContext


async def handle_message(
    message: str,
    store: DocumentStore,
    *,
    session_store: SessionStore | None = None,
    thread_id: str | None = None,
    user: UserContext | None = None,
    audit: AuditLogStore | None = None,
) -> dict:
    sessions = session_store
    tid = sessions.ensure_thread_id(thread_id) if sessions else (thread_id or "")

    prior_turns = sessions.get_turns(tid) if sessions else []
    result, trace = await run_chat_graph(
        message,
        store,
        prior_turns=prior_turns,
        user=user,
        audit=audit,
        thread_id=tid or None,
    )

    if audit:
        actor = AuditActor.from_user(user)
        audit.record(
            EVENT_TOOL_INVOKE,
            payload={"graph_path": trace.path, "message_preview": message[:500]},
            thread_id=tid or None,
            actor=actor,
            tool_id=trace.tool_id,
        )
        audit.record(
            EVENT_CHAT_PROMPT,
            payload={
                "prompt": message[:2000],
                "citation_count": len(result.get("citations") or []),
                "has_draft": bool(result.get("draft")),
            },
            thread_id=tid or None,
            actor=actor,
            tool_id=trace.tool_id,
        )

    if sessions and tid:
        sessions.append_exchange(
            tid,
            user_message=message,
            assistant_message=result.get("answer", ""),
            meta={
                "tool": trace.tool_id,
                "graph_path": trace.path,
                "draft": result.get("draft"),
            },
        )
        result["thread_id"] = tid

    return result
