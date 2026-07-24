# Secrets Management Standard

Secrets include passwords, API tokens, private keys, connection strings, and signing material. Plaintext secrets must not appear in source control, tickets, chat, or build logs.

## Classification

| Class | Examples | Storage | Rotation |
| --- | --- | --- | --- |
| C1 | TLS keys, encryption KMS | HSM-backed vault | 90 days |
| C2 | Database credentials | Dynamic secrets engine | On lease expiry |
| C3 | Third-party API keys | Team vault path | 180 days |
| C4 | Shared dev placeholders | Sealed dev vault | Annual |

Higher classes require tighter access reviews and MFA for human retrieval.

## Developer workflow

1. Request a vault path through the access portal; manager approves.
2. Inject secrets at runtime via the cluster secret store operator—no env files in images.
3. Local development uses personal short-lived tokens from `platform-cli secrets login`.
4. Rotate by writing new versions; applications must support dual-read during cutover.

## CI and GitOps

Pipelines authenticate with workload identity. Git repositories contain references (paths, keys) never values. Sealed secrets or external secrets CRDs sync from vault to namespaces.

Scanning tools run on every push. Leaked secrets trigger automatic revocation playbooks for supported providers.

## Logging and debugging

Structured logs must redact known secret patterns. Support engineers use break-glass vault roles with session recording for production debugging.

Never paste secrets into incident channels; use one-time secure links with expiry.

## Key ceremony

Asymmetric keys for signing artifacts follow dual-control generation. Public keys publish to the trust store; private keys never leave vault export policies.

## Violations

Confirmed leaks require:

- Immediate rotation
- Incident ticket with timeline
- Root-cause fix (pre-commit hook, training, or pipeline change)

Repeated violations escalate to security review of team practices.

## Audit

Quarterly access recertification for vault paths tied to production. Unused paths are disabled automatically after 60 days without read activity.
