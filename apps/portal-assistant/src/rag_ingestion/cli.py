from __future__ import annotations

import argparse
from glob import glob
from pathlib import Path

import yaml

from portal_assistant.chunking import chunk_markdown
from portal_assistant.config import settings
from portal_assistant.store import DocumentStore


def load_sources(config_path: Path) -> list[dict]:
    with config_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    sources = data.get("sources", [])
    return sources if isinstance(sources, list) else []


def resolve_base(path: str) -> Path:
    if path.startswith("/"):
        return Path(path)
    return Path(settings.knowledge_path) / path.lstrip("/")


def ingest(config_path: Path | None = None) -> int:
    if config_path is None:
        candidates = [
            Path(settings.knowledge_path).parent / "sources.yaml",
            Path("/app/knowledge/sources.yaml"),
            Path(__file__).resolve().parents[4] / "knowledge" / "sources.yaml",
        ]
        cfg = next((p for p in candidates if p.is_file()), candidates[-1])
    else:
        cfg = config_path
    chunk_cfg = yaml.safe_load(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
    size = chunk_cfg.get("chunk", {}).get("size", 1200)
    overlap = chunk_cfg.get("chunk", {}).get("overlap", 200)

    store = DocumentStore(settings.database_url)
    store.init_schema()

    total = 0
    for source in load_sources(cfg):
        base = resolve_base(source["path"])
        pattern = str(base / source.get("glob", "**/*.md"))
        visibility = source.get("visibility", "public")
        for file_path in sorted(glob(pattern, recursive=True)):
            path = Path(file_path)
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.as_posix()
            title = path.stem.replace("-", " ").title()
            chunks = chunk_markdown(text, rel, title, size=size, overlap=overlap)
            for chunk in chunks:
                chunk.visibility = visibility
            total += store.upsert_chunks(chunks)
            print(f"indexed {rel} ({len(chunks)} chunks)")

    print(f"done — {store.count()} documents in store")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge sources")
    parser.add_argument("--config", type=Path, default=None)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("ingest")
    args = parser.parse_args()
    if args.cmd == "ingest":
        ingest(args.config)


if __name__ == "__main__":
    main()
