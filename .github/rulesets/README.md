# Repository rulesets

Version-controlled definition of the **main branch** ruleset for
`opsdevcode/relay` (aligned with [opsdevcode/repave](https://github.com/opsdevcode/repave)).

**Review policy:** `required_approving_review_count: 1` for everyone except bypass actors.
The bypass list includes maintainer `@erskaggs` (`bypass_mode: pull_request`) so owner PRs
do not need a review; external contributors still need one approval. CI remains required.

After changing `main-branch.json`, apply on GitHub (admin on the repo). If classic branch
protection is also enabled, remove it so the ruleset is the single source of truth:

```bash
gh api --method DELETE repos/opsdevcode/relay/branches/main/protection
```

Requires admin on the repository:

```bash
gh api --method POST repos/opsdevcode/relay/rulesets \
  --input .github/rulesets/main-branch.json
```

If a ruleset named `main branch` already exists, update it:

```bash
RULESET_ID="$(gh ruleset list --repo opsdevcode/relay --json id,name \
  -q '.[] | select(.name=="main branch") | .id')"
gh api --method PUT "repos/opsdevcode/relay/rulesets/${RULESET_ID}" \
  --input .github/rulesets/main-branch.json
```

Inspect:

```bash
gh ruleset check main --repo opsdevcode/relay
```

Docs-only pull requests rely on workflows that **always run** but skip heavy work via
`.github/actions/ci-paths/` so required checks still report success.
