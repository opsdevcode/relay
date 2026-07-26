"""Parse optional YAML frontmatter from markdown corpus files."""

from __future__ import annotations

import re
from typing import Any

import yaml

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (metadata, body). Metadata is empty when frontmatter is absent."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text.strip()
    raw = match.group(1)
    try:
        meta = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    body = text[match.end() :].strip()
    return meta, body


def metadata_str(meta: dict[str, Any], key: str) -> str:
    value = meta.get(key)
    if value is None:
        return ""
    return str(value).strip()


def metadata_group_list(meta: dict[str, Any], key: str) -> tuple[str, ...]:
    value = meta.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(g.strip() for g in value.split(",") if g.strip())
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            token = str(item).strip()
            if token:
                out.append(token)
        return tuple(out)
    return ()
