# Developer Onboarding

Welcome to the internal developer platform. This guide gets you from zero access to a deployed service in a sandbox cluster within your first week.

## Day zero checklist

| Step | Owner | Outcome |
| --- | --- | --- |
| Identity | IT | SSO group membership for `developers` |
| Source control | Platform | Org invite and team repo access |
| Secrets | Security | Vault namespace and break-glass training |
| Cluster | Platform | `kubectl` context for dev and sandbox |

Complete identity and SSO before requesting cluster credentials. Automated provisioning runs nightly; urgent access uses the `#platform-requests` channel with manager approval.

## Local toolchain

Install the supported versions pinned in the platform CLI bundle:

- `platform-cli` (auth, env, deploy helpers)
- `kubectl` matching the cluster minor version
- Container runtime compatible with our base images
- `terraform` only if you own infrastructure modules

Run `platform-cli doctor` after install. All checks must pass before your first deploy.

## First service deploy

1. Clone the golden-path starter from the internal template catalog.
2. Copy `values-sandbox.yaml` and set `team`, `service`, and `cost-center` labels.
3. Open a pull request; CI runs unit tests, image build, and policy scans.
4. Merge to `main`; GitOps syncs to the sandbox namespace within five minutes.
5. Hit the generated preview URL and confirm health endpoints return `200`.

## Learning path

- Week 1: Sandbox deploy and observability dashboards for your service.
- Week 2: Staging promotion workflow and SLO draft for one user journey.
- Week 3: On-call shadow for your team’s tier-2 rotation (optional for app devs).

## Support channels

| Channel | Use for |
| --- | --- |
| `#platform-help` | How-to, broken pipelines, access |
| `#incidents` | Production impact only |
| Office hours | Architecture and golden-path exceptions |

Document exceptions in your team runbook; do not bypass merge gates for convenience.

## Related material

After onboarding, read the golden-path Kubernetes guide and the pull-request workflow standard before requesting production access.
