# Demo script (≈5 minutes)

Present the **AI Developer Portal** working model with **no API keys**. Audience: platform leadership or design partners.

## Before you start

```bash
git clone git@github.com:opsdevcode/ai-developer-portal.git
cd ai-developer-portal
make up
make smoke   # optional confidence check
open http://localhost:3000
```

Footer should show document count **≥ 15** and mode **extractive (no API keys)**.

---

## 1 · Local-first story (30 sec)

- Emphasize: **zero secrets** for the demo — extractive RAG over bundled corpus.
- Point at suggested prompt chips and `/health` version in the footer (after releases are enabled).

---

## 2 · Grounded Q&A (1 min)

**Prompt:** `What are the required resource tags?`

- Show **bold** excerpt and **Sources** list with paths under `/knowledge/standards/`.
- Optional follow-up: `What does our CI/CD pipeline require?` (hits `standards/ci-cd-requirements.md`).

---

## 3 · Platform services (45 sec)

**Prompt:** `What platform services are available?`

- Registry-backed list: knowledge, golden-path scaffold, sandbox, observability (mock read).

---

## 4 · Draft-and-route scaffold (1.5 min)

**Prompt:** `Create a new service called payments-api`

- Assistant returns a **draft** — call out human-in-the-loop.
- Click **Confirm** → **Run workflow** link (no PAT in the portal).
- Mention committed example: `examples/services/demo-api/` from the same golden-path template.

---

## 5 · Sandbox handoff (45 sec)

**Prompt:** `I need a sandbox for a POC`

- Confirm → GitHub issue template link (production would be ticket system).

---

## 6 · Close (30 sec)

- Roadmap: Backstage embed, hybrid RAG, real observability read ([docs/roadmap.md](roadmap.md)).
- Local testing: `make ci` / `make smoke` ([local-testing.md](local-testing.md)).
- Releases: semver tags on `feat`/`fix` merges via Conventional Commits ([CONTRIBUTING.md](../CONTRIBUTING.md)).

---

## Troubleshooting live

| Issue | Fix |
| --- | --- |
| API unreachable | `make up` · check port 8080 |
| Documents: 0 | wait for startup ingest or `make ingest` |
| Smoke fails on scaffold | ensure latest `main` (confirm reads `inputs.service_name`) |
