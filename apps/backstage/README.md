# Relay Backstage (Phase 1C.1)

Minimal Backstage app whose **software catalog** imports the repo-root seed at
[`catalog/entities/`](../../catalog/entities/).

Chat UI remains `apps/web/` (1C.2 will embed it). TechDocs and Scaffolder
registration are later roadmap items (1C.3 / 1C.4).

## Prerequisites

- **Node.js 22 or 24** (see `package.json` `engines`; asdf: `nodejs 22.23.1`)
- Yarn via Corepack (`corepack enable`) — this app pins **Yarn 4.13.0**

## Local run

```bash
# from repo root
make backstage-install   # yarn install --immutable (first time: yarn install)
make backstage-dev       # frontend :3001 + backend :7007
```

Open http://localhost:3001 — Catalog should list **Relay** and **CloudOpt**,
owned by **platform-team**.

Port **3001** avoids clashing with Relay web (`make up` → `:3000`).

## Catalog location

`app-config.yaml` → `catalog.locations` points at:

```text
../../../../catalog/entities/catalog.yaml
```

(relative to `packages/backend`). Adding entities: edit that YAML (or add more
`*.yaml` files under `catalog/entities/` and another location entry).

## Tests

| Layer | Command |
| --- | --- |
| Catalog contract (Python, always in `make ci`) | `pytest` → `test_catalog_entities.py`, `test_backstage_config.py` |
| Backstage unit tests | `make backstage-test` |
| Backstage E2E (Playwright) | `make backstage-e2e` |

New catalog entities or Backstage config changes **must** update contract tests and
Playwright specs in the same PR ([docs/tdd.md](../../docs/tdd.md)).

## Next (not in 1C.1)

1. Embed Relay chat (1C.2)
2. TechDocs for at least one entity (1C.3)
3. Register `templates/k8s-service/` as a Scaffolder template (1C.4)
4. GitHub org discovery / OAuth for non-prod
