# Audit log (Phase 2A.4)

Relay persists operator-facing audit events in Postgres (`audit_events`) for chat,
retrieval, tool routing, and confirm actions.

## Event types

| `event_type` | When |
| --- | --- |
| `chat_prompt` | After `/chat` completes (prompt preview, citation count, draft flag) |
| `tool_invoke` | Same turn (graph path + tool id) |
| `retrieval` | `docs_search` returns sources (query preview + source list) |
| `confirm_action` | Successful `/actions/confirm` (action, status, provider/ticket metadata) |

Actor fields (`actor_subject`, `actor_email`) populate when `USER_CONTEXT_HEADERS_ENABLED=true`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `AUDIT_LOG_ENABLED` | `true` | Set `false` to disable writes (query API unchanged) |
| `AUDIT_QUERY_SECRET` | empty | Required to enable `GET /internal/audit-events` |

`/health` includes `audit_log_enabled`.

## Query API

```bash
curl -s "http://localhost:8080/internal/audit-events?limit=20&thread_id=abc" \
  -H "X-Audit-Secret: $AUDIT_QUERY_SECRET"
```

Optional filters: `thread_id`, `event_type`, `limit` (max 200).

Local compose: set `AUDIT_QUERY_SECRET` in `.env` (see `.env.example`). Without it the endpoint returns **503** (same pattern as reindex webhook).

## Related

- [identity-ingress.md](identity-ingress.md) — user context headers
- [ticket-intake.md](ticket-intake.md) — confirm handoff metadata in audit payload
