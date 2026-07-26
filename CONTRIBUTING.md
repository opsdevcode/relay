# Contributing to Relay

Thanks for your interest in this working model. The goal is a **local-first**, **zero-key** demo of a conversational IDP that grows into a pilot-ready product — see [`docs/roadmap.md`](docs/roadmap.md).

## Ground rules

- **Draft-and-route only.** Do not add paths that mutate production (or GitHub) without human confirmation.
- **No secrets in the repo.** Use gitignored `.env` locally; never commit API keys or PATs.
- **Local testing is mandatory.** Every new feature or fix ships in the **same PR** with:
  - **Unit tests** — pytest (`make ci`) and/or Backstage Jest (`make backstage-test`)
  - **E2E updates** — extend [`scripts/smoke-local.sh`](scripts/smoke-local.sh) for Relay API
    behavior and/or [`apps/backstage/packages/app/e2e-tests/`](apps/backstage/packages/app/e2e-tests/)
    for Backstage UI flows
  - Do not merge `feat:` / `fix:` work and plan tests as follow-up. See
    [`docs/tdd.md`](docs/tdd.md) and [`docs/local-testing.md`](docs/local-testing.md).
- **Pin Actions to SHAs.** Third-party actions in workflows must use full commit SHAs (see existing workflows).
- **Keep the roadmap in sync.** When a PR completes a roadmap item (e.g. **1D.2**), update
  [`docs/roadmap.md`](docs/roadmap.md) in the **same PR**: mark the workstream **done**, refresh
  **Quick reference — what to build next**, and adjust **Current state** if the baseline table is
  stale. See **How this doc stays current** in the roadmap.

## Development

From repo root (Python 3.12 recommended):

```bash
make install      # pip install -e apps/relay-assistant[dev]
make up           # Docker stack — no API keys required
make ci             # ruff + mypy + bandit + pip-audit + pytest (host)
make smoke          # HTTP smoke / API e2e (requires make up)
make backstage-e2e  # Backstage Playwright (starts app on :3001 if needed)
```

Or only unit tests:

```bash
make test-local
```

Quality and security (same as CI):

```bash
make quality
make security
```

### Python quality and security tooling

