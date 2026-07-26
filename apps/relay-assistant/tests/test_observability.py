from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from portal_assistant.config import Settings
from portal_assistant.observability import (
    build_grafana_url,
    fetch_service_health,
    format_service_health_answer,
    resolve_observability_provider,
)
from portal_assistant.registry import ObservabilityRegistry, ObservabilityServiceEntry


def test_resolve_observability_provider_mock():
    assert resolve_observability_provider(Settings(observability_provider="mock")) == "mock"


def test_resolve_observability_provider_auto_grafana():
    cfg = Settings(grafana_base_url="https://grafana.example.com")
    assert resolve_observability_provider(cfg) == "grafana_deeplink"


def test_build_grafana_url_from_catalog():
    obs = ObservabilityRegistry(
        catalog={
            "demo-api": ObservabilityServiceEntry(
                dashboard_uid="relay-demo",
                slo_target="99.9%",
            )
        }
    )
    url = build_grafana_url(
        service_slug="demo-api",
        dashboard_uid="relay-demo",
        cfg=Settings(grafana_base_url="https://grafana.example.com"),
        obs=obs,
    )
    assert url == "https://grafana.example.com/d/relay-demo?var-service=demo-api"


@pytest.mark.asyncio
async def test_fetch_service_health_mock():
    result = await fetch_service_health(
        "demo-api",
        cfg=Settings(observability_provider="mock"),
    )
    assert result.mode == "mock"
    assert result.service == "demo-api"
    assert "GRAFANA_BASE_URL" in (result.note or "")


@pytest.mark.asyncio
async def test_fetch_service_health_grafana_catalog():
    obs = ObservabilityRegistry(
        catalog={
            "payments-api": ObservabilityServiceEntry(
                dashboard_uid="pay-dash",
                slo_target="99.95%",
            )
        }
    )
    result = await fetch_service_health(
        "payments-api",
        cfg=Settings(
            observability_provider="grafana_deeplink",
            grafana_base_url="https://grafana.example.com",
        ),
        obs_registry=obs,
    )
    assert result.catalog_match is True
    assert result.grafana_url is not None
    assert "pay-dash" in result.grafana_url
    assert result.slo["target"] == "99.95%"


@pytest.mark.asyncio
async def test_fetch_service_health_prometheus_alerts():
    obs = ObservabilityRegistry(catalog={})

    async def fake_scalar(**kwargs):
        return 2.0

    with patch(
        "portal_assistant.observability._prometheus_scalar",
        new=AsyncMock(side_effect=fake_scalar),
    ):
        result = await fetch_service_health(
            "demo-api",
            cfg=Settings(
                observability_provider="prometheus",
                prometheus_base_url="https://prom.example.com",
            ),
            obs_registry=obs,
        )
    assert result.mode == "prometheus"
    assert result.status == "degraded"
    assert result.alerts[0]["count"] == 2


@pytest.mark.asyncio
async def test_fetch_service_health_prometheus_http_error():
    obs = ObservabilityRegistry(catalog={})

    async def fail(**kwargs):
        raise httpx.ConnectError("down")

    with patch(
        "portal_assistant.observability._prometheus_scalar",
        new=AsyncMock(side_effect=fail),
    ):
        result = await fetch_service_health(
            "demo-api",
            cfg=Settings(
                observability_provider="prometheus",
                prometheus_base_url="https://prom.example.com",
            ),
            obs_registry=obs,
        )
    assert result.note is not None
    assert "Prometheus" in result.note


def test_format_service_health_answer_includes_grafana():
    text = format_service_health_answer(
        {
            "service": "demo-api",
            "mode": "grafana_deeplink",
            "slo": {"target": "99.9%", "burn_rate": None},
            "alerts": [],
            "grafana_url": "https://grafana.example.com/d/x",
            "note": None,
        }
    )
    assert "Grafana:" in text
    assert "demo-api" in text
