"""Pluggable sandbox ticket handoff (Phase 2A.2)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from portal_assistant import ticket_intake as ti
from portal_assistant.config import Settings
from portal_assistant.user_context import UserContext


def test_resolve_ticket_provider_defaults_github():
    assert ti.resolve_ticket_intake_provider(Settings()) == "github_issue"


def test_github_issue_handoff_includes_template():
    cfg = Settings(github_repo="opsdevcode/relay")
    result = ti.github_issue_handoff({"purpose": "POC widgets"}, cfg=cfg)
    body = result.as_response()
    assert body["provider"] == "github_issue"
    assert "sandbox-request.md" in body["intake_url"]
    assert body["issue_url"] == body["intake_url"]


def test_url_template_substitutes_draft_fields():
    cfg = Settings(
        ticket_intake_provider="url_template",
        ticket_intake_url_template=(
            "https://portal.example/sp?id=item&desc={purpose_raw}&budget={budget_raw}"
        ),
    )
    user = UserContext(subject="alice", email="alice@example.com")
    result = ti.url_template_handoff(
        {"purpose": "Load test", "budget_usd_monthly": "750"},
        user=user,
        cfg=cfg,
    )
    assert "Load%20test" in result.intake_url or "Load test" in result.intake_url
    assert "750" in result.intake_url


@pytest.mark.asyncio
async def test_jira_api_create_returns_ticket_link():
    cfg = Settings(
        ticket_intake_provider="jira",
        ticket_intake_base_url="https://jira.example.com",
        ticket_intake_username="bot@example.com",
        ticket_intake_api_token="secret",
        ticket_intake_project="SANDBOX",
    )
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"key": "SAN-42"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("portal_assistant.ticket_intake.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value = mock_client
        result = await ti.jira_handoff({"purpose": "Edge POC"}, cfg=cfg)

    assert result.ticket_id == "SAN-42"
    assert "SAN-42" in result.intake_url
    assert result.status == "ticket_created"


@pytest.mark.asyncio
async def test_jira_without_credentials_returns_deeplink():
    cfg = Settings(
        ticket_intake_provider="jira",
        ticket_intake_base_url="https://jira.example.com",
        ticket_intake_project="SANDBOX",
    )
    result = await ti.jira_handoff({"purpose": "POC"}, cfg=cfg)
    assert result.status == "ticket_link"
    assert result.intake_url.startswith("https://jira.example.com/")


@pytest.mark.asyncio
async def test_servicenow_api_create():
    cfg = Settings(
        ticket_intake_provider="servicenow",
        ticket_intake_base_url="https://snow.example.com",
        ticket_intake_username="relay.bot",
        ticket_intake_api_token="secret",
        ticket_intake_project="incident",
    )
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"result": {"number": "INC001", "sys_id": "abc"}}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("portal_assistant.ticket_intake.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value = mock_client
        result = await ti.servicenow_handoff({"purpose": "Lab"}, cfg=cfg)

    assert result.ticket_id == "INC001"
    assert result.provider == "servicenow"
