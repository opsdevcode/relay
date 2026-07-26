# GitHub catalog discovery (Phase 2C.1)

The discovery processor pulls **`catalog-info.yaml`** (and extra paths) from in-scope GitHub org repos and writes **`catalog/entities/discovered-github.yaml`** for Backstage import.

## Configure

Copy [`catalog/discovery.example.yaml`](../catalog/discovery.example.yaml) to `catalog/discovery.yaml` (the repo includes a demo config for `opsdevcode/relay`).

```yaml
github:
  org: your-org
  repos: []          # empty = list org repos (up to max_repos)
  paths:
    - catalog-info.yaml
  max_repos: 100
output_path: catalog/entities/discovered-github.yaml
```

Authentication uses **`GITHUB_TOKEN`** or **`GITHUB_API_TOKEN`** (or `GITHUB_API_TOKEN` / ticket token via settings). Public repos work unauthenticated with lower rate limits.

## Run locally

```bash
make catalog-discover
# or
cd apps/relay-assistant && PYTHONPATH=src python -m catalog_discovery.cli sync
```

Backstage loads entities via [`catalog/entities/discovered-github-location.yaml`](../catalog/entities/discovered-github-location.yaml) (registered in `app-config.yaml`).

## Automation

Same operator secret as corpus reindex:

```bash
curl -sS -X POST http://localhost:8080/internal/catalog-discovery/sync \
  -H "X-Ingest-Secret: $INGEST_WEBHOOK_SECRET"
```

`/health` includes `enabled`, `org`, `output_path`, and `discovered_entities`.

## Annotations

Each ingested entity is stamped with:

- `relay.dev/discovered-from`: `org/repo@path`
- `github.com/project-slug` when missing

## Related

- [catalog-as-code proposal](../knowledge/corpus/proposals/catalog-as-code.md)
- [roadmap.md](roadmap.md) — Phase 2C.2 ownership resolution ([catalog-ownership.md](catalog-ownership.md))
