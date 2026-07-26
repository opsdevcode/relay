#!/usr/bin/env python3
"""Register a scaffolded service catalog-info.yaml in scaffolded-services Location."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portal_assistant.scaffold_catalog import catalog_target, register_scaffolded_service


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service_name", help="Kebab-case service name")
    args = parser.parse_args(argv)
    try:
        added = register_scaffolded_service(args.service_name, repo_root=_repo_root())
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    target = catalog_target(args.service_name)
    if added:
        print(f"Registered {target} in scaffolded-services Location")
    else:
        print(f"Already registered: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
