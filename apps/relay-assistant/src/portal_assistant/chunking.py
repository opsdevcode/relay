from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)


@dataclass
class Chunk:
    source: str
    title: str
    content: str
    visibility: str = "public"
    doc_owner: str = ""
    doc_updated: str = ""


def slugify(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return base or "doc"


def _heading_in_text(piece: str) -> str | None:
    match = _HEADING_RE.search(piece)
    if not match:
        return None
    return match.group(1).strip()


def chunk_title_for_piece(doc_title: str, piece: str, index: int, total: int) -> str:
    heading = _heading_in_text(piece)
    if heading and heading.lower() != doc_title.lower():
        return f"{doc_title} — {heading}"
    if total <= 1:
        return doc_title
    return f"{doc_title} — part {index + 1}"


def chunk_markdown(
    text: str, source: str, title: str, size: int = 1200, overlap: int = 200
) -> list[Chunk]:
    text = text.strip()
    if not text:
        return []
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            break_at = text.rfind("\n\n", start, end)
            if break_at > start + size // 2:
                end = break_at
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    total = len(pieces)
    return [
        Chunk(
            source=source,
            title=chunk_title_for_piece(title, piece, idx, total),
            content=piece,
        )
        for idx, piece in enumerate(pieces)
    ]