CI runs these on every push and pull request (aligned with [opsdevcode/repave](https://github.com/opsdevcode/repave)):

| Workflow | Job / check name |
| --- | --- |
| `ci.yml` | `test` |
| `python-quality-security.yml` | `Code quality (Ruff + mypy)`, `Security (Bandit + pip-audit)` |
| `conventional-commits.yml` | `commitlint`, `semantic-pull-request` |

**Docs-only** changes still trigger workflows so required checks complete, but jobs **skip heavy work** when the diff touches only:

- `docs/**`
- `**/*.md`
- `LICENSE`
- `.github/pull_request_template.md`

Detection lives in `.github/actions/ci-paths/`. Mixed PRs (for example `docs/` plus `apps/relay-assistant/`) run the full gate.

Configuration: `apps/relay-assistant/pyproject.toml`.

| Tool | Purpose |
| --- | --- |
| [Ruff](https://docs.astral.sh/ruff/) | Lint + format |
| [mypy](https://mypy-lang.org/) | Static types |
| [Bandit](https://bandit.readthedocs.io/) | Python SAST |
| [pip-audit](https://pypi.org/project/pip-audit/) | Dependency vulnerabilities (OSV) |

### Branch ruleset (`main`)

Repository ruleset **main branch** (see `.github/rulesets/main-branch.json`) requires on `main`:

- Changes merged via **pull request**
- **One approving review** for PRs from contributors (you cannot approve your own PR)
- **Maintainer bypass:** `@erskaggs` is in the ruleset bypass list for pull-request rules only — CI checks still required; you can merge your own PRs without a review
- Status checks: `test`, `Code quality (Ruff + mypy)`, `Security (Bandit + pip-audit)`, `commitlint`, `semantic-pull-request`
- No force-push (`non_fast_forward`)

Apply or update after editing the JSON:

```bash
gh api --method POST repos/opsdevcode/relay/rulesets \
  --input .github/rulesets/main-branch.json
```

To update an existing ruleset:

```bash
RULESET_ID="$(gh ruleset list --repo opsdevcode/relay --json id,name \
  -q '.[] | select(.name=="main branch") | .id')"
gh api --method PUT "repos/opsdevcode/relay/rulesets/${RULESET_ID}" \
  --input .github/rulesets/main-branch.json
```

Classic branch protection may still restrict who can push; the ruleset adds required checks and PR rules. See [`docs/security-governance.md`](docs/security-governance.md).

## Commit messages (Conventional Commits)

Format:

```text
<type>[optional scope]: <description>
```

Common types: `feat`, `fix`, `docs`, `ci`, `chore`, `refactor`, `test`.

Examples:

```text
feat(portal): add registry-driven tool dispatch
fix(scaffold): read service_name from draft inputs
docs: expand local testing guide
```

**PR titles** are validated the same way (for example `ci: align workflows with repave`).

## Releases (semver)

Versioning and GitHub releases are automated from
[Conventional Commits](https://www.conventionalcommits.org/) on `main` using
[python-semantic-release](https://python-semantic-release.readthedocs.io/) for the
`relay-assistant` package (`apps/relay-assistant/`).

| Commit type | Semver bump |
| --- | --- |
| `fix:` | Patch |
| `feat:` | Minor |
| `feat!:` / `fix!:` / `BREAKING CHANGE:` | Major |
| `docs:`, `chore:`, `ci:`, `refactor:`, `test:` | None (unless breaking) |

Flow:

1. Merge a PR to `main` with a conventional title (`feat:`, `fix:`, etc.).
2. CI runs; the **Release** workflow (non-docs-only paths) runs tests, bumps version,
   opens a **`chore/release/*` PR**, admin-merges it to `main`, tags `vX.Y.Z`, and publishes
   a GitHub Release with wheel/sdist artifacts.
3. No separate release PR is required.

The **Release** workflow does not run when a push to `main` only touches docs-only paths
(see `release.yml` `paths-ignore`).

Changelog: [`apps/relay-assistant/CHANGELOG.md`](apps/relay-assistant/CHANGELOG.md).

## Maintainer setup

`main` is protected; release commits must land via PR. The release workflow uses
repository secret **`RELAY_RELEASE_TOKEN`**: a fine-grained or classic PAT owned by a
maintainer with **`contents: write`** and permission to **bypass branch protections**
(admin merge), same pattern as repave’s `REPAVE_RELEASE_TOKEN`.

```bash
gh secret set RELAY_RELEASE_TOKEN --repo opsdevcode/relay
```

Org scope (optional):

```bash
gh secret set RELAY_RELEASE_TOKEN --org opsdevcode --visibility private
```

### Releases not showing up?

1. **Secret missing** — The Release job fails immediately if `RELAY_RELEASE_TOKEN` is unset.
   Check: `gh secret list --repo opsdevcode/relay` (name must appear).
   Use the same PAT pattern as repave’s `REPAVE_RELEASE_TOKEN` if you already have one.
2. **Re-run after adding the secret** — Merges do not retry automatically:

```bash
gh workflow run Release --repo opsdevcode/relay --ref main
```

3. **Commit type** — Only `feat` / `fix` / breaking commits since the last tag produce a bump.
   The PR #1 squash title was `ci:` (no release). PR #2 was `feat:` (should release **v0.2.0** once the workflow succeeds).
4. **GH013 push rejected** — If Release fails with “Changes must be made through a pull request”,
   the workflow could not admin-merge the automated `chore/release/*` PR. Use an administrator PAT
   for `RELAY_RELEASE_TOKEN`, or re-run Release after updating `.github/workflows/release.yml`.

## Pull requests

- Use the [pull request template](.github/pull_request_template.md).
- Keep changes focused; follow **TDD** ([docs/tdd.md](docs/tdd.md)): unit tests + E2E updates in the same PR.
- Run `make ci` before opening; run `make smoke` when touching Relay API/ingest/chat; run
  `make backstage-e2e` when touching Backstage catalog or UI.
- Head branches are deleted automatically when a PR merges (`pr-branch-cleanup.yml`).

## Reporting issues

Use GitHub issues. For security-sensitive reports, see [SECURITY.md](SECURITY.md).
