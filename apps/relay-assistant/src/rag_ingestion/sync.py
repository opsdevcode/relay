"""Sync git-backed knowledge sources into a local checkout directory."""

from __future__ import annotations

import logging
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

from rag_ingestion.sources import source_type, validate_source

logger = logging.getLogger(__name__)


def sync_git_source(source: dict[str, Any], checkout_root: Path) -> Path:
    """Clone or update a shallow checkout; return the markdown root path.

    ``ref`` should be a branch or tag name (shallow clone uses ``--branch``).
    Optional ``subdir`` selects a path within the repo (doc-as-code output).
    """
    validate_source(source)
    if source_type(source) != "git":
        raise ValueError(f"sync_git_source requires type git, got {source_type(source)!r}")

    name = str(source["name"])
    url = str(source["url"]).strip()
    ref = str(source.get("ref") or "main").strip() or "main"
    subdir = str(source.get("subdir") or "").strip().lstrip("/")

    dest = checkout_root / name
    checkout_root.mkdir(parents=True, exist_ok=True)

    if (dest / ".git").is_dir():
        logger.info("Updating git source %s (%s @ %s)", name, url, ref)
        _run(["git", "-C", str(dest), "fetch", "--depth", "1", "origin", ref])
        _run(["git", "-C", str(dest), "checkout", "--force", "FETCH_HEAD"])
    else:
        if dest.exists():
            shutil.rmtree(dest)
        logger.info("Cloning git source %s (%s @ %s)", name, url, ref)
        _run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                ref,
                url,
                str(dest),
            ]
        )

    root = dest / subdir if subdir else dest
    if not root.is_dir():
        raise FileNotFoundError(f"git source {name!r}: checkout path does not exist: {root}")
    return root


def resolve_source_root(
    source: dict[str, Any],
    *,
    knowledge_path: str,
    checkout_root: Path,
) -> Path:
    """Return the local directory to glob for a filesystem or git source."""
    validate_source(source)
    if source_type(source) == "git":
        return sync_git_source(source, checkout_root)

    from rag_ingestion.sources import resolve_filesystem_base

    return resolve_filesystem_base(str(source["path"]), knowledge_path=knowledge_path)


def _run(cmd: list[str]) -> None:
    # Fixed argv list; never shell=True (bandit B603/B404 acceptable for git sync).
    result = subprocess.run(  # nosec B603
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git command failed ({result.returncode}): {' '.join(cmd)}\n{stderr}")
