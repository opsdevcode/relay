from __future__ import annotations

from fastapi.testclient import TestClient

from portal_assistant.config import Settings
from portal_assistant.main import app
from portal_assistant.views import load_platform_services, resolve_grafana_embed_view


def test_platform_services_includes_grafana_embed_view():
    client = TestClient(app)
    response = client.get("/platform-services")
    assert response.status_code == 200
    services = response.json()
    obs = next(s for s in services if s.get("id") == "observability-insight")
    assert "grafana-embed" in obs.get("views", [])
    embed = obs.get("view_urls", {}).get("grafana_embed")
    assert embed is not None
    assert embed["service"] == "demo-api"
    assert embed["configured"] is False
    assert "GRAFANA_BASE_URL" in embed.get("hint", "")


def test_resolve_grafana_embed_url_when_grafana_configured():
    cfg = Settings(grafana_base_url="https://grafana.example.com")
    embed = resolve_grafana_embed_view(cfg=cfg, service_slug="demo-api")
    assert embed["configured"] is True
    assert embed["url"].startswith("https://grafana.example.com/d/relay-demo")
    assert "kiosk" in embed["url"]
    assert embed["catalog_match"] is True


def test_grafana_embed_endpoint_resolves_service():
    client = TestClient(app)
    response = client.get(
        "/platform-services/observability-insight/grafana-embed",
        params={"service": "payments-api"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "payments-api"
    assert data["dashboard_uid"] == "payments-overview"


def test_grafana_embed_endpoint_unknown_service():
    client = TestClient(app)
    response = client.get("/platform-services/knowledge-standards/grafana-embed")
    assert response.status_code == 404


def test_load_platform_services_attaches_view_urls():
    services = load_platform_services(cfg=Settings())
    obs = next(s for s in services if s.get("id") == "observability-insight")
    assert "view_urls" in obs
    assert "grafana_embed" in obs["view_urls"]
    assert "catalog_services" in obs["view_urls"]["grafana_embed"]
