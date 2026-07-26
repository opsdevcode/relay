# Local run with Docker Compose

Relay supports **Make** (recommended in the README) and **plain Docker Compose** from the repo root. Both use the same [`deploy/docker-compose.yml`](../deploy/docker-compose.yml) definition.

## One-time setup

```bash
cp .env.example .env   # optional overrides; Make `bootstrap` does this too
```

## Portal only (chat + API)

Same stack as `make up`:

```bash
docker compose up --build -d
```

| URL | Service |
| --- | --- |
| http://localhost:3000 | Web chat UI |
| http://localhost:8080 | Relay API (`/health`) |

Stop:

```bash
docker compose down
```

## Portal + Backstage (one command)

Adds **Backstage** on **:3001** (frontend) and **:7007** (backend). First start runs `yarn install` inside the container and can take several minutes.

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
| http://localhost:3001 | Backstage (catalog, Create, Relay Assistant, TechDocs) |
| http://localhost:7007 | Backstage backend API |

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
