"""Validate repo-root Backstage seed catalog (Phase 1C.1)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = REPO_ROOT / "catalog" / "entities" / "catalog.yaml"


def _load_entities(path: Path) -> list[dict]:
    docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    return [d for d in docs if isinstance(d, dict)]


def test_catalog_entities_file_exists():
    assert CATALOG_PATH.is_file(), f"missing seed catalog: {CATALOG_PATH}"


def test_catalog_entities_required_kinds_and_names():
    entities = _load_entities(CATALOG_PATH)
    by_kind: dict[str, set[str]] = {}
    for ent in entities:
        kind = ent.get("kind")
        name = (ent.get("metadata") or {}).get("name")
        assert kind, f"entity missing kind: {ent}"
        assert name, f"entity missing metadata.name: {ent}"
        assert ent.get("apiVersion", "").startswith("backstage.io/")
        by_kind.setdefault(kind, set()).add(name)

    assert "relay" in by_kind.get("Component", set())
    assert "cloudopt" in by_kind.get("Component", set())
    assert "platform-team" in by_kind.get("Group", set())
    assert "guest" in by_kind.get("User", set())


def test_catalog_component_owners_resolve_to_group():
    entities = _load_entities(CATALOG_PATH)
    groups = {(e.get("metadata") or {}).get("name") for e in entities if e.get("kind") == "Group"}
    components = [e for e in entities if e.get("kind") == "Component"]
    assert components
    for component in components:
        owner = (component.get("spec") or {}).get("owner")
        assert owner, f"{component['metadata']['name']} missing spec.owner"
        assert owner in groups, (
            f"owner {owner!r} for {component['metadata']['name']} "
            f"not found in Groups {sorted(groups)}"
        )


def test_catalog_guest_user_member_of_platform_team():
    entities = _load_entities(CATALOG_PATH)
    guest = next(
        e
        for e in entities
        if e.get("kind") == "User" and (e.get("metadata") or {}).get("name") == "guest"
    )
    member_of = (guest.get("spec") or {}).get("memberOf") or []
    assert "platform-team" in member_of
