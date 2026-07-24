# Pull Request Workflow

Code changes reach shared environments only through reviewed pull requests. This standard applies to application, platform, and documentation repositories under org governance.

## Before you open

- Link the work item or incident ID in the description
- Keep diffs focused; split unrelated changes
- Run local lint and tests matching CI
- Update changelogs or user-facing docs when behavior changes

## Description template

Use the org template sections:

1. **Summary** — What and why in plain language
2. **Test plan** — Steps reviewers or QA can replay
3. **Risk** — Blast radius, rollback, feature flags
4. **Screenshots / logs** — For UI or pipeline changes

## Review expectations

| Change type | Reviewers | Notes |
| --- | --- | --- |
| Application feature | 1 peer + code owner | Product optional |
| Shared library | 2 peers | Semver impact called out |
| Infrastructure | Platform + SRE | Plan output attached |
| Security control | Security architect | Threat model link |

Reviewers leave actionable comments; authors respond or resolve with rationale. Stale approvals clear when new commits push after review.

## CI gates

All required checks must pass before merge. Re-run failed flaky tests once; open a reliability ticket if flakes persist. Do not merge with overridden checks except documented break-glass with post-merge fix within 24 hours.

## Merge strategy

Default branch uses squash merge with conventional commit title. Release branches may use merge commits to preserve hotfix history—follow release captain guidance.

## After merge

- Monitor deployment pipeline and error budgets for one hour on prod changes
- Announce breaking API changes in the developer newsletter
- Backport critical fixes using labeled cherry-pick PRs

## Documentation-only changes

Docs PRs still require one reviewer and spell-check CI. Standards and policy docs need owner team approval.

## Anti-patterns

- Giant Friday merges without on-call coverage
- Reviewing your own production infra change under a second account
- Bypassing PR via direct cluster edits (subject to audit and rollback)
