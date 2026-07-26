from __future__ import annotations

from portal_assistant.user_context import UserContext, parse_user_context_from_headers


def test_parse_user_context_from_oauth2_proxy_headers():
    ctx = parse_user_context_from_headers(
        x_auth_request_user="alice",
        x_auth_request_email="alice@example.com",
        x_auth_request_groups="platform-team, developers",
    )
    assert ctx is not None
    assert ctx.subject == "alice"
    assert ctx.email == "alice@example.com"
    assert ctx.groups == ("platform-team", "developers")
    assert "platform-team" in ctx.retrieval_principals()


def test_parse_user_context_missing_subject():
    assert parse_user_context_from_headers() is None


def test_user_context_retrieval_principals_dedupe():
    ctx = UserContext(subject="alice@example.com", email="alice@example.com")
    assert ctx.retrieval_principals() == ["alice@example.com"]
