from __future__ import annotations

import pytest

from portal_assistant.chunking import chunk_markdown
from portal_assistant.llm import format_extractive_answer


def test_chunk_markdown_splits_long_text():
    text = "paragraph one\n\n" + ("word " * 400)
    chunks = chunk_markdown(text, "a.md", "A", size=200, overlap=20)
    assert len(chunks) >= 2
    assert chunks[0].source == "a.md"


def test_extractive_answer_without_api_key():
    contexts = [
        {
            "source": "/knowledge/standards/resource-tagging.md",
            "title": "Resource Tagging Standard",
            "content": "## Required tags\n\n| Tag | owner |\n| --- | --- |\n| owner | team |",
        }
    ]
    answer = format_extractive_answer("What are required resource tags?", contexts)
    assert "Resource Tagging Standard" in answer
    assert "extractive mode" in answer
    assert "ANTHROPIC" not in answer
