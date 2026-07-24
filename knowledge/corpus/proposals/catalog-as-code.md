# Catalog-as-Code Proposal

## Status

Proposed — target adoption next quarter for new services; existing services migrate over two quarters.

## Problem

Service metadata today lives in spreadsheets, wikis, and tribal knowledge. Onboarding engineers cannot discover owners, dependencies, or SLOs consistently. Platform automation lacks a single source for scoring, tagging, and lifecycle events.

## Proposal

Treat the software catalog as version-controlled YAML beside each repository, aggregated into a central index by nightly automation.

### Entity model

Each `catalog-info.yaml` describes one component:

- `name`, `type` (service, library, data pipeline)
- `owner` team reference
- `lifecycle` (experimental, production, deprecated)
- `dependsOn` logical IDs
- Links to runbooks, dashboards, and repos

Teams may extend with custom annotations prefixed `platform.io/`.

### Workflows

1. Scaffold adds a valid catalog file on service creation.
2. CI validates schema and referential integrity (owners exist, no cycles).
3. Index job publishes to the developer portal search API.
4. Deprecation sets `lifecycle: deprecated` and opens a cleanup ticket automatically.

### Benefits

- Golden-path generators read catalog entries for defaults
- Incident tools resolve ownership in one lookup
- FinOps maps `cost-center` from catalog to cloud tags
- Compliance exports a machine-readable inventory

## Non-goals

- Replacing CMDB asset records for physical hardware
- Storing secrets or endpoint credentials in catalog files
- Mandating full architecture diagrams in v1

## Rollout

| Phase | Scope |
| --- | --- |
| 1 | Schema, linter, portal read-only view |
| 2 | CI required on default branch for new repos |
| 3 | Scorecards (SLO defined, on-call linked, docs present) |

## Open questions

- How to model multi-region duplicates—as one logical service or sharded entries?
- Should third-party SaaS dependencies appear as `dependsOn` or a separate integration type?

Feedback welcome in platform office hours before phase 2 enforcement.
