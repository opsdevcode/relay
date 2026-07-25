---
title: Resource Tagging Standard
owner: platform-team
updated: 2026-01-15
---

# Resource Tagging Standard

All cloud resources must carry mandatory tags for cost, ownership, security, and operations.

## Required tags

| Tag | Description | Example |
| --- | --- | --- |
| `owner` | Team or individual accountable | `platform-team` |
| `environment` | dev, staging, prod | `prod` |
| `cost-center` | FinOps allocation | `CC-1234` |
| `application` | Application identifier | `payments-api` |
| `managed-by` | Provisioning tool | `terraform` |
| `data-classification` | Data sensitivity tier | `internal` |

## Enforcement

Tags are enforced via policy-as-code in CI and cloud policy engines. Untagged resources are flagged for remediation.
