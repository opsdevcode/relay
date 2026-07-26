# Local setup

This page is the TechDocs publish target for [`docs/local-setup.md`](https://github.com/opsdevcode/relay/blob/main/docs/local-setup.md) in the repository.

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)

## Steps

```bash
git clone git@github.com:opsdevcode/relay.git
cd relay

make up
open http://localhost:3000
make smoke   # optional
```

That's it — **no API keys, no manual ingest**. On first start the Portal Assistant indexes the bundled `knowledge/corpus/` automatically.

## Modes

| Mode | When | Behavior |
| --- | --- | --- |
| **Extractive** (default) | No synthesis credentials / `LLM_PROVIDER=none` | Best-matching excerpts from indexed docs + citations |
| **LLM** (optional) | `LLM_PROVIDER` + matching env (see `.env.example`) | Synthesized, cited answers via Anthropic, Azure OpenAI, or OpenAI-compatible endpoint |

## Try these prompts

| Prompt | Expected behavior |
| --- | --- |
| "What are the required resource tags?" | Excerpt from `standards/resource-tagging.md` |
| "What platform services are available?" | Lists registry |
| "Create a new service called demo-api" | Draft → Confirm → GitHub Actions workflow link |
| "I need a sandbox for a POC" | Draft → Confirm → GitHub issue template link |

## Troubleshooting

**Indexed documents: 0**

- Wait a few seconds after `make up` for startup ingestion
- Or run `make ingest`
- Check mount: `docker compose -f deploy/docker-compose.yml exec relay-assistant ls /knowledge/standards`

**Fresh start**

```bash
make down
docker volume rm deploy_postgres_data 2>/dev/null || true
make up
```

## Optional configuration

Copy overrides into `.env` (created automatically from `.env.example` on `make up`):

- `LLM_PROVIDER` and provider-specific vars — enable LLM synthesis (see `.env.example`)
- `INGEST_WEBHOOK_SECRET` — enable `POST /internal/reindex`

To index a custom markdown tree instead of the bundled corpus, add `deploy/docker-compose.override.yml` (gitignored) with a different volume mount.

## Backstage and TechDocs

```bash
make backstage-dev   # :3001 — open the Relay component → Docs tab
```

First doc build uses the TechDocs Docker generator (`app-config.yaml`); keep Docker running.
