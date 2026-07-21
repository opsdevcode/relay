# GitOps PR Workflow

Production changes ship exclusively through pull requests with risk-tiered review.

## Risk tiers

| Tier | Examples | Review |
| --- | --- | --- |
| L0 | Docs, non-prod config | Peer |
| L1 | Module version bump | Team lead |
| L2 | Prod infra change | Eng + SRE |
| L3 | Security-sensitive | Eng + SRE + Security |

## Branch naming

Use prefixes: `feat/`, `fix/`, `chore/`, `platform/`.

## Merge requirements

- CI must pass (fmt, validate, lint, plan, scan)
- Required CODEOWNERS approvals for the tier
- No standing prod write — pipeline applies after merge
