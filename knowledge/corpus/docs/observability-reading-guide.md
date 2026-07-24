# Observability Reading Guide

This guide helps engineers interpret logs, metrics, and traces for services on the shared platform without becoming full-time SREs.

## The three pillars

| Signal | Best for | Primary tools |
| --- | --- | --- |
| Logs | Specific events, errors, audit | Log explorer, saved queries |
| Metrics | Rates, saturation, trends | Dashboards, alert history |
| Traces | Latency across services | Trace search, service map |

Start with user-visible symptoms (slow checkout, failed login), then narrow to one signal type. Jumping straight to raw logs wastes time on high-volume info lines.

## Golden signals checklist

For each investigation, answer:

1. **Traffic** — Is volume normal for time of day?
2. **Errors** — Which status codes or exception types spiked?
3. **Latency** — Did p50 stay flat while p99 grew? (tail problem)
4. **Saturation** — CPU, memory, connection pools, queue depth

Dashboards for tier-1 services include these four rows by default.

## Correlating signals

Use the trace ID injected at the edge gateway. Search logs with the same ID to connect a slow span to a downstream timeout message.

Metric-to-log workflow:

1. Open the service dashboard for the incident window.
2. Identify the first metric that diverged from baseline.
3. Pivot to logs filtered by `service`, `level>=error`, and the spike timestamp.
4. Open a exemplar trace if metrics link to trace IDs.

## Common false leads

- Deploy markers coinciding with spikes — check canary vs full rollout
- Cache stampedes after TTL alignment — look for miss-rate metrics
- Noisy neighbor on shared nodes — compare pod placement and node metrics
- Synthetic probes failing while real traffic succeeds — verify probe paths

## Access and retention

Developers have read access to dev, sandbox, and staging telemetry for their teams. Production read access requires on-call or break-glass role. Retention is 30 days hot, 400 days cold archive for compliance tiers.

## Escalation

If dashboards show cross-team impact or budget burn above 14× hourly rate, page the central incident channel with links to dashboards and the earliest anomalous graph.

Practice this workflow in sandbox using injected fault scenarios during onboarding labs.
