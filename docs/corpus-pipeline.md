# Corpus pipeline

How Relay indexes markdown knowledge for RAG — local corpus, Git / doc-as-code
sources, and how to trigger a re-index.

See also: [local-setup.md](local-setup.md) · [local-testing.md](local-testing.md) ·
[roadmap.md](roadmap.md) (item **1B.2**)

---

## Default path (this repo)

1. Edit markdown under `knowledge/corpus/{docs,proposals,standards}/`.
2. Sources are declared in [`knowledge/sources.yaml`](../knowledge/sources.yaml).
3. On empty DB (first `make up`), the API runs startup ingest automatically.
4. After corpus changes with an existing DB, re-index:

```bash
make ingest          # upsert (keeps stale rows from deleted files)
make ingest-full     # delete all rows, then re-index
```

Compose mounts `knowledge/corpus` → `/knowledge` in the assistant container.
Chunk size / overlap live in `sources.yaml` under `chunk:`.

### Frontmatter (optional)

Markdown files may start with YAML frontmatter. Ingest strips it before chunking
and uses:

| Field | Purpose |
| --- | --- |
| `title` | Document title (default: filename stem) |
| `owner` | Stored on each chunk row (`doc_owner`) for future ABAC |
| `updated` | Stored as `doc_updated` (ISO date string recommended) |

Multi-chunk docs get section-aware titles when a chunk begins with a `##`
heading, e.g. `Resource Tagging Standard — Required tags`.

Example: see `knowledge/corpus/standards/resource-tagging.md`.

---

## Source types

### Filesystem (default)

```yaml
- name: corpus-standards
  path: /knowledge/standards   # absolute in container, or relative to KNOWLEDGE_PATH
  glob: "**/*.md"
  visibility: public
```

Use a compose override to mount an external tree (standards checkout, MkDocs
`site/`, etc.):

```bash
cp deploy/docker-compose.override.example.yml deploy/docker-compose.override.yml
# edit the host path, then:
make up && make ingest-full
```

### Git (standards repo / doc-as-code)

Add a `type: git` entry (see [`knowledge/sources.git.example.yaml`](../knowledge/sources.git.example.yaml)):

```yaml
- name: platform-standards
  type: git
  url: https://github.com/example-org/platform-standards.git
  ref: main                 # branch or tag (shallow clone)
  subdir: docs              # optional path inside the repo
  glob: "**/*.md"
  visibility: public
```

On ingest, Relay:

1. Shallow-clones (or fetches) into `INGEST_CHECKOUT_DIR` / `<name>`
   (default `$TMPDIR/relay-corpus-checkouts`).
2. Globs `subdir` (or repo root) for markdown.
3. Upserts chunks into Postgres (FTS + embeddings).

Doc-as-code: point `subdir` at the published markdown (or mount the build
output as a filesystem source instead).

Merge git sources with the bundled corpus by appending entries to
`knowledge/sources.yaml`, or point `--config` at a combined file in deploy.

```bash
docker compose -f deploy/docker-compose.yml exec relay-assistant \
  python -m rag_ingestion.cli --config /app/knowledge/sources.yaml ingest --full
```

---

## Re-index triggers

| Trigger | When to use |
| --- | --- |
| Startup | Empty index, or embedding backfill (`full` reindex) |
| `make ingest` / `make ingest-full` | Local corpus edits |
| `POST /internal/reindex` | Webhook / Cron / operator after a standards repo push |
| K8s CronJob (example) | Periodic refresh when Git sources change infrequently |

### Webhook

Set a shared secret (not committed):

```bash
# .env
INGEST_WEBHOOK_SECRET=replace-with-long-random
```

```bash
curl -sS -X POST http://localhost:8080/internal/reindex \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Secret: replace-with-long-random" \
  -d '{"full": true}'
```

- Without `INGEST_WEBHOOK_SECRET`, the endpoint returns **503**.
- Wrong secret → **401**.
- Body: optional `{"full": true}` to purge before indexing.

Wire GitHub **repository_dispatch** or a workflow `curl` against your non-prod
URL after merges to the standards repo (URL and secret live in the env / deploy
repo, not in this working model).

### CronJob example

See [`deploy/k8s/base/ingest-cronjob.example.yaml`](../deploy/k8s/base/ingest-cronjob.example.yaml).
Not included in the base kustomization (cluster still needs managed Postgres /
corpus mounts — Phase **3.4–3.5**). Same command as local:

`python -m rag_ingestion.cli ingest --full`

---

## Registry checklist

When adding a knowledge capability:

1. Add / update sources in `knowledge/sources.yaml` (or git example).
2. List source **names** under the service in
   `packages/platform-services/registry.yaml`.
3. Re-index (`make ingest-full` or webhook).
4. Add a Q&A eval / smoke prompt if the content is user-facing.

---

## Ops knobs

| Env | Default | Purpose |
| --- | --- | --- |
| `KNOWLEDGE_PATH` | `/knowledge` | Filesystem corpus root |
| `INGEST_CHECKOUT_DIR` | `$TMPDIR/relay-corpus-checkouts` | Git clone cache |
| `INGEST_WEBHOOK_SECRET` | _(empty)_ | Enables `POST /internal/reindex` |
| `HYBRID_SEARCH_ENABLED` | `true` | FTS + local embeddings |

`/health` reports `documents` and `retrieval_mode` (`hybrid` \| `fts`).
