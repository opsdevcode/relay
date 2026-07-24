# Contributing to AI Developer Portal

Thanks for your interest in this working model. The goal is a **local-first**, **zero-key** demo of a conversational IDP that grows into a pilot-ready product — see [`docs/roadmap.md`](docs/roadmap.md).

## Ground rules

- **Draft-and-route only.** Do not add paths that mutate production (or GitHub) without human confirmation.
- **No secrets in the repo.** Use gitignored `.env` locally; never commit API keys or PATs.
- **Local testing is mandatory.** New behavior ships with tests and must pass `make ci` (see [`docs/local-testing.md`](docs/local-testing.md)).
- **Pin Actions to SHAs.** Third-party actions in workflows must use full commit SHAs (see existing workflows).

## Development

From repo root (Python 3.12 recommended):

```bash
make install      # pip install -e apps/portal-assistant[dev]
make up           # Docker stack — no API keys required
make ci             # ruff + mypy + bandit + pip-audit + pytest (host)
make smoke          # HTTP smoke (requires make up)
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

Detection lives in `.github/actions/ci-paths/`. Mixed PRs (for example `docs/` plus `apps/portal-assistant/`) run the full gate.

Configuration: `apps/portal-assistant/pyproject.toml`.

| Tool | Purpose |
| --- | --- |
| [Ruff](https://docs.astral.sh/ruff/) | Lint + format |
| [mypy](https://mypy-lang.org/) | Static types |
| [Bandit](https://bandit.readthedocs.io/) | Python SAST |
| [pip-audit](https://pypi.org/project/pip-audit/) | Dependency vulnerabilities (OSV) |

### Branch ruleset (`main`)

Repository ruleset **main branch** (see `.github/rulesets/main-branch.json`) requires on `main`:

- Changes merged via **pull request** (zero approving reviews required — solo maintainer OK)
- Status checks: `test`, `Code quality (Ruff + mypy)`, `Security (Bandit + pip-audit)`, `commitlint`, `semantic-pull-request`
- No force-push (`non_fast_forward`)

Apply or update after editing the JSON:

```bash
gh api --method POST repos/opsdevcode/ai-developer-portal/rulesets \
  --input .github/rulesets/main-branch.json
```

To update an existing ruleset:

```bash
RULESET_ID="$(gh ruleset list --repo opsdevcode/ai-developer-portal --json id,name \
  -q '.[] | select(.name=="main branch") | .id')"
gh api --method PUT "repos/opsdevcode/ai-developer-portal/rulesets/${RULESET_ID}" \
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

## Pull requests

- Use the [pull request template](.github/pull_request_template.md).
- Keep changes focused; include tests for assistant/RAG/tool changes.
- Run `make ci` before opening; run `make smoke` when touching HTTP flows.
- Head branches are deleted automatically when a PR merges (`pr-branch-cleanup.yml`).

## Reporting issues

Use GitHub issues. For security-sensitive reports, see [SECURITY.md](SECURITY.md).
