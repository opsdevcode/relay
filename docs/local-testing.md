# Local testing

Local testing is a **first-class deliverable** for this repository. Anyone cloning the repo should be able to validate behavior on a laptop **without cloud accounts, API keys, or production services**.

**Quick gate**

```bash
make install     # pip install -e apps/relay-assistant[dev]
make ci          # quality + security + unit tests (matches CI jobs on host)
make up          # start stack (no keys)
make verify      # unit tests in container + HTTP smoke
```

See also: [local-setup.md](local-setup.md) · [roadmap.md](roadmap.md) · [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Why local testing matters

| Audience | What they need |
| --- | --- |
| **Contributors** | Fast feedback before opening a PR |
| **Reviewers** | Reproducible checks, not “works on my machine” |
| **Demos** | Proof the portal runs with zero secrets |
| **Platform teams** | Contract tests for draft-and-route and RAG before pilot envs exist |

Production pilots add identity, managed databases, and observability backends. **Local testing must stay runnable without those dependencies.**

---

## Test layers

```mermaid
flowchart TB
  L1["Layer 1 — Host gate (`make ci`)"]
  L2["Layer 2 — Unit only (`make test-local`)"]
  L3["Layer 3 — Container unit (`make test-docker`)"]
  L4["Layer 4 — Smoke (`make smoke`)"]
  L5["Layer 5 — Stack gate (`make verify`)"]

  L1 --> L2
  L2 --> L3
  L3 --> L4
  L4 --> L5
```

### Layer 1 — Host CI gate (no Docker)

Runs the same checks as GitHub Actions quality, security, and test jobs:

```bash
make ci    # make quality && make security && make test-local
```

Includes Ruff, mypy, Bandit, pip-audit, and pytest.

### Layer 2 — Unit tests only

```bash
make test-local
```

**Requirements:** Python 3.11+ (3.12 recommended), `make install` or `pip install -e "./apps/relay-assistant[dev]"`.

**No API keys.** No Postgres. No Redis.

### Layer 3 — Unit tests in container

```bash
make up
make test-docker
```

### Layer 4 — Smoke (HTTP end-to-end)

`scripts/smoke-local.sh` exercises the running stack on `http://localhost:8080`:

| Step | Validates |
| --- | --- |
| `GET /health` | OK status, `api_keys_required: false`, documents indexed |
| `POST /chat` | Extractive Q&A over bundled corpus |
| `GET /platform-services` | Registry loaded |
| `POST /actions/confirm` | Scaffold confirm with **chat-shaped draft** (`inputs.service_name`) |

```bash
make up    # wait until healthy
make smoke
```

Override API base: `API=http://127.0.0.1:8080 make smoke`.

### Layer 5 — Verify (pre-push)

```bash
make up
make verify    # `make test-docker` then `make smoke`
```

Use **`make verify`** before pushing changes that touch the assistant, ingestion, or smoke script.

---

## CI parity

| Local | GitHub Actions |
| --- | --- |
| `make test-local` | `ci.yml` → job **test** |
| `make quality` | `python-quality-security.yml` → **Code quality (Ruff + mypy)** |
| `make security` | `python-quality-security.yml` → **Security (Bandit + pip-audit)** |
| PR title + commits | `conventional-commits.yml` → **semantic-pull-request**, **commitlint** |
| `make ci` | All of the above on the host (before opening a PR) |

Docs-only PRs skip heavy steps via `.github/actions/ci-paths/` but checks still report success (required for rulesets). See [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Adding tests with new behavior

Every change to portal behavior should extend local testing in the same PR:

| Change type | Required testing |
| --- | --- |
| New tool or draft shape | Unit test for draft + confirm; extend smoke if HTTP-facing |
| RAG / ingest | Unit test for chunking/search helpers; smoke if default answers change |
| Registry entry | Test that registry loads (smoke already checks one ID) |
| Web UI only | Manual check in browser; prefer a small JS test or smoke note in PR |

**Scaffold example:** `test_confirm_scaffold_draft_uses_chat_draft_shape` ensures confirm reads `inputs.service_name` from drafts returned by `/chat` — the same JSON the web UI posts on Confirm.

---

## Troubleshooting

**`make ci` — No module named pytest**

```bash
pip install -e "./apps/relay-assistant[dev]"
```

**`make test` — service not running**

```bash
make up
docker compose -f deploy/docker-compose.yml ps
```

**`make smoke` — API unreachable**

- Confirm port 8080 is free and `relay-assistant` container is healthy.
- `docker compose -f deploy/docker-compose.yml logs relay-assistant`

**`make smoke` — documents: 0**

- Wait a few seconds after startup for auto-ingest, or run `make ingest`.

**Fresh database**

```bash
make down
docker volume rm deploy_postgres_data 2>/dev/null || true
make up
make smoke
```

---

## Acceptance criteria (local testing deliverable)

We treat local testing as **done for a release** when all of the following hold:

- [ ] `make ci` passes on a clean clone with only Python 3.12 + pip install (documented in README).
- [ ] `make smoke` passes after `make up` with no `.env` API keys.
- [ ] `make ci` passes locally before every PR.
- [ ] CI workflows `test`, quality, security, commitlint, and semantic PR checks pass on `main`.
- [ ] [roadmap.md](roadmap.md) Phase 0 items for testing (0.6, 0.7) stay green or are superseded by stricter gates.
- [ ] New features ship with tests per the table above.

---

## Related Makefile targets

| Target | Purpose |
| --- | --- |
| `make bootstrap` | Create `.env` from example if missing |
| `make up` / `make down` | Start/stop compose stack |
| `make ingest` | Re-index knowledge corpus |
| `make install` | Install dev dependencies (`apps/relay-assistant[dev]`) |
| `make ci` | Quality + security + unit tests (host) |
| `make test-local` | Pytest only (host) |
| `make test-docker` | Pytest inside container |
| `make quality` | Ruff + mypy |
| `make security` | Bandit + pip-audit |
| `make smoke` | HTTP smoke tests |
| `make verify` | Container unit + smoke |
