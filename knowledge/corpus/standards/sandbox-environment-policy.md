# Sandbox Environment Policy

Sandbox clusters exist for learning, integration testing, and demos. They are not miniature production environments and carry lighter controls by design.

## Intended use

Allowed:

- Trying golden-path deploys and GitOps flows
- Partner demos with synthetic data only
- Short-lived experiments under seven days
- Automated CI smoke tests after merge

Not allowed:

- Production or regulated personal data
- Open inbound access from the public internet without approval
- Cryptocurrency mining, port scanning, or security research without coordination
- Long-running stateful stores without backup acknowledgment

## Data handling

All sandbox data must be generated or anonymized. If you import a dataset, attach a data classification label of `public` or `internal-synthetic` only. DLP scans run weekly; violations trigger namespace suspension.

## Resource limits

| Resource | Default quota | Extension |
| --- | --- | --- |
| CPU | 20 cores per namespace | Ticket + manager |
| Memory | 64 GiB | Ticket + manager |
| Persistent volume | 100 GiB | Auto-delete after 14 days |
| Load balancer | 2 | Architecture review |

Idle namespaces without deploy activity for 30 days are archived and recreated on request.

## Network

Egress to the internet is allowed for package pulls and documented SaaS APIs on the allow list. Ingress URLs use shared DNS under `*.sandbox.internal`. Do not point customer DNS at sandbox endpoints.

## Identity and access

Every engineer receives sandbox admin within their team namespace only. Cross-team access requires temporary RBAC grants logged in the access portal.

## Cleanup expectations

Tag resources with `expires-on` labels when creating demos. The reaper job deletes expired workloads nightly. Teams own communication if a shared demo must persist longer.

## Escalation to staging

Promote workloads that need realistic load tests or partner UAT to staging; do not relax sandbox policy to mimic production compliance controls.
