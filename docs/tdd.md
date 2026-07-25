# Test-driven development (TDD)

Relay uses **test-driven development** for product behavior: define expected
outcomes in tests first, implement until green, then refactor. Every feature or
fix ships **unit tests and E2E updates in the same PR** — see
[local-testing.md](local-testing.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Red → green → refactor

| Step | What you do | Relay commands |
| --- | --- | --- |
| **Red** | Add or extend a test that fails for the right reason | `make test-local` or targeted `pytest apps/relay-assistant/tests/test_foo.py -k ...` |
| **Green** | Minimal code change to pass | Re-run tests; then `make ci` |
| **Refactor** | Clean up without changing behavior | `make ci`; `make format` as needed |
| **E2E** | Assert user-visible / HTTP contracts | `make up && make smoke`; `make backstage-e2e` when Backstage changes |

Do **not** merge with tests planned for a follow-up PR.

---

## Where tests live (by surface)

| Surface | Unit / contract (fast, `make ci`) | E2E (stack or browser) |
| --- | --- | --- |
| **Python assistant** (RAG, tools, API) | `apps/relay-assistant/tests/test_*.py` | `scripts/smoke-local.sh` via `make smoke` |
| **Ingest / corpus** | `test_ingest.py`, `test_frontmatter.py`, … | Smoke chat + citations; `make ingest-full` after corpus edits |
| **Platform registry** | `test_registry.py` | Smoke `GET /platform-services` |
| **Catalog seed** | `test_catalog_entities.py`, `test_backstage_config.py` | Backstage Playwright under `apps/backstage/packages/app/e2e-tests/` |
| **Backstage UI** | `App.test.tsx` (`make backstage-test`) | `make backstage-e2e` (Playwright; starts app on **:3001** locally) |

**Rule of thumb:** if a reviewer or user can hit it over HTTP or in the browser,
extend **smoke or Playwright** in the same PR as pytest/Jest.

---

## TDD workflow by change type

### New API route or HTTP behavior

1. **Red** — pytest with `FastAPI` + `TestClient` (see `test_ingest.py` reindex
   webhook tests) **or** add a step to `scripts/smoke-local.sh`.
2. **Green** — implement route in `portal_assistant/main.py` (or module).
3. **E2E** — smoke step must pass with `make up && make smoke`.

### Pure logic (chunking, frontmatter, registry validation)

1. **Red** — test in `tests/test_<module>.py` with fixtures under `tmp_path`; no
   Docker.
2. **Green** — implement in `src/portal_assistant/` or `src/rag_ingestion/`.
3. **E2E** — only if default demo answers or smoke prompts change.

### New platform tool or draft shape

1. **Red** — unit test for draft JSON + `confirm_*` (see `test_scaffold.py`).
2. **Green** — `tools.py`, registry entry, optional graph guard.
3. **E2E** — extend smoke if confirm or chat contract changes.

### Backstage catalog / config

1. **Red** — `test_catalog_entities.py` / `test_backstage_config.py`.
2. **Green** — `catalog/entities/`, `app-config.yaml`.
3. **E2E** — Playwright in `e2e-tests/` (e.g. seed entities visible); run
   `make backstage-e2e`.

### Bug fix

1. **Red** — regression test that **failed before** the fix (same PR).
2. **Green** — fix.
3. **E2E** — update smoke/Playwright if the bug was only visible end-to-end.

---

## Suggested order inside a feature branch

```text
1. pytest (and/or Jest) for core behavior     ← TDD red/green loop
2. make ci                                    ← quality + security + all unit tests
3. Update scripts/smoke-local.sh and/or e2e-tests/*.ts
4. make up && make verify                     ← container unit + smoke (before push)
5. make backstage-e2e                         ← when apps/backstage/** or catalog UX changes
```

Docs-only changes skip code tests unless behavior docs claim new commands.

---

## Examples in this repo

| Feature | Unit (red first) | E2E |
| --- | --- | --- |
| Scaffold confirm shape | `test_confirm_scaffold_draft_uses_chat_draft_shape` | Smoke `POST /actions/confirm` |
| Corpus pipeline / reindex | `test_ingest.py`, webhook tests | Smoke reindex **503** without secret |
| Frontmatter / chunk titles | `test_frontmatter.py`, ingest test | Smoke citations include `"title"` |
| Backstage 1C.1 | `test_catalog_entities.py` | `catalog-seed.test.ts` (Relay, CloudOpt) |

---

## PR checklist (TDD)

Before opening a PR:

- [ ] New/changed behavior has a **failing test added first** (or same commit series
      with clear red-then-green history).
- [ ] `make ci` passes.
- [ ] HTTP/API changes update **`scripts/smoke-local.sh`** when applicable.
- [ ] Backstage UX changes update **`e2e-tests/`** and you ran **`make backstage-e2e`**
      (or noted why not in the PR).
- [ ] Bug fixes include a **regression** test.

See [.github/pull_request_template.md](../.github/pull_request_template.md).
