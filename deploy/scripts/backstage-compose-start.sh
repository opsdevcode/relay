#!/usr/bin/env bash
# Backstage dev server for Docker Compose (profile: backstage).
set -euo pipefail

cd /workspace/apps/backstage

if ! command -v corepack >/dev/null 2>&1; then
  echo "corepack not found in Node image" >&2
  exit 1
fi

corepack enable

if [[ ! -d node_modules ]] || [[ ! -x node_modules/.bin/backstage-cli ]]; then
  echo "Running yarn install --immutable (first start may take a few minutes)…"
  yarn install --immutable
fi

exec yarn start
