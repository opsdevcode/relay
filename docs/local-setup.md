# Local setup

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- A local clone of [`opsdevcode/sn`](https://github.com/opsdevcode/sn) (proposals knowledge corpus)
- Optional: `ANTHROPIC_API_KEY` for synthesized chat answers

## Steps

```bash
git clone git@github.com:opsdevcode/ai-developer-portal.git
cd ai-developer-portal

cp .env.example .env
# Edit .env — set KNOWLEDGE_PATH to your sn clone, e.g.:
# KNOWLEDGE_PATH=/Users/you/sn

make up
make ingest
open http://localhost:3000
```

## Try these prompts

| Prompt | Expected behavior |
| --- | --- |
| "What are the required Azure resource tags?" | Cited answer from tagging standard (after ingest) |
| "What platform services are available?" | Lists registry from `packages/platform-services/registry.yaml` |
| "Create a new service called demo-api" | Draft scaffold — confirm button (simulated without GITHUB_TOKEN) |
| "I need a sandbox for a POC" | Draft sandbox request |
| "How is cloudopt doing?" | Mock observability insight |

## Without Anthropic API key

Ingest still works. `/chat` returns retrieved chunks with source paths instead of a synthesized paragraph.

## Troubleshooting

**Indexed documents: 0**

- Confirm `KNOWLEDGE_PATH` mounts correctly: `docker compose -f deploy/docker-compose.yml exec portal-assistant ls /knowledge/proposals`
- Re-run `make ingest`

**API unreachable from browser**

- Web UI calls `http://localhost:8080` — ensure portal-assistant container is healthy on port 8080

## Next steps

- Add Backstage (`apps/backstage/`) as catalog backbone
- Wire `GITHUB_TOKEN` for real PR/Issue draft-and-route
- Swap FTS for pgvector embeddings when Azure/OpenAI keys are available
