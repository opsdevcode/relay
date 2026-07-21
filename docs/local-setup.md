# Local setup

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- Optional: `ANTHROPIC_API_KEY` for synthesized chat answers

## Steps

```bash
git clone git@github.com:opsdevcode/ai-developer-portal.git
cd ai-developer-portal

cp .env.example .env
# Optional: ANTHROPIC_API_KEY=... in .env (never commit .env)

make up
make ingest
open http://localhost:3000
```

By default, ingestion indexes the **bundled** sample docs under `knowledge/corpus/`. To index a different markdown tree, set `KNOWLEDGE_PATH` in `.env` to an absolute path before `make up`.

## Try these prompts

| Prompt | Expected behavior |
| --- | --- |
| "What are the required resource tags?" | Cited answer from `standards/resource-tagging.md` |
| "What platform services are available?" | Lists registry from `packages/platform-services/registry.yaml` |
| "Create a new service called demo-api" | Draft scaffold → **Confirm** → GitHub Actions **Run workflow** link |
| "I need a sandbox for a POC" | Draft → **Confirm** → GitHub issue template link |
| "How is cloudopt doing?" | Mock observability insight |

## Without Anthropic API key

Ingest still works. `/chat` returns retrieved chunks with source paths instead of a synthesized paragraph.

## Troubleshooting

**Indexed documents: 0**

- Confirm corpus mount: `docker compose -f deploy/docker-compose.yml exec portal-assistant ls /knowledge/proposals`
- Re-run `make ingest`

**API unreachable from browser**

- Web UI calls `http://localhost:8080` — ensure portal-assistant is healthy on port 8080

## Next steps

- Add Backstage (`apps/backstage/`) as catalog backbone
- Wire GitHub Actions scaffold workflow (see [docs/scaffolding.md](scaffolding.md))
- Swap FTS for pgvector embeddings when model keys are available
