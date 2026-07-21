# Security governance

This repository is configured so **only [@erskaggs](https://github.com/erskaggs)** can change `main`, CI/CD workflows, and deployment manifests.

## GitHub settings (applied on the repo)

| Control | Setting |
| --- | --- |
| **Branch protection (`main`)** | Push restricted to `erskaggs` only; PRs require CODEOWNER review; no force-push or deletion; linear history; conversation resolution required |
| **CODEOWNERS** | All paths (especially `.github/workflows/`) owned by `erskaggs` |
| **Actions: allowed actions** | `local_only` — workflows in this repo only, no third-party reusable workflows |
| **Actions: SHA pinning** | Required — actions must use full commit SHAs |
| **Actions: `GITHUB_TOKEN`** | Default **read-only** at repo level; write scopes declared per workflow job |
| **Fork PR workflows** | Disabled where supported; fork PRs never receive repository secrets (GitHub default) |

## CI/CD constraints (in workflow files)

- **`workflow_dispatch`** scaffold workflow runs only when `github.actor == 'erskaggs'`
- Workflow jobs declare **minimum** `permissions` (`contents: write`, `pull-requests: write` only where needed)
- Third-party actions pinned to **full SHAs**, not floating tags

## What others can do

Public users may **fork** and **open issues/PRs**, but they **cannot**:

- Push to `main`
- Merge pull requests (no write access; CODEOWNER approval required)
- Run `workflow_dispatch` with write side-effects (no write access)
- Use org/repo Actions secrets (none are required for the working model)

## Maintainer checklist

- Do **not** add collaborators with write access unless you intend to share control
- Do **not** store personal API keys in the repo — use gitignored `.env` locally
- Review PRs from forks carefully before merging (workflows do not run from forks)
- Rotate keys if a fork PR ever looks suspicious

## Org-level recommendations (`opsdevcode`)

If you are org owner, also consider:

- Base permissions: **Read** for members
- Disable repository creation for members unless needed
- Require 2FA for all org members
- Enable secret scanning + push protection (if available on your plan)
