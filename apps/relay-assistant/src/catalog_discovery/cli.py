from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from catalog_discovery.sync import run_discovery


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub catalog-info discovery (Phase 2C.1)")
    sub = parser.add_subparsers(dest="command", required=True)
    sync = sub.add_parser("sync", help="Fetch catalog-info.yaml from in-scope GitHub repos")
    sync.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to catalog/discovery.yaml (default: repo catalog/discovery.yaml)",
    )
    sync.add_argument("--output", type=Path, default=None, help="Override output entity file")
    args = parser.parse_args(argv)

    if args.command == "sync":
        try:
            result = run_discovery(config_path=args.config, output_path=args.output)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"discovery failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
