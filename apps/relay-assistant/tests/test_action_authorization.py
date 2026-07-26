import pytest
from fastapi import HTTPException

from portal_assistant import action_authorization as auth
from portal_assistant.registry import RegistryConfig, ToolDefinition
from portal_assistant.user_context import UserContext


def test_user_may_confirm_when_disabled():
    user = UserContext(subject="bob", groups=("other",))
    assert auth.user_may_confirm(user, "scaffold_service") is True


def test_user_may_confirm_requires_group(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(auth.settings, "confirm_action_authorization_enabled", True)
    entitled = UserContext(subject="alice", groups=("relay-platform-admins",))
    denied = UserContext(subject="bob", groups=("other",))
    assert auth.user_may_confirm(entitled, "scaffold_service") is True
    assert auth.user_may_confirm(denied, "scaffold_service") is False
    assert auth.user_may_confirm(None, "scaffold_service") is False


def test_sandbox_allows_sandbox_users(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(auth.settings, "confirm_action_authorization_enabled", True)
    user = UserContext(subject="dev", groups=("relay-sandbox-users",))
    assert auth.user_may_confirm(user, "request_sandbox") is True


def test_require_confirm_raises_403(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(auth.settings, "confirm_action_authorization_enabled", True)
    user = UserContext(subject="bob", groups=("other",))
    with pytest.raises(HTTPException) as exc:
        auth.require_confirm_authorization(user, "scaffold_service")
    assert exc.value.status_code == 403


def test_require_confirm_raises_401_without_user(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(auth.settings, "confirm_action_authorization_enabled", True)
    with pytest.raises(HTTPException) as exc:
        auth.require_confirm_authorization(None, "scaffold_service")
    assert exc.value.status_code == 401


def test_env_fallback_groups(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(auth.settings, "confirm_action_authorization_enabled", True)
    monkeypatch.setattr(auth.settings, "confirm_allowed_groups", "custom-admins")
    config = RegistryConfig(
        services=[],
        routing=[],
        tools={
            "scaffold_service": ToolDefinition(
                kind="write",
                requires_confirmation=True,
                confirm_allowed_groups=(),
            ),
        },
    )
    user = UserContext(subject="u", groups=("custom-admins",))
    assert auth.user_may_confirm(user, "scaffold_service", config=config) is True
