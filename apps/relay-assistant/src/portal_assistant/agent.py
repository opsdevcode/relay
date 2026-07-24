from __future__ import annotations

from portal_assistant.graph import run_chat_graph
from portal_assistant.sessions import SessionStore
from portal_assistant.store import DocumentStore


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
    result, trace = await run_chat_graph(
        message,
        store,
        prior_turns=prior_turns,
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
