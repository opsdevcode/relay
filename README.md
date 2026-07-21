# AI Developer Portal — Working Model

Local-first conversational internal developer portal: cited Q&A, platform-service registry, and draft-and-route actions.

License: [BSD 3-Clause](LICENSE)

## Quick start

No API keys required — answers use **extractive mode** from the bundled docs.

```bash
make up          # creates .env from .env.example if missing, starts stack, auto-indexes
open http://localhost:3000
make smoke       # optional sanity check
```

Optional: set `ANTHROPIC_API_KEY` in `.env` for synthesized LLM answers instead of extractive excerpts.

API: http://localhost:8080 · Health: http://localhost:8080/health

To index a custom markdown tree, add `deploy/docker-compose.override.yml` (see `deploy/docker-compose.override.example.yml`).

## Repo layout

```text
apps/
  portal-assistant/     # FastAPI: chat, RAG, tools
  web/                  # Static chat UI (Backstage plugin comes later)
packages/
  platform-services/    # Registry: knowledge + tools + views per capability
knowledge/
  corpus/               # Bundled sample docs (proposals, standards, docs)
  sources.yaml          # Ingestion config
templates/
  k8s-service/          # Golden-path: containerized service (any managed K8s)
deploy/
  docker-compose.yml
  k8s/base/             # Portable K8s (no cloud CRDs)
  k8s/overlays/         # aks | eks | gke — ingress/LB annotations only
catalog/entities/       # Seed catalog-info.yaml for demo
docs/
```

## Architecture (working model)

```mermaid
flowchart LR
  WEB[Web chat UI] --> PA[Portal Assistant]
  PA --> PG[(Postgres FTS / pgvector)]
  PA --> RD[(Redis sessions)]
  PA --> LLM[LLM provider API]
  ING[RAG ingestion] --> PG
  CORPUS[(knowledge corpus)] --> ING
```

Draft-and-route: mutating tools return a **draft**; the UI requires explicit confirmation before any GitHub action runs.

## Conversational surfaces

| Surface | Status |
| --- | --- |
| **Web** (embedded chat) | Working model — `apps/web/` |
| **Microsoft Teams** | Planned — bot adapter on Portal Assistant API |
| **Slack** | Planned — bot adapter on Portal Assistant API |

Backstage (phase 2) embeds the web chat; Teams and Slack reuse the same backend with channel-specific adapters.

## Kubernetes portability

| Concern | Base manifest | Cloud overlay |
| --- | --- | --- |
| Ingress | Generic `networking.k8s.io/v1` | Class + annotations per cloud |
| Secrets | K8s Secret / External Secrets pattern | ESO + cloud secret store |
| Identity | None (add OIDC at ingress) | Cognito / Google IAP / corporate IdP |
| Storage | `standard` StorageClass | Set per cluster in overlay |
| Images | GHCR (`ghcr.io/opsdevcode/...`) | Same — any registry |

See [docs/kubernetes.md](docs/kubernetes.md) · [docs/security-governance.md](docs/security-governance.md)

## Status

| Phase | Scope |
| --- | --- |
| **Now** | Local compose, FTS RAG, cited chat, platform-service registry, Actions-only scaffold |
| **Next** | LangGraph tools, Backstage backbone |
| **Later** | Managed K8s deploy (incl. AKS), hybrid RAG swap-in, **Teams and Slack** bots |
