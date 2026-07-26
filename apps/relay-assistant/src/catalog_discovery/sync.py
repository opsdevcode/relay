from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from catalog_discovery.config import (
    default_output_path,
    discovery_enabled,
    load_discovery_config,
    resolve_github_token,
)
from catalog_discovery.github import discover_entities_from_github


def write_entities(path: Path, entities: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not entities:
        path.write_text(
            "# GitHub catalog discovery (Phase 2C.1) — run catalog_discovery.cli sync\n",
            encoding="utf-8",
        )
        return
    chunks: list[str] = []
    for entity in entities:
        chunks.append(yaml.safe_dump(entity, sort_keys=False).rstrip())
    path.write_text("\n---\n".join(chunks) + "\n", encoding="utf-8")


def run_discovery(
    *,
    config_path: Path | None = None,
    output_path: Path | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    config = load_discovery_config(config_path)
    if not config.github:
        raise ValueError(
            "catalog discovery not configured — add catalog/discovery.yaml with github.org"
        )
    api_token = token if token is not None else resolve_github_token()
    entities, logs = discover_entities_from_github(config.github, token=api_token)
    out = output_path or config.output_path or default_output_path()
    write_entities(out, entities)
    return {
        "status": "ok",
        "entities_written": len(entities),
        "output_path": str(out),
        "logs": logs,
    }


def discovered_entity_count(path: Path | None = None) -> int:
    target = path or default_output_path()
    if not target.is_file():
        return 0
    text = target.read_text(encoding="utf-8")
    if text.strip().startswith("#"):
        return 0
    count = 0
    for doc in yaml.safe_load_all(text):
        if isinstance(doc, dict) and doc.get("kind"):
            count += 1
    return count


def discovery_status() -> dict[str, Any]:
    config = load_discovery_config()
    return {
        "enabled": discovery_enabled(config),
        "org": config.github.org if config.github else None,
        "output_path": str(config.output_path),
        "discovered_entities": discovered_entity_count(config.output_path),
    }
