#!/usr/bin/env bash
# Smoke test local stack — no API keys required.
set -euo pipefail

API="${API:-http://localhost:8080}"

echo "==> health"
health="$(curl -sf "$API/health")"
echo "$health" | grep -q '"status":"ok"' || { echo "health check failed"; exit 1; }
echo "$health" | grep -q '"api_keys_required":false' || { echo "expected api_keys_required=false"; exit 1; }

docs="$(echo "$health" | sed -n 's/.*"documents":\([0-9]*\).*/\1/p')"
if [ "${docs:-0}" -lt 1 ]; then
  echo "expected documents > 0 (run make up and wait for startup ingest)"
  exit 1
fi

echo "==> chat (extractive Q&A)"
answer="$(curl -sf -X POST "$API/chat" -H 'Content-Type: application/json' \
  -d '{"message":"What are the required resource tags?"}')"
echo "$answer" | grep -q 'Resource Tagging' || { echo "Q&A smoke failed"; echo "$answer"; exit 1; }

echo "==> platform services"
curl -sf "$API/platform-services" | grep -q 'golden-path-scaffold' || exit 1

echo "==> scaffold confirm (workflow link, no token)"
confirm="$(curl -sf -X POST "$API/actions/confirm" -H 'Content-Type: application/json' \
  -d '{"draft":{"action":"scaffold_service","service_name":"demo-api","description":"Demo"}}')"
echo "$confirm" | grep -q 'workflow_url' || { echo "scaffold confirm failed"; echo "$confirm"; exit 1; }

echo "OK — local dev works without API keys"
