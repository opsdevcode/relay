from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    source: str
    title: str
    content: str
    visibility: str = "public"


def slugify(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return base or "doc"


def chunk_markdown(text: str, source: str, title: str, size: int = 1200, overlap: int = 200) -> list[Chunk]:
    text = text.strip()
    if not text:
        return []
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            break_at = text.rfind("\n\n", start, end)
            if break_at > start + size // 2:
                end = break_at
        piece = text[start:end].strip()
        if piece:
            chunks.append(Chunk(source=source, title=title, content=piece))
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
