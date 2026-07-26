# Local run with Docker Compose

Relay supports **Make** (recommended in the README) and **plain Docker Compose** from the repo root. Both use the same [`deploy/docker-compose.yml`](../deploy/docker-compose.yml) definition.

## Local ports (Docker Compose)

Published on the **host** (what you open in the browser or `curl`):

| Host port | Service (compose) | URL / use |
| --- | --- | --- |
| **3000** | `web` | Relay chat UI — http://localhost:3000 |
| **8080** | `relay-assistant` | Relay API — http://localhost:8080 (`/health`, `/chat`, `/platform-services`) |
| **3001** | `backstage` (profile `backstage`) | Backstage **frontend** — http://localhost:3001 (catalog, Create, Relay Assistant, Observability, TechDocs) |
| **7007** | `backstage` (profile `backstage`) | Backstage **backend** API — http://localhost:7007 (used by the UI; not the main entry URL) |

**Not published** (container network only): Postgres `5432`, Redis `6379`.

**Portal-only** (`docker compose up`): **3000** + **8080**.

**Portal + Backstage** (`docker compose --profile backstage up`): **3000**, **8080**, **3001**, **7007**. Open **3001** for Backstage; the UI embeds Relay chat from **3000** and calls the Relay API on **8080** where configured.

Host **`make backstage-dev`** uses the same **3001** / **7007** ports without running the Backstage container.

## One-time setup

```bash
cp .env.example .env   # optional overrides; Make `bootstrap` does this too
```

## Portal only (chat + API)

Same stack as `make up`:

```bash
docker compose up --build -d
```

See [Local ports](#local-ports-docker-compose) — host **3000** (web) and **8080** (API).

| URL | Service |
| --- | --- |
| http://localhost:3000 | Web chat UI |
| http://localhost:8080 | Relay API (`/health`) |

Stop:

```bash
docker compose down
```

## Portal + Backstage (one command)

Adds **Backstage** on host **3001** (frontend) and **7007** (backend). The dev server binds **`0.0.0.0:3001`** inside the container so the published port works from macOS/Linux hosts. First start runs `yarn install` inside the container and can take several minutes.

**Pick one:**

```bash
docker compose --profile backstage up --build -d
make up-backstage    # same
make up-all          # alias for up-backstage
```

Or enable the profile by default via `.env` (Compose reads `COMPOSE_PROFILES` automatically):

```bash
# In .env (see .env.example)
COMPOSE_PROFILES=backstage

docker compose up --build -d   # portal + Backstage
```

| URL | Service |
| --- | --- |
| http://localhost:3001 | Backstage UI (start here) |
| http://localhost:7007 | Backstage backend API |
| http://localhost:3000 | Relay chat (embedded in Backstage **Relay Assistant**) |
| http://localhost:8080 | Relay API (Backstage **Observability** / platform-services) |

Requirements:

- **Docker Desktop** (or engine + Compose v2) with enough disk for `node:22` and Yarn cache.
- **Docker socket** mounted for the Backstage service so TechDocs can use `generator.runIn: docker` (local only).
- The Backstage service uses a **named Docker volume** for `apps/backstage/node_modules` so Linux native packages (Rspack) are not taken from a macOS host install.
- Optional **`GITHUB_TOKEN`** in `.env` for real GitHub API / Scaffolder dispatch. Compose sets a **placeholder** when unset so Backstage can start (catalog + Relay embed still work).

Stop everything:

```bash
docker compose --profile backstage down
```

## Make equivalents

| Goal | Compose | Make |
| --- | --- | --- |
| Portal stack | `docker compose up --build -d` | `make up` |
| Portal + Backstage | `docker compose --profile backstage up --build -d` | `make up-backstage` or `make up-all` |
| Portal + Backstage (via `.env`) | `COMPOSE_PROFILES=backstage` then `docker compose up --build -d` | — |
| Stop | `docker compose down` | `make down` |
| Stop (with Backstage) | `docker compose --profile backstage down` | `make down-backstage` |
| Ingest | `docker compose exec relay-assistant python -m rag_ingestion.cli ingest` | `make ingest` |
| Host CI tests | — | `make ci` |
| Backstage on host (hot reload) | — | `make backstage-install && make backstage-dev` |

Host **Backstage dev** (`make backstage-dev`) is still the best loop for UI/plugin work; the Compose profile is for an all-container demo without local Node/Yarn.

## Explicit file path

If you prefer not to use root [`compose.yaml`](../compose.yaml):

```bash
docker compose -f deploy/docker-compose.yml up --build -d
docker compose -f deploy/docker-compose.yml --profile backstage up --build -d
```

## Overrides

Custom knowledge mounts: copy [`deploy/docker-compose.override.example.yml`](../deploy/docker-compose.override.example.yml) to `deploy/docker-compose.override.yml`. Compose merges overrides automatically when the project includes `deploy/docker-compose.yml`.

## Troubleshooting

**Backstage on :3001 unreachable but :3000 works**

Check `docker compose --profile backstage ps`. If `backstage` is `Exited`, read logs:

```bash
docker compose --profile backstage logs backstage --tail 80
```

`Cannot find module './rspack.linux-…'` means the container used **host** `node_modules` (wrong OS). Recreate with the named volume (current compose file):

```bash
docker compose --profile backstage down
docker compose --profile backstage up --build -d
docker compose --profile backstage logs -f backstage   # wait for “webpack compiled”
```

First Backstage start runs `yarn install` inside the container and can take several minutes before :3001 responds.
