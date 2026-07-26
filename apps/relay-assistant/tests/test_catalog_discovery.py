from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import httpx
import yaml

from catalog_discovery.config import load_discovery_config
from catalog_discovery.github import (
    discover_entities_from_github,
    parse_catalog_documents,
    stamp_discovered_entity,
)
from catalog_discovery.sync import run_discovery, write_entities


def test_parse_catalog_documents_multi_doc():
    text = """
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: a
spec:
  type: service
---
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: b
spec:
  type: service
"""
    docs = parse_catalog_documents(text)
    assert len(docs) == 2
    assert docs[0]["metadata"]["name"] == "a"


def test_stamp_discovered_entity_adds_annotations():
    entity = {"apiVersion": "v1", "kind": "Component", "metadata": {"name": "x"}, "spec": {}}
    stamped = stamp_discovered_entity(
        entity, repo_full_name="opsdevcode/relay", path="catalog-info.yaml"
    )
    assert stamped["metadata"]["annotations"]["relay.dev/discovered-from"] == (
        "opsdevcode/relay@catalog-info.yaml"
    )
    assert stamped["metadata"]["annotations"]["github.com/project-slug"] == "opsdevcode/relay"


def test_discover_entities_from_github_mocked():
    cfg = load_discovery_config()
    assert cfg.github is not None
    gh = cfg.github
    gh = type(gh)(
        org=gh.org,
        repos=("opsdevcode/relay",),
        paths=gh.paths,
        api_url=gh.api_url,
        max_repos=5,
    )
    catalog_yaml = yaml.safe_dump(
        {
            "apiVersion": "backstage.io/v1alpha1",
            "kind": "Component",
            "metadata": {"name": "widget"},
            "spec": {"type": "service"},
        }
    )
    encoded = base64.b64encode(catalog_yaml.encode()).decode()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/contents/examples/services/demo-api/catalog-info.yaml"):
            return httpx.Response(
                200,
                json={"content": encoded, "encoding": "base64"},
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=client)
    ctx.__exit__ = MagicMock(return_value=False)
    with patch("catalog_discovery.github.httpx.Client", return_value=ctx):
        entities, logs = discover_entities_from_github(gh, token="test")
    assert len(entities) == 1
    assert entities[0]["metadata"]["name"] == "widget"
    assert any("ingested" in line for line in logs)


def test_run_discovery_writes_file(tmp_path):
    cfg_path = tmp_path / "discovery.yaml"
    cfg_path.write_text(
        """
github:
  org: opsdevcode
  repos: [relay]
  paths: [catalog-info.yaml]
output_path: catalog/entities/out.yaml
""".strip(),
        encoding="utf-8",
    )
    out = tmp_path / "catalog/entities/out.yaml"
    sample = [
        {
            "apiVersion": "backstage.io/v1alpha1",
            "kind": "Component",
            "metadata": {"name": "demo"},
            "spec": {"type": "service"},
        }
    ]

    with patch(
        "catalog_discovery.sync.discover_entities_from_github",
        return_value=(sample, ["ok"]),
    ):
        result = run_discovery(config_path=cfg_path, output_path=out, token="")
    assert result["entities_written"] == 1
    assert out.is_file()
    loaded = list(yaml.safe_load_all(out.read_text(encoding="utf-8")))
    assert loaded[0]["metadata"]["name"] == "demo"


def test_write_entities_empty_writes_comment(tmp_path):
    path = tmp_path / "discovered.yaml"
    write_entities(path, [])
    assert path.read_text(encoding="utf-8").startswith("#")
