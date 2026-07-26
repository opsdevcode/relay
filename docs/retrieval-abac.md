# Retrieval ABAC (Phase 2D.1)

Hybrid / FTS retrieval filters indexed chunks by **visibility** and **user groups** so restricted corpus content is not returned to anonymous or unauthorized callers.

## Visibility levels

| Value | Who can retrieve |
| --- | --- |
| `public` | Everyone (always indexed in search results when ABAC applies) |
| `internal` | Authenticated users only (`X-Auth-Request-*` with a subject or email) |
| `restricted` | Callers whose subject, email, or IdP **group** matches `doc_owner`, or whose groups overlap chunk **`allowed_groups`** |

Set visibility on a **source** in `knowledge/sources.yaml`, or override per file in markdown frontmatter.

## Frontmatter

```yaml
---
title: Incident runbook
owner: platform-team
visibility: restricted
allowed_groups:
  - relay-platform-admins
  - platform-team
---
```

| Field | Stored on chunk |
| --- | --- |
| `owner` | `doc_owner` |
| `visibility` | `visibility` (overrides source default) |
| `allowed_groups` | PostgreSQL `allowed_groups` text array |

Re-index after metadata changes: `make ingest-full`.

## Enable filtering

| Mode | Behavior |
| --- | --- |
| Local default | No filter when ingress user headers are off (`RETRIEVAL_ABAC_ENABLED` false, no user context) |
| Ingress (1D.2) | `USER_CONTEXT_HEADERS_ENABLED=true` — filter using oauth2-proxy headers on `/chat` |
| Strict (2D.1) | `RETRIEVAL_ABAC_ENABLED=true` — filter even without user; unauthenticated callers see **`public`** only |

`/health` includes `retrieval_abac_enabled` and `user_context_headers_enabled`.

## Related

- [identity-ingress.md](identity-ingress.md) — oauth2-proxy headers
- [corpus-pipeline.md](corpus-pipeline.md) — ingest and frontmatter
- [roadmap.md](roadmap.md) — Phase 2D.2 groundedness eval set
