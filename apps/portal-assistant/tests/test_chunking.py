import pytest

from portal_assistant.chunking import chunk_markdown


def test_chunk_markdown_splits_long_text():
    text = "paragraph one\n\n" + ("word " * 400)
    chunks = chunk_markdown(text, "a.md", "A", size=200, overlap=20)
    assert len(chunks) >= 2
    assert chunks[0].source == "a.md"
