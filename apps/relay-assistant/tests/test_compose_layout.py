"""Root compose.yaml includes deploy stack (local-compose Tier 1)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_ROOT = REPO_ROOT / "compose.yaml"
COMPOSE_DEPLOY = REPO_ROOT / "deploy" / "docker-compose.yml"


def test_root_compose_file_includes_deploy_stack():
    assert COMPOSE_ROOT.is_file()
    data = yaml.safe_load(COMPOSE_ROOT.read_text(encoding="utf-8"))
    includes = data.get("include") or []
    assert includes, "compose.yaml should include deploy/docker-compose.yml"
    paths = []
    for item in includes:
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict):
            paths.append(item.get("path", ""))
    assert any("deploy/docker-compose.yml" in p for p in paths)


def test_deploy_compose_defines_backstage_profile():
    data = yaml.safe_load(COMPOSE_DEPLOY.read_text(encoding="utf-8"))
    backstage = (data.get("services") or {}).get("backstage") or {}
    assert backstage.get("profiles") == ["backstage"]
