#!/usr/bin/env python3
"""Render scaffold PR body with risk tier + CODEOWNERS (Phase 2A.3)."""

from __future__ import annotations

import os
import sys

from portal_assistant.risk_tiers import scaffold_pr_body_markdown


def main() -> int:
    service_name = os.environ.get("SERVICE_NAME", "").strip()
    if not service_name:
        print("SERVICE_NAME required", file=sys.stderr)
        return 1
    description = os.environ.get("DESCRIPTION", "Containerized service")
    github_org = os.environ.get("GITHUB_ORG", "opsdevcode")
    owner = os.environ.get("OWNER", "platform-team")
    sys.stdout.write(
        scaffold_pr_body_markdown(
            service_name=service_name,
            description=description,
            github_org=github_org,
            owner=owner,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
