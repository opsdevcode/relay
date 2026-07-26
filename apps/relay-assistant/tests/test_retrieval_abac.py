from portal_assistant.retrieval_abac import abac_should_filter, access_where_clause
from portal_assistant.user_context import UserContext


class _Cfg:
    retrieval_abac_enabled = False


class _CfgStrict:
    retrieval_abac_enabled = True


def test_abac_skipped_without_user_or_flag():
    assert abac_should_filter(None, _Cfg()) is False
    sql, params = access_where_clause(None, cfg=_Cfg())
    assert sql == ""
    assert params == []


def test_abac_strict_public_only_without_user():
    sql, params = access_where_clause(None, cfg=_CfgStrict())
    assert "visibility = 'public'" in sql
    assert params == []


def test_abac_authenticated_sees_internal():
    user = UserContext(subject="alice", email="alice@example.com")
    sql, _params = access_where_clause(user, cfg=_Cfg())
    assert "visibility = 'internal'" in sql
    assert "visibility = 'public'" in sql


def test_abac_restricted_by_owner_and_groups():
    user = UserContext(subject="alice", groups=("platform-team",))
    sql, params = access_where_clause(user, cfg=_CfgStrict())
    assert "doc_owner = ANY" in sql
    assert "allowed_groups &&" in sql
    assert params == [["alice", "platform-team"], ["alice", "platform-team"]]


def test_abac_no_principals_public_only_when_headers_user_empty():
    user = UserContext(subject="", email="")
    sql, params = access_where_clause(user, cfg=_Cfg())
    assert "visibility = 'public'" in sql
    assert "restricted" not in sql
    assert params == []
