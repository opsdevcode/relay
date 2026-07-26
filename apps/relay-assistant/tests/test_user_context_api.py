import pytest

from portal_assistant import main as main_mod
from portal_assistant.main import _resolve_user_context


def test_resolve_user_context_disabled_by_default():
    assert _resolve_user_context("alice", "alice@example.com", "team-a") is None


def test_resolve_user_context_when_enabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main_mod.settings, "user_context_headers_enabled", True)
    ctx = _resolve_user_context(
        "alice",
        "alice@example.com",
        "team-a, team-b",
    )
    assert ctx is not None
    assert ctx.subject == "alice"
    assert ctx.groups == ("team-a", "team-b")


@pytest.mark.asyncio
async def test_dispatch_tool_passes_user_to_search():
    from portal_assistant.tools import dispatch_tool
    from portal_assistant.user_context import UserContext

    class SpyStore:
        def __init__(self) -> None:
            self.last_user = "unset"

        def search(self, _query: str, user=None) -> list:
            self.last_user = user
            return []

    store = SpyStore()
    user = UserContext(subject="alice", groups=("team-a",))
    await dispatch_tool("docs_search", "What is golden path?", store, user=user)  # type: ignore[arg-type]
    assert store.last_user == user
