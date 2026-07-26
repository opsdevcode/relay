from portal_assistant.store import _access_filter_clause
from portal_assistant.user_context import UserContext


def test_access_filter_skipped_without_user():
    sql, params = _access_filter_clause(None)
    assert sql == ""
    assert params == []


def test_access_filter_public_only_when_no_principals():
    user = UserContext(subject="", email="")
    sql, params = _access_filter_clause(user)
    assert "visibility = 'public'" in sql
    assert params == []


def test_access_filter_includes_principals():
    user = UserContext(subject="alice", email="alice@example.com", groups=("platform",))
    sql, params = _access_filter_clause(user)
    assert "doc_owner = ANY" in sql
    assert params == [["alice", "alice@example.com", "platform"]]
