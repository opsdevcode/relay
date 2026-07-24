import pytest

from portal_assistant.sessions import (
    SessionStore,
    apply_follow_up_refinement,
)


def test_apply_follow_up_after_scaffold_draft():
    turns = [
        {"role": "user", "content": "scaffold a service"},
        {
            "role": "assistant",
            "content": "draft",
            "meta": {
                "tool": "scaffold_service",
                "draft": {"action": "scaffold_service", "inputs": {"service_name": "demo-service"}},
            },
        },
    ]
    assert apply_follow_up_refinement("call it payments-api", turns) == (
        "Create a new service called payments-api"
    )


def test_apply_follow_up_ignored_without_scaffold_context():
    turns = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi", "meta": {"tool": "docs_search"}},
    ]
    assert apply_follow_up_refinement("call it payments-api", turns) == "call it payments-api"


def test_session_store_trims_history():
    store = SessionStore.in_memory(max_turns=2)
    tid = store.ensure_thread_id(None)
    for i in range(3):
        store.append_exchange(
            tid,
            user_message=f"u{i}",
            assistant_message=f"a{i}",
            meta={"tool": "docs_search"},
        )
    turns = store.get_turns(tid)
    assert len(turns) == 4
    assert turns[0]["content"] == "u1"


@pytest.mark.asyncio
async def test_handle_message_follow_up_scaffold_name():
    from portal_assistant.agent import handle_message
    from portal_assistant.sessions import SessionStore

    store = SessionStore.in_memory()
    tid = "test-thread"

    class FakeStore:
        def search(self, _query: str) -> list:
            return []

    fake = FakeStore()  # type: ignore[assignment]

    await handle_message(
        "Create a new service called demo-service",
        fake,  # type: ignore[arg-type]
        session_store=store,
        thread_id=tid,
    )
    result = await handle_message(
        "call it payments-api",
        fake,  # type: ignore[arg-type]
        session_store=store,
        thread_id=tid,
    )
    assert result["draft"] is not None
    assert result["draft"]["inputs"]["service_name"] == "payments-api"
