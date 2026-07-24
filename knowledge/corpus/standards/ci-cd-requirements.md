# CI/CD Pipeline Requirements

All application and infrastructure repositories connected to the platform must implement the minimum pipeline stages below. Forks and personal experiments are exempt until they request deployment credentials.

## Required stages

| Stage | Purpose | Blocking |
| --- | --- | --- |
| Lint / format | Consistent style and static checks | Yes |
| Unit test | Fast feedback on logic | Yes |
| Build | Reproducible artifact | Yes |
| SCA / license scan | Known vulnerabilities | Yes on high/critical |
| Container scan | Image CVE policy | Yes on fixable critical |
| IaC validate | Schema and policy for infra | Yes |
| Deploy to dev | Smoke test target | Yes for default branch |

Promotion to staging and production uses separate workflows triggered by tags or approved environment gates.

## Branch protections

- Default branch requires pull request and at least one peer review
- Force push and direct commits disabled for protected branches
- Required status checks must match the stage names registered in the platform catalog
- Signed commits encouraged; mandatory for infrastructure repos

## Secrets in CI

- Never store long-lived cloud keys in repository secrets
- Use OIDC federation from the CI provider to short-lived roles
- Third-party API keys live in the centralized secrets store with rotation dates
- Pull requests from forks do not receive access to org secrets

## Artifact immutability

Images and Helm charts published to production registries must be content-addressed or semver-tagged once. Overwriting tags is blocked. Roll back by deploying a previous digest, not by repushing.

## Pipeline performance

Target p95 pipeline duration under 15 minutes for application repos. Split slow integration tests into nightly or post-merge workflows with clear ownership.

## Exceptions

Teams may skip container scan only for non-deployable libraries if they publish SBOMs instead. Document exceptions in `platform-exceptions.yaml` with expiry dates.

## Compliance evidence

Pipeline definitions and run history are retained for audit. Do not disable logging on production deploy jobs.
