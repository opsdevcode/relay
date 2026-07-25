"""Load and validate knowledge source definitions from sources.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from portal_assistant.config import settings

ALLOWED_SOURCE_TYPES = frozenset({"filesystem", "git"})


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.is_file():
        return {}
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def load_sources(config_path: Path) -> list[dict[str, Any]]:
    data = load_config(config_path)
    sources = data.get("sources", [])
    if not isinstance(sources, list):
        return []
    return [s for s in sources if isinstance(s, dict)]


def chunk_settings(config_path: Path) -> tuple[int, int]:
    data = load_config(config_path)
    chunk = data.get("chunk") or {}
    if not isinstance(chunk, dict):
        return 1200, 200
    size = int(chunk.get("size", 1200))
    overlap = int(chunk.get("overlap", 200))
    return size, overlap


def source_type(source: dict[str, Any]) -> str:
    raw = str(source.get("type") or "filesystem").strip().lower()
    return raw if raw else "filesystem"


def validate_source(source: dict[str, Any]) -> None:
    name = source.get("name")
    if not name or not isinstance(name, str):
        raise ValueError("source requires a string name")
    kind = source_type(source)
    if kind not in ALLOWED_SOURCE_TYPES:
        raise ValueError(f"source {name!r}: unsupported type {kind!r}")
    if kind == "filesystem":
        path = source.get("path")
        if not path or not isinstance(path, str):
            raise ValueError(f"source {name!r}: filesystem type requires path")
        return
    url = source.get("url")
    if not url or not isinstance(url, str):
        raise ValueError(f"source {name!r}: git type requires url")
    if not _allowed_git_url(url):
        raise ValueError(
            f"source {name!r}: git url must start with https://, http://, git@, or file://"
        )


def validate_sources(sources: list[dict[str, Any]]) -> None:
    for source in sources:
        validate_source(source)


def resolve_filesystem_base(path: str, knowledge_path: str | None = None) -> Path:
    root = Path(knowledge_path or settings.knowledge_path)
    if path.startswith("/"):
        return Path(path)
    return root / path.lstrip("/")


def _allowed_git_url(url: str) -> bool:
    lowered = url.strip().lower()
    return (
        lowered.startswith("https://")
        or lowered.startswith("http://")
        or lowered.startswith("git@")
        or lowered.startswith("file://")
    )


def default_config_path(knowledge_path: str | None = None) -> Path:
    kp = Path(knowledge_path or settings.knowledge_path)
    candidates = [
        kp.parent / "sources.yaml",
        Path("/app/knowledge/sources.yaml"),
        Path(__file__).resolve().parents[4] / "knowledge" / "sources.yaml",
    ]
    return next((p for p in candidates if p.is_file()), candidates[-1])
