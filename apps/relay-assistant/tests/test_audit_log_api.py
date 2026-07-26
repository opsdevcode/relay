from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from portal_assistant import main as main_mod


def test_audit_events_requires_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main_mod.settings, "audit_query_secret", "")
    app = FastAPI()
    app.get("/internal/audit-events")(main_mod.list_audit_events)
    with TestClient(app) as client:
        resp = client.get("/internal/audit-events")
    assert resp.status_code == 503


def test_audit_events_returns_rows(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main_mod.settings, "audit_query_secret", "test-secret")

    def fake_query(**kwargs: object) -> list[dict]:
        return [{"id": 1, "event_type": "chat_prompt", "payload": {}}]

    monkeypatch.setattr(main_mod.audit_store, "query", fake_query)
    app = FastAPI()
    app.get("/internal/audit-events")(main_mod.list_audit_events)
    with TestClient(app) as client:
        resp = client.get("/internal/audit-events", headers={"X-Audit-Secret": "test-secret"})
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
