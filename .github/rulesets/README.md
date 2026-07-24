# Repository rulesets

Version-controlled definition of the **main branch** ruleset for
`opsdevcode/relay` (aligned with [opsdevcode/repave](https://github.com/opsdevcode/repave)).

## Apply

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
