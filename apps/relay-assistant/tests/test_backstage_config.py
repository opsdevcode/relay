"""Assert Backstage app-config wires catalog/entities (Phase 1C.1)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
APP_CONFIG = REPO_ROOT / "apps" / "backstage" / "app-config.yaml"
CATALOG_REL = "../../../../catalog/entities/catalog.yaml"
TEMPLATE_REL = "../../../../templates/k8s-service/template.yaml"
TEMPLATE_PATH = REPO_ROOT / "templates" / "k8s-service" / "template.yaml"


def test_backstage_app_config_exists():
    assert APP_CONFIG.is_file(), f"missing Backstage config: {APP_CONFIG}"


def test_backstage_catalog_location_imports_repo_entities():
    data = yaml.safe_load(APP_CONFIG.read_text(encoding="utf-8"))
    locations = (data.get("catalog") or {}).get("locations") or []
    targets = [loc.get("target") for loc in locations if isinstance(loc, dict)]
    assert CATALOG_REL in targets, (
        f"expected catalog location {CATALOG_REL!r} in app-config locations={targets}"
    )


def test_backstage_catalog_registers_k8s_template():
    data = yaml.safe_load(APP_CONFIG.read_text(encoding="utf-8"))
    locations = (data.get("catalog") or {}).get("locations") or []
    targets = [loc.get("target") for loc in locations if isinstance(loc, dict)]
    assert TEMPLATE_REL in targets
    template_loc = next(loc for loc in locations if loc.get("target") == TEMPLATE_REL)
    allowed: set[str] = set()
    for rule in template_loc.get("rules") or []:
        allowed.update(rule.get("allow") or [])
    assert "Template" in allowed


def test_backstage_template_path_resolves_from_backend_cwd():
    backend_cwd = REPO_ROOT / "apps" / "backstage" / "packages" / "backend"
    resolved = (backend_cwd / TEMPLATE_REL).resolve()
    assert resolved == TEMPLATE_PATH.resolve()
    assert resolved.is_file()


def test_backstage_catalog_location_allows_component_user_group():
    data = yaml.safe_load(APP_CONFIG.read_text(encoding="utf-8"))
    locations = (data.get("catalog") or {}).get("locations") or []
    relay_loc = next(loc for loc in locations if loc.get("target") == CATALOG_REL)
    allowed: set[str] = set()
    for rule in relay_loc.get("rules") or []:
        allowed.update(rule.get("allow") or [])
    for kind in ("Component", "User", "Group"):
        assert kind in allowed, f"{kind} must be allowed for seed catalog import"


def test_backstage_frontend_port_avoids_relay_web():
    data = yaml.safe_load(APP_CONFIG.read_text(encoding="utf-8"))
    base_url = (data.get("app") or {}).get("baseUrl", "")
    assert ":3001" in base_url, f"expected frontend on :3001, got {base_url}"
    cors_origin = ((data.get("backend") or {}).get("cors") or {}).get("origin", "")
    assert cors_origin == "http://localhost:3001"


def test_backstage_embeds_relay_chat_url():
    data = yaml.safe_load(APP_CONFIG.read_text(encoding="utf-8"))
    embed_url = (data.get("relay") or {}).get("chatEmbedUrl", "")
    assert embed_url == "http://localhost:3000", (
        f"expected relay.chatEmbedUrl for local web UI, got {embed_url!r}"
    )


def test_backstage_csp_allows_chat_embed_frame():
    data = yaml.safe_load(APP_CONFIG.read_text(encoding="utf-8"))
    frame_src = ((data.get("backend") or {}).get("csp") or {}).get("frame-src") or []
    assert "http://localhost:3000" in frame_src


def test_seed_catalog_path_resolves_from_backend_cwd():
    """Mirrors Backstage file location resolution from packages/backend."""
    backend_cwd = REPO_ROOT / "apps" / "backstage" / "packages" / "backend"
    resolved = (backend_cwd / CATALOG_REL).resolve()
    assert resolved == (REPO_ROOT / "catalog" / "entities" / "catalog.yaml").resolve()
    assert resolved.is_file()
