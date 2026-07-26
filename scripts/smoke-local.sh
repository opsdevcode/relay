#!/usr/bin/env bash
# End-to-end smoke for the Relay API stack (requires `make up`).
# Keep in sync with docs/local-testing.md — update when HTTP behavior changes.
set -euo pipefail

API="${API:-http://localhost:8080}"

echo "==> health"
health="$(curl -sf "$API/health")"
echo "$health" | grep -q '"status":"ok"' || { echo "health check failed"; exit 1; }
echo "$health" | grep -q '"api_keys_required":false' || { echo "expected api_keys_required=false"; exit 1; }
echo "$health" | grep -q '"retrieval_mode":"hybrid"' || { echo "expected hybrid retrieval after ingest"; echo "$health"; exit 1; }

docs="$(echo "$health" | sed -n 's/.*"documents":\([0-9]*\).*/\1/p')"
if [ "${docs:-0}" -lt 1 ]; then
  echo "expected documents > 0 (run make up and wait for startup ingest)"
  exit 1
fi

echo "==> chat (extractive Q&A)"
answer="$(curl -sf -X POST "$API/chat" -H 'Content-Type: application/json' \
  -d '{"message":"What are the required resource tags?"}')"
echo "$answer" | grep -q 'Resource Tagging' || { echo "Q&A smoke failed"; echo "$answer"; exit 1; }
echo "$answer" | grep -q '"citations"' || { echo "expected citations in chat response"; echo "$answer"; exit 1; }
echo "$answer" | grep -q '"title"' || { echo "expected citation titles in chat response"; echo "$answer"; exit 1; }

echo "==> reindex webhook (disabled without INGEST_WEBHOOK_SECRET)"
reindex_code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/internal/reindex" \
  -H 'Content-Type: application/json' -d '{}')"
if [ "$reindex_code" != "503" ]; then
  echo "expected HTTP 503 for unconfigured reindex webhook, got $reindex_code"
  exit 1
fi

echo "==> platform services"
curl -sf "$API/platform-services" | grep -q 'golden-path-scaffold' || exit 1

echo "==> scaffold confirm (chat draft shape, no token)"
confirm="$(curl -sf -X POST "$API/actions/confirm" -H 'Content-Type: application/json' \
  -d '{"draft":{"action":"scaffold_service","mode":"workflow_dispatch","requires_confirmation":true,"inputs":{"service_name":"payments-api","description":"Payments","github_org":"opsdevcode"}}}')"
echo "$confirm" | grep -q 'workflow_url' || { echo "scaffold confirm failed"; echo "$confirm"; exit 1; }
echo "$confirm" | grep -q 'payments-api' || { echo "expected payments-api in confirm response"; echo "$confirm"; exit 1; }

echo "==> sandbox confirm (default github issue template)"
sandbox="$(curl -sf -X POST "$API/actions/confirm" -H 'Content-Type: application/json' \
  -d '{"draft":{"action":"request_sandbox","purpose":"Smoke POC","budget_usd_monthly":"500","requires_confirmation":true}}')"
echo "$sandbox" | grep -q 'intake_url' || { echo "sandbox confirm failed"; echo "$sandbox"; exit 1; }

echo "OK — local dev works without API keys"
