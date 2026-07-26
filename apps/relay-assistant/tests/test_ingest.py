from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from portal_assistant.chunking import Chunk
from rag_ingestion.cli import ingest
from rag_ingestion.sources import (
    load_sources,
    resolve_filesystem_base,
    validate_source,
    validate_sources,
)
from rag_ingestion.sync import resolve_source_root, sync_git_source


class RecordingStore:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.deleted = 0
        self.inited = False

    def init_schema(self) -> None:
        self.inited = True

    def upsert_chunks(self, chunks: list[Chunk]) -> int:
        self.chunks.extend(chunks)
        return len(chunks)

    def delete_all(self) -> int:
        n = len(self.chunks)
        self.chunks.clear()
        self.deleted = n
        return n

    def count(self) -> int:
        return len(self.chunks)


def _write_sources(tmp: Path, sources: list[dict[str, Any]]) -> Path:
    cfg = tmp / "sources.yaml"
    cfg.write_text(yaml.safe_dump({"sources": sources, "chunk": {"size": 200, "overlap": 20}}))
    return cfg


def test_validate_filesystem_source_requires_path():
    with pytest.raises(ValueError, match="requires path"):
        validate_source({"name": "x", "type": "filesystem"})


def test_validate_git_source_requires_url():
    with pytest.raises(ValueError, match="requires url"):
        validate_source({"name": "x", "type": "git"})


def test_validate_git_url_scheme():
    with pytest.raises(ValueError, match="git url must start"):
        validate_source({"name": "x", "type": "git", "url": "ftp://evil.example/repo"})


def test_resolve_filesystem_base_absolute_and_relative():
    assert resolve_filesystem_base("/knowledge/docs") == Path("/knowledge/docs")
    assert resolve_filesystem_base("docs", knowledge_path="/knowledge") == Path("/knowledge/docs")


def test_ingest_filesystem_source(tmp_path: Path):
    corpus = tmp_path / "corpus" / "docs"
    corpus.mkdir(parents=True)
    (corpus / "hello-world.md").write_text("# Hello\n\nTagging policy requires env.\n")

    cfg = _write_sources(
        tmp_path,
        [
            {
                "name": "corpus-docs",
                "path": str(corpus),
                "glob": "**/*.md",
                "visibility": "public",
            }
        ],
    )
    store = RecordingStore()
    total = ingest(
        cfg,
        store=store,  # type: ignore[arg-type]
        knowledge_path=str(tmp_path / "corpus"),
        checkout_root=tmp_path / "checkouts",
    )
    assert store.inited
    assert total >= 1
    assert any("Tagging policy" in c.content for c in store.chunks)


def test_ingest_applies_frontmatter_and_section_titles(tmp_path: Path):
    corpus = tmp_path / "docs"
    corpus.mkdir()
    (corpus / "tags.md").write_text(
        """---
title: Tagging Policy
owner: platform-team
updated: 2026-02-01
---
## Required tags

Every resource needs an environment tag.
"""
    )
    cfg = _write_sources(
        tmp_path,
        [{"name": "docs", "path": str(corpus), "glob": "**/*.md", "visibility": "public"}],
    )
    store = RecordingStore()
    ingest(cfg, store=store, knowledge_path=str(tmp_path))  # type: ignore[arg-type]
    assert len(store.chunks) == 1
    chunk = store.chunks[0]
    assert chunk.title == "Tagging Policy — Required tags"
    assert chunk.doc_owner == "platform-team"
    assert chunk.doc_updated == "2026-02-01"
    assert chunk.allowed_groups == ()
    assert "environment tag" in chunk.content
    assert "---" not in chunk.content


def test_ingest_frontmatter_visibility_and_allowed_groups(tmp_path: Path):
    corpus = tmp_path / "docs"
    corpus.mkdir()
    (corpus / "secret.md").write_text(
        """---
title: Restricted runbook
owner: platform-team
visibility: restricted
allowed_groups:
  - relay-platform-admins
---
# Secret

Do not share.
"""
    )
    cfg = _write_sources(
        tmp_path,
        [{"name": "docs", "path": str(corpus), "glob": "**/*.md", "visibility": "public"}],
    )
    store = RecordingStore()
    ingest(cfg, store=store, knowledge_path=str(tmp_path))  # type: ignore[arg-type]
    chunk = store.chunks[0]
    assert chunk.visibility == "restricted"
    assert chunk.allowed_groups == ("relay-platform-admins",)
    assert "Do not share" in chunk.content


