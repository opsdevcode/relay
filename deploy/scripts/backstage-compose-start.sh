#!/usr/bin/env bash
# Backstage dev server for Docker Compose (profile: backstage).
set -euo pipefail

cd /workspace/apps/backstage

if ! command -v corepack >/dev/null 2>&1; then
  echo "corepack not found in Node image" >&2
  exit 1
fi

corepack enable

need_install=false
if [[ ! -d node_modules ]] || [[ ! -x node_modules/.bin/backstage-cli ]]; then
  need_install=true
fi
if [[ "${need_install}" == "false" ]] && ! node -e "require('@rspack/binding')" >/dev/null 2>&1; then
  echo "Native bindings missing or wrong platform (common when node_modules came from the host)."
  need_install=true
fi

if [[ "${need_install}" == "true" ]]; then
  echo "Running yarn install --immutable (first start may take a few minutes)…"
  yarn install --immutable
fi

exec yarn start
