from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

OWNERSHIP_KINDS = frozenset({"Component", "System", "API", "Resource"})


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _is_placeholder_catalog(path: Path) -> bool:
    text = path.read_text(encoding="utf-8").strip()
    return not text or text.startswith("#")


def _load_documents(path: Path) -> list[dict[str, Any]]:
    if not path.is_file() or _is_placeholder_catalog(path):
        return []
    docs: list[dict[str, Any]] = []
    for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")):
        if isinstance(doc, dict) and doc.get("kind"):
            docs.append(doc)
    return docs


def _expand_location_file(location_path: Path) -> list[Path]:
    targets: list[Path] = []
    for doc in _load_documents(location_path):
        if doc.get("kind") != "Location":
            continue
        spec = doc.get("spec") or {}
        for raw_target in spec.get("targets") or []:
            target = str(raw_target).strip()
            if not target:
                continue
            targets.append((location_path.parent / target).resolve())
    return targets


def catalog_entity_paths(root: Path | None = None) -> list[Path]:
    base = root or repo_root()
    paths: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen or not resolved.is_file():
            return
        seen.add(resolved)
        paths.append(resolved)

    add(base / "catalog" / "entities" / "catalog.yaml")
    for location in (
        base / "catalog" / "entities" / "scaffolded-services.yaml",
        base / "catalog" / "entities" / "discovered-github-location.yaml",
    ):
        if location.is_file():
            for target in _expand_location_file(location):
                add(target)
    discovered = base / "catalog" / "entities" / "discovered-github.yaml"
    add(discovered)
    return paths


def load_catalog_entities(root: Path | None = None) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    for path in catalog_entity_paths(root):
        for doc in _load_documents(path):
            kind = str(doc.get("kind") or "")
            if kind in OWNERSHIP_KINDS or kind in {"Group", "User"}:
                rel = path.relative_to(root or repo_root())
                entities.append({**doc, "_relay_source": str(rel)})
    return entities


def _normalize_owner_ref(owner: str) -> str:
    ref = owner.strip()
    if ":" in ref:
        ref = ref.rsplit("/", 1)[-1]
    return ref.lower()


def _entity_name(entity: dict[str, Any]) -> str:
    return str((entity.get("metadata") or {}).get("name") or "").strip()


def _entity_title(entity: dict[str, Any]) -> str:
    return str((entity.get("metadata") or {}).get("title") or "").strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")


def extract_ownership_target(message: str) -> str:
    patterns = [
        (
            r"(?i)\b(?:who owns|ownership of|owner of|which team owns|team for)\s+"
            r"['\"]?([a-z0-9][a-z0-9_-]*)"
        ),
        r"(?i)\b([a-z0-9][a-z0-9_-]*)\s+ownership\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return _slug(match.group(1))
    skip = {
        "who",
        "owns",
        "ownership",
        "team",
        "which",
        "does",
        "the",
        "for",
        "what",
        "is",
        "are",
        "service",
        "component",
    }
    tokens = re.findall(r"\b[a-z][a-z0-9-]{2,}\b", message.lower())
    for token in reversed(tokens):
        if token not in skip:
            return str(token)
    return "demo-api"


@dataclass(frozen=True)
class OwnershipMatch:
    entity: dict[str, Any]
    owner_ref: str
    owner_entity: dict[str, Any] | None
    source: str

    def to_dict(self) -> dict[str, Any]:
        meta = self.entity.get("metadata") or {}
        spec = self.entity.get("spec") or {}
        owner_meta = (self.owner_entity or {}).get("metadata") or {}
        return {
            "kind": self.entity.get("kind"),
            "name": meta.get("name"),
            "title": meta.get("title"),
            "owner": self.owner_ref,
            "owner_kind": self.owner_entity.get("kind") if self.owner_entity else None,
            "owner_name": owner_meta.get("name"),
            "lifecycle": spec.get("lifecycle"),
            "type": spec.get("type"),
            "source": self.source,
            "annotations": meta.get("annotations") or {},
        }


def resolve_ownership(
    query: str,
    *,
    root: Path | None = None,
    entities: list[dict[str, Any]] | None = None,
) -> OwnershipMatch | None:
    needle = _slug(query)
    if not needle:
        return None
    catalog = entities if entities is not None else load_catalog_entities(root)
    catalog_entities = [e for e in catalog if e.get("kind") in OWNERSHIP_KINDS]
    groups = {_entity_name(e).lower(): e for e in catalog if e.get("kind") == "Group"}
    users = {_entity_name(e).lower(): e for e in catalog if e.get("kind") == "User"}

    def score(entity: dict[str, Any]) -> int:
        name = _entity_name(entity).lower()
        title = _slug(_entity_title(entity))
        if name == needle:
            return 100
        if name.replace("_", "-") == needle.replace("_", "-"):
            return 95
        if title and title == needle:
            return 90
        if needle in name or name in needle:
            return 70
        return 0

    scored = ((score(e), e) for e in catalog_entities)
    ranked = sorted(scored, key=lambda pair: pair[0], reverse=True)
    if not ranked or ranked[0][0] == 0:
        return None
    entity = ranked[0][1]
    owner_raw = str((entity.get("spec") or {}).get("owner") or "").strip()
    if not owner_raw:
        return None
    owner_key = _normalize_owner_ref(owner_raw)
    owner_entity = groups.get(owner_key) or users.get(owner_key)
    source = str(entity.get("_relay_source") or "")
    return OwnershipMatch(
        entity=entity,
        owner_ref=owner_raw,
        owner_entity=owner_entity,
        source=source,
    )


def format_ownership_answer(match: OwnershipMatch | None, *, query: str) -> str:
    if match is None:
        catalog = load_catalog_entities()
        names = sorted(
            {
                _entity_name(e)
                for e in catalog
                if e.get("kind") in OWNERSHIP_KINDS and _entity_name(e)
            }
        )
        hint = ", ".join(names[:12]) if names else "(no catalog entities loaded)"
        return (
            f"No catalog entity matched **{query}**. "
            f"Ownership answers come from Backstage catalog YAML, not RAG docs.\n\n"
            f"Known components: {hint}."
        )
    data = match.to_dict()
    title = data.get("title") or data.get("name")
    owner_label = data.get("owner_name") or data.get("owner")
    owner_kind = data.get("owner_kind") or "ref"
    lines = [
        f"**{title}** (`{data.get('name')}`, {data.get('kind')}) is owned by "
        f"**{owner_label}** ({owner_kind}).",
    ]
    if data.get("lifecycle"):
        lines.append(f"- Lifecycle: {data['lifecycle']}")
    if data.get("type"):
        lines.append(f"- Type: {data['type']}")
    slug = (data.get("annotations") or {}).get("github.com/project-slug")
    if slug:
        lines.append(f"- Repo: `{slug}`")
    if data.get("source"):
        lines.append(f"- Catalog source: `{data['source']}`")
    lines.append("\n(Source: catalog entities, not document search.)")
    return "\n".join(lines)
