# Relay usage

## Purpose

The platform assistant answers questions about internal standards, deploy steps, and troubleshooting using the curated knowledge corpus. It is a guide, not an authority that bypasses change control.

## Good questions

- “What are the required tags for a new sandbox namespace?”
- “Walk through promoting a service from staging to production.”
- “Which alerts should I wire for a tier-2 API SLO?”
- “Summarize the secrets rotation policy for C2 credentials.”

Provide context: environment, team name, and service type. The assistant grounds answers in indexed docs and standards.

## Questions to avoid

- Pasting production secrets, tokens, or customer data
- Asking for one-click production changes without a pull request
- Requesting exceptions to security policy without linking an approved ticket

The assistant must refuse or redact when sensitive patterns appear.

## Verification habit

Treat every answer as a draft:

1. Check cited document titles against the latest version in the portal.
2. Run suggested CLI commands first in sandbox.
3. Confirm breaking changes with code owners if the answer touches shared libraries.

If the assistant contradicts written policy, policy wins—file a corpus correction ticket.

## Improving answers

When content is missing or stale:

- Propose edits via pull request to the knowledge corpus
- Tag `platform-docs` for review
- Note the gap you hit so the next indexer run includes it

## Integration points

IDE plugins and chat widgets use the same backend. Session history may be retained 30 days for quality review; do not include regulated data in prompts.

## Limitations

The assistant does not have live cluster state. For “what is running now,” use observability tools and GitOps sync status. It cannot approve access or merge pull requests on your behalf.

## Training recommendation

New hires complete the 30-minute lab: ask three onboarding questions, deploy to sandbox using assistant hints, then validate steps against the official onboarding doc.