def test_ingest_full_clears_stale_chunks(tmp_path: Path):
    corpus = tmp_path / "docs"
    corpus.mkdir()
    (corpus / "keep.md").write_text("# Keep\n\nStill here.\n")
    cfg = _write_sources(
        tmp_path,
        [{"name": "docs", "path": str(corpus), "glob": "**/*.md", "visibility": "public"}],
    )
    store = RecordingStore()
    store.chunks.append(Chunk(source="gone.md", title="Gone", content="stale", visibility="public"))

    ingest(cfg, store=store, full=True, knowledge_path=str(tmp_path))  # type: ignore[arg-type]
    assert store.deleted == 1
    assert all(c.title != "Gone" for c in store.chunks)
    assert any("Still here" in c.content for c in store.chunks)


def test_sync_git_source_clones_when_missing(tmp_path: Path):
    source = {
        "name": "standards",
        "type": "git",
        "url": "https://github.com/example/standards.git",
        "ref": "main",
        "subdir": "docs",
    }
    dest = tmp_path / "standards"
    docs = dest / "docs"

    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
        calls.append(cmd)
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "policy.md").write_text("# Policy\n")
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        result.stdout = ""
        return result

    with patch("rag_ingestion.sync.subprocess.run", side_effect=fake_run):
        root = sync_git_source(source, tmp_path)
    assert root == docs
    assert calls
    assert calls[0][:3] == ["git", "clone", "--depth"]


def test_resolve_source_root_git_delegates(tmp_path: Path):
    source = {
        "name": "standards",
        "type": "git",
        "url": "https://github.com/example/standards.git",
        "ref": "main",
    }
    checkout = tmp_path / "checkouts"
    (checkout / "standards").mkdir(parents=True)
    (checkout / "standards" / ".git").mkdir()
    (checkout / "standards" / "readme.md").write_text("hi")

    with patch("rag_ingestion.sync.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        root = resolve_source_root(
            source,
            knowledge_path="/knowledge",
            checkout_root=checkout,
        )
    assert root == checkout / "standards"
    assert run.call_count == 2  # fetch + checkout


def test_load_sources_roundtrip(tmp_path: Path):
    cfg = _write_sources(
        tmp_path,
        [{"name": "a", "path": "/knowledge/a", "glob": "**/*.md"}],
    )
    sources = load_sources(cfg)
    validate_sources(sources)
    assert sources[0]["name"] == "a"


def test_reindex_webhook_requires_secret(monkeypatch: pytest.MonkeyPatch):
    from portal_assistant import main as main_mod

    monkeypatch.setattr(main_mod.settings, "ingest_webhook_secret", "")
    app = FastAPI()
    app.post("/internal/reindex")(main_mod.reindex_corpus)
    with TestClient(app) as client:
        resp = client.post("/internal/reindex", json={"full": False})
    assert resp.status_code == 503


def test_reindex_webhook_rejects_bad_secret(monkeypatch: pytest.MonkeyPatch):
    from portal_assistant import main as main_mod

    monkeypatch.setattr(main_mod.settings, "ingest_webhook_secret", "correct-secret")

    def boom(**_kwargs: Any) -> int:
        raise AssertionError("should not ingest")

    monkeypatch.setattr(main_mod, "_run_ingest", boom)

    app = FastAPI()
    app.post("/internal/reindex")(main_mod.reindex_corpus)
    with TestClient(app) as client:
        resp = client.post(
            "/internal/reindex",
            json={"full": True},
            headers={"X-Ingest-Secret": "wrong"},
        )
    assert resp.status_code == 401


def test_reindex_webhook_runs_ingest(monkeypatch: pytest.MonkeyPatch):
    from portal_assistant import main as main_mod

    monkeypatch.setattr(main_mod.settings, "ingest_webhook_secret", "correct-secret")
    called: dict[str, Any] = {}

    def fake_ingest(*, full: bool = False) -> int:
        called["full"] = full
        return 3

    monkeypatch.setattr(main_mod, "_run_ingest", fake_ingest)
    monkeypatch.setattr(main_mod.store, "count", lambda: 12)
    monkeypatch.setattr(main_mod.store, "retrieval_mode", lambda: "hybrid")

    app = FastAPI()
    app.post("/internal/reindex")(main_mod.reindex_corpus)
    with TestClient(app) as client:
        resp = client.post(
            "/internal/reindex",
            json={"full": True},
            headers={"X-Ingest-Secret": "correct-secret"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["full"] is True
    assert body["chunks_indexed"] == 3
    assert body["documents"] == 12
    assert called["full"] is True
