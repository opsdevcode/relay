## Summary

<!-- What changed and why? Keep this focused on intent and impact. -->

## Change type

<!-- PR titles must follow Conventional Commits (validated in CI). -->

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `docs` — documentation only
- [ ] `refactor` — code change without behavior change
- [ ] `test` — tests only
- [ ] `build` / `ci` / `chore` — tooling, CI, or maintenance
- [ ] breaking change (`feat!` / `fix!` or `BREAKING CHANGE:` in body)

**Suggested PR title:**

```text
<type>[optional scope]: <description>
```

## Scope

- [ ] `apps/relay-assistant/`
- [ ] `apps/web/`
- [ ] `apps/backstage/`
- [ ] `deploy/` / K8s / compose
- [ ] `knowledge/` / RAG corpus
- [ ] `.github/` workflows
- [ ] `docs/` / repo metadata
- [ ] other: <!-- describe -->

## Test plan

- [ ] **TDD:** failing test(s) added before or with implementation ([docs/tdd.md](docs/tdd.md))
- [ ] `make ci` (unit tests — no Docker)
- [ ] `make quality` (ruff + mypy)
- [ ] `make security` (bandit + pip-audit)
- [ ] `make up && make smoke` when Relay API / ingest / chat behavior changed
- [ ] `make backstage-e2e` when Backstage UI or catalog UX changed (or explain why not)
- [ ] not run (explain why)

## Release impact

<!-- python-semantic-release publishes on merge to main for feat/fix/breaking commits. -->

- [ ] user-facing release note expected (`feat` / `fix` / breaking) → **semver minor/patch/major**
- [ ] no release bump expected (`docs`, `chore`, `ci`, etc.)

## Checklist

- [ ] PR title follows [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] Draft-and-route preserved (no direct prod mutation from chat)
- [ ] New behavior: **unit tests + E2E updates** per [docs/tdd.md](docs/tdd.md)
- [ ] Actions pinned to full SHAs (repo policy)
- [ ] Secrets/credentials are not committed or logged

## Related links

- 
