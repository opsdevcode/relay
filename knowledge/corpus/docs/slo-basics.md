# SLO Basics

Service level objectives (SLOs) express how reliable a service should be for users. They connect product expectations to engineering priorities and on-call response.

## Definitions

| Term | Meaning |
| --- | --- |
| SLI | Measurable signal (latency, availability, correctness) |
| SLO | Target range for an SLI over a window |
| Error budget | Allowed bad events before the SLO is violated |
| SLA | Contractual commitment; often stricter than internal SLO |

Platform teams publish default SLI libraries; product teams choose targets within approved bands.

## Picking an SLI

Good SLIs are:

- User-centric (what customers experience)
- Measurable from production telemetry
- Resistant to gaming

Examples:

- Availability: ratio of successful HTTP requests excluding client errors
- Latency: proportion of requests faster than 300 ms at p99
- Freshness: age of the newest row in a replication lag metric

Avoid infrastructure-only metrics (CPU) unless they directly predict user pain.

## Setting the target

Start from historical performance plus product requirements. A common starting point for APIs is 99.9% monthly availability with latency SLOs on critical endpoints only.

Document assumptions: traffic growth, maintenance windows, and dependency SLOs. If a downstream database offers 99.95%, your service cannot honestly claim 99.99% without redundancy.

## Error budgets

Error budget = `(1 - SLO target) × eligible events` in the window.

When budget remains, ship features and take reasonable deploy risk. When budget burns fast, freeze risky changes and focus on reliability work until budget recovers.

Burn-rate alerts (multi-window) page on-call before the month ends with no budget left.

## Review cadence

- Weekly: team review of budget remaining and recent incidents
- Quarterly: adjust targets with product and SRE sign-off
- After major incidents: blameless postmortem ties actions to SLO gaps

## Tooling

SLO definitions live in version control beside service metadata. Dashboards pull from the metrics backend; recording rules materialize SLI time series for alerting.

New services must publish at least one availability SLI before production promotion.
