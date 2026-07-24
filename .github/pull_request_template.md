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

- [ ] `apps/portal-assistant/`
- [ ] `apps/web/`
- [ ] `deploy/` / K8s / compose
- [ ] `knowledge/` / RAG corpus
- [ ] `.github/` workflows
- [ ] `docs/` / repo metadata
- [ ] other: <!-- describe -->

## Test plan

- [ ] `make ci` (unit tests — no Docker)
- [ ] `make quality` (ruff + mypy)
- [ ] `make security` (bandit + pip-audit)
- [ ] `make up && make smoke` (stack + HTTP smoke)
- [ ] not run (explain why)

## Release impact

<!-- python-semantic-release publishes on merge to main for feat/fix/breaking commits. -->

- [ ] user-facing release note expected (`feat` / `fix` / breaking) → **semver minor/patch/major**
- [ ] no release bump expected (`docs`, `chore`, `ci`, etc.)

## Checklist

- [ ] PR title follows [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] Draft-and-route preserved (no direct prod mutation from chat)
- [ ] New behavior includes tests per [docs/local-testing.md](docs/local-testing.md)
- [ ] Actions pinned to full SHAs (repo policy)
- [ ] Secrets/credentials are not committed or logged

## Related links

- 
