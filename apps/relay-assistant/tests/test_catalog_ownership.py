from __future__ import annotations

from pathlib import Path

import pytest

from portal_assistant.catalog_ownership import (
    catalog_entity_paths,
    extract_ownership_target,
    format_ownership_answer,
    load_catalog_entities,
    resolve_ownership,
)
from portal_assistant.tools import dispatch_tool


class _NoOpStore:
    pass


def test_catalog_entity_paths_includes_seed_and_demo_api():
    paths = catalog_entity_paths()
    rel = {p.name for p in paths}
    assert "catalog.yaml" in rel
    assert any(p.name == "catalog-info.yaml" for p in paths)


def test_resolve_ownership_demo_api():
    match = resolve_ownership("demo-api")
    assert match is not None
    assert match.entity["metadata"]["name"] == "demo-api"
    assert match.owner_ref == "platform-team"
    assert match.owner_entity is not None
    assert match.owner_entity["kind"] == "Group"


def test_resolve_ownership_relay():
    match = resolve_ownership("relay")
    assert match is not None
    assert match.entity["metadata"]["name"] == "relay"


def test_extract_ownership_target_parses_who_owns():
    assert extract_ownership_target("Who owns demo-api?") == "demo-api"
    assert extract_ownership_target("ownership of cloudopt") == "cloudopt"


def test_format_ownership_answer_includes_source():
    match = resolve_ownership("demo-api")
    text = format_ownership_answer(match, query="demo-api")
    assert "platform-team" in text
    assert "catalog" in text.lower()
    assert "not document search" in text.lower()


def test_format_ownership_answer_unknown_lists_known():
    text = format_ownership_answer(None, query="missing-widget")
    assert "missing-widget" in text
    assert "demo-api" in text or "relay" in text


@pytest.mark.asyncio
async def test_dispatch_catalog_ownership_tool():
    result = await dispatch_tool(
        "catalog_ownership",
        "Who owns demo-api?",
        _NoOpStore(),  # type: ignore[arg-type]
    )
    assert "platform-team" in result["answer"]
    assert result["citations"] == []


def test_load_catalog_entities_with_custom_root(tmp_path: Path):
    catalog = tmp_path / "catalog" / "entities" / "catalog.yaml"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        """
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: widget
spec:
  type: service
  owner: team-a
---
apiVersion: backstage.io/v1alpha1
kind: Group
metadata:
  name: team-a
spec:
  type: team
""".strip(),
        encoding="utf-8",
    )
    entities = load_catalog_entities(tmp_path)
    match = resolve_ownership("widget", root=tmp_path, entities=entities)
    assert match is not None
    assert match.owner_entity is not None
    assert match.owner_entity["metadata"]["name"] == "team-a"
