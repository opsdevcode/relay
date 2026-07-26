from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from portal_assistant.on_call import (
    build_schedule_deeplink,
    extract_on_call_target,
    fetch_on_call,
    format_on_call_answer,
    on_call_live_configured,
    resolve_on_call_provider,
)
from portal_assistant.registry import OnCallRegistry, OnCallTeamEntry


def test_resolve_on_call_provider_defaults():
    assert resolve_on_call_provider() == "deeplink"


def test_extract_on_call_target():
    assert extract_on_call_target("Who is on call for demo-api?") == "demo-api"
    assert extract_on_call_target("demo-api on-call") == "demo-api"


def test_build_schedule_deeplink_from_registry():
    entity = {"metadata": {"name": "demo-api"}, "spec": {"owner": "platform-team"}}
    on_call = OnCallRegistry(
        url_template="https://pd.example/schedules/{schedule_id}",
        teams={
            "platform-team": OnCallTeamEntry(
                schedule_id="ABC123",
                pagerduty_escalation_policy_id="POL1",
            )
        },
    )
    url = build_schedule_deeplink(owner_ref="platform-team", entity=entity, on_call=on_call)
    assert url == "https://pd.example/schedules/ABC123"


@pytest.mark.asyncio
async def test_fetch_on_call_deeplink():
    result = await fetch_on_call("demo-api")
    assert result.entity_name == "demo-api"
    assert result.owner_team == "platform-team"
    assert "example.pagerduty.com" in result.schedule_url or result.schedule_url


@pytest.mark.asyncio
async def test_fetch_on_call_pagerduty_live():
    payload = {
        "oncalls": [
            {
                "user": {"summary": "Alex Engineer", "email": "alex@example.com"},
            }
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert "oncalls" in request.url.path
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)

    with patch("portal_assistant.on_call.settings") as mock_settings:
        mock_settings.on_call_provider = "pagerduty"
        mock_settings.pagerduty_api_token = "secret"
        mock_settings.pagerduty_api_url = "https://api.pagerduty.com"
        mock_settings.on_call_url_template = ""
        mock_settings.pagerduty_base_url = ""

        with patch("portal_assistant.on_call.httpx.AsyncClient", return_value=client):
            result = await fetch_on_call("demo-api", cfg=mock_settings)

    assert result.status == "live"
    assert "Alex Engineer" in result.on_call_users[0]


def test_on_call_live_configured():
    class Cfg:
        on_call_provider = "pagerduty"
        pagerduty_api_token = "x"
        opsgenie_api_token = ""

    assert on_call_live_configured(Cfg()) is True


def test_format_on_call_answer():
    from portal_assistant.on_call import OnCallResult

    text = format_on_call_answer(
        OnCallResult(
            provider="deeplink",
            entity_name="demo-api",
            owner_team="platform-team",
            status="deeplink",
            on_call_users=(),
            schedule_url="https://pd.example/s/1",
            note="test note",
        )
    )
    assert "demo-api" in text
    assert "https://pd.example/s/1" in text
