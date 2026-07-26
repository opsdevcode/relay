from __future__ import annotations

import argparse
import logging
from glob import glob
from pathlib import Path

from portal_assistant.chunking import chunk_markdown
from portal_assistant.config import settings
from portal_assistant.frontmatter import metadata_group_list, metadata_str, parse_frontmatter
from portal_assistant.store import DocumentStore
from rag_ingestion.sources import (
    chunk_settings,
    default_config_path,
    load_sources,
    validate_sources,
)
from rag_ingestion.sync import resolve_source_root

logger = logging.getLogger(__name__)


def ingest(
    config_path: Path | None = None,
    *,
    store: DocumentStore | None = None,
    full: bool = False,
    checkout_root: Path | None = None,
    knowledge_path: str | None = None,
) -> int:
    """Index markdown sources into Postgres.

    When ``full`` is true, existing documents are deleted first so removed files
    do not leave stale chunks. Git sources are synced under ``checkout_root``
    before globbing.
    """
    cfg = config_path or default_config_path(knowledge_path)
    sources = load_sources(cfg)
    validate_sources(sources)
    size, overlap = chunk_settings(cfg)

    doc_store = store or DocumentStore(settings.database_url)
    doc_store.init_schema()
    if full:
        deleted = doc_store.delete_all()
        logger.info("Full reindex: deleted %s existing documents", deleted)
        print(f"full reindex — deleted {deleted} existing documents")

    kp = knowledge_path or settings.knowledge_path
    checkout = checkout_root or Path(settings.ingest_checkout_dir)

    total = 0
    for source in sources:
        base = resolve_source_root(
            source,
            knowledge_path=kp,
            checkout_root=checkout,
        )
        pattern = str(base / source.get("glob", "**/*.md"))
        visibility = source.get("visibility", "public")
        name = source.get("name", base.name)
        matched = sorted(glob(pattern, recursive=True))
        if not matched:
            logger.warning("No files matched for source %s (%s)", name, pattern)
            print(f"warning: no files matched for {name} ({pattern})")
        for file_path in matched:
            path = Path(file_path)
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.as_posix()
            meta, body = parse_frontmatter(text)
            doc_title = metadata_str(meta, "title") or path.stem.replace("-", " ").title()
            doc_owner = metadata_str(meta, "owner")
            doc_updated = metadata_str(meta, "updated")
            doc_visibility = metadata_str(meta, "visibility") or visibility
            allowed_groups = metadata_group_list(meta, "allowed_groups")
            chunks = chunk_markdown(body, rel, doc_title, size=size, overlap=overlap)
            for chunk in chunks:
                chunk.visibility = doc_visibility
                chunk.doc_owner = doc_owner
                chunk.doc_updated = doc_updated
                chunk.allowed_groups = allowed_groups
            total += doc_store.upsert_chunks(chunks)
            print(f"indexed {rel} ({len(chunks)} chunks)")

    print(f"done — {doc_store.count()} documents in store")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge sources")
    parser.add_argument("--config", type=Path, default=None)
    sub = parser.add_subparsers(dest="cmd")
    ingest_parser = sub.add_parser("ingest", help="Index configured knowledge sources")
    ingest_parser.add_argument(
        "--full",
        action="store_true",
        help="Delete all documents before indexing (drops stale chunks)",
    )
    args = parser.parse_args()
    if args.cmd == "ingest":
        ingest(args.config, full=bool(args.full))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
