from portal_assistant.chunking import chunk_markdown, chunk_title_for_piece
from portal_assistant.frontmatter import metadata_str, parse_frontmatter


def test_parse_frontmatter_extracts_yaml_and_body():
    raw = """---
title: Resource Tagging Standard
owner: platform-team
updated: 2026-01-15
---

# Resource Tagging

Body text here.
"""
    meta, body = parse_frontmatter(raw)
    assert meta["title"] == "Resource Tagging Standard"
    assert meta["owner"] == "platform-team"
    assert body.startswith("# Resource Tagging")
    assert "---" not in body.splitlines()[0]


def test_parse_frontmatter_absent_returns_full_text():
    meta, body = parse_frontmatter("# Hello\n\nContent")
    assert meta == {}
    assert body.startswith("# Hello")


def test_metadata_str_missing_key():
    assert metadata_str({}, "owner") == ""


def test_chunk_title_uses_section_heading():
    piece = "## Required tags\n\nAll resources must have env."
    assert chunk_title_for_piece("Resource Tagging", piece, 0, 2) == (
        "Resource Tagging — Required tags"
    )


def test_chunk_title_part_when_no_heading():
    assert chunk_title_for_piece("Long Doc", "plain text", 1, 3) == "Long Doc — part 2"


def test_chunk_markdown_splits_long_text():
    text = "paragraph one\n\n" + ("word " * 400)
    chunks = chunk_markdown(text, "a.md", "A", size=200, overlap=20)
    assert len(chunks) >= 2
    assert chunks[0].source == "a.md"
