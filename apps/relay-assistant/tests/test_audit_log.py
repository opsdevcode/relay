"""Audit log persistence (Phase 2A.4)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from portal_assistant import audit_log as audit_mod
from portal_assistant.audit_log import (
    EVENT_CHAT_PROMPT,
    EVENT_CONFIRM,
    AuditActor,
    AuditLogStore,
)
from portal_assistant.config import settings
from portal_assistant.user_context import UserContext


def test_audit_actor_from_user():
    actor = AuditActor.from_user(UserContext(subject="alice", email="a@example.com"))
    assert actor.subject == "alice"
    assert actor.email == "a@example.com"


def test_record_noop_when_disabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "audit_log_enabled", False)
    store = AuditLogStore("postgresql://invalid")
    store.connect = MagicMock()  # type: ignore[method-assign]
    store.record(EVENT_CHAT_PROMPT, payload={"prompt": "hi"})
    store.connect.assert_not_called()


def test_query_limit_clamped(monkeypatch: pytest.MonkeyPatch):
    captured: list = []

    def fake_execute(sql, params):
        captured.append(params)
        result = MagicMock()
        result.fetchall.return_value = []
        return result

    conn = MagicMock()
    conn.execute = fake_execute
    conn.__enter__ = lambda self: conn
    conn.__exit__ = lambda *args: None

    store = AuditLogStore("postgresql://x")
    store.connect = MagicMock(return_value=conn)  # type: ignore[method-assign]
    store.query(limit=999)
    assert captured[0][0] == 200


def test_event_type_constants():
    assert EVENT_CHAT_PROMPT == "chat_prompt"
    assert EVENT_CONFIRM == "confirm_action"
    assert audit_mod.EVENT_RETRIEVAL == "retrieval"
    assert audit_mod.EVENT_TOOL_INVOKE == "tool_invoke"
