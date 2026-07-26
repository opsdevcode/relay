# Relay Backstage (Phase 1C)

Minimal Backstage app whose **software catalog** imports the repo-root seed at
[`catalog/entities/`](../../catalog/entities/). **Relay Assistant** chat is
embedded at `/relay` via iframe (1C.2) pointing at `relay.chatEmbedUrl`
(default `http://localhost:3000`). **TechDocs** for the **Relay** component (1C.3)
publishes markdown from [`docs/techdocs/relay/`](../../docs/techdocs/relay/).

Scaffolder **K8s Service (Golden Path)** template (1C.4) dispatches the same
[`scaffold-k8s-service.yml`](../../.github/workflows/scaffold-k8s-service.yml) workflow as Relay chat.

## Prerequisites

- **Node.js 22 or 24** (see `package.json` `engines`; asdf: `nodejs 22.23.1`)
- Yarn via Corepack (`corepack enable`) — this app pins **Yarn 4.13.0**

## Local run

```bash
# from repo root
make backstage-install   # yarn install --immutable (first time: yarn install)
make up                  # Relay web :3000 + API :8080 (for embedded chat)
make backstage-dev       # frontend :3001 + backend :7007
```

Open http://localhost:3001 — use **Relay Assistant** in the sidebar for chat,
or **Catalog** for **Relay** / **CloudOpt** (owned by **platform-team**).

Port **3001** avoids clashing with Relay web (`make up` → `:3000`).

## Embedded chat (1C.2)

`app-config.yaml`:

- `relay.chatEmbedUrl` — URL loaded in the `/relay` iframe (local: port 3000).
- `backend.csp.frame-src` — must include the chat origin so the iframe can load.

Production: set `relay.chatEmbedUrl` to your deployed web UI URL and extend CSP
accordingly.

## Catalog location

`app-config.yaml` → `catalog.locations` points at:

```text
../../../../catalog/entities/catalog.yaml
```

(relative to `packages/backend`). Adding entities: edit that YAML (or add more
`*.yaml` files under `catalog/entities/` and another location entry).

## TechDocs (1C.3)

The **Relay** component annotation `backstage.io/techdocs-ref` points at
`docs/techdocs/relay/` (MkDocs + `techdocs-core`). Open **Catalog → Relay → Docs**.
The first build uses the Docker generator (`techdocs.generator.runIn: docker` in
`app-config.yaml`); keep Docker running locally.

## Scaffolder (1C.4)

**Create** (`/create`) lists **K8s Service (Golden Path)** from
[`templates/k8s-service/template.yaml`](../../templates/k8s-service/template.yaml).
The template calls `github:actions:dispatch` on `scaffold-k8s-service.yml` when
`GITHUB_TOKEN` is set for the Backstage GitHub integration; otherwise use the
post-run link to trigger the workflow manually (see [scaffolding.md](../../docs/scaffolding.md)).

## Tests

| Layer | Command |
| --- | --- |
| Catalog contract (Python, always in `make ci`) | `pytest` → `test_catalog_entities.py`, `test_backstage_config.py` |
| Backstage unit tests | `make backstage-test` |
| Backstage E2E (Playwright) | `make backstage-e2e` |

New catalog entities or Backstage config changes **must** update contract tests and
Playwright specs in the same PR ([docs/tdd.md](../../docs/tdd.md)).

## Next (not in 1C.4)

1. GitHub org discovery / OAuth for non-prod (1D+)
