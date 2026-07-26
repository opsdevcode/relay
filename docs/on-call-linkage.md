# On-call linkage (Phase 2C.3)

Optional paging integration links catalog **owners** and **components** to on-call schedules and (when configured) live roster names from PagerDuty.

## Flow

1. Chat routes *on-call* questions to **`on_call_lookup`** ([`registry.yaml`](../packages/platform-services/registry.yaml)).
2. Relay resolves the target component via the same catalog index as [catalog ownership](catalog-ownership.md).
3. Schedule URLs come from **`on_call.teams`** in the registry and/or catalog annotations (`relay.dev/on-call-url`, `pagerduty.com/*`).
4. With **`ON_CALL_PROVIDER=pagerduty`** and **`PAGERDUTY_API_TOKEN`**, Relay queries the PagerDuty on-calls API for the team escalation policy.

## Try it

- `Who is on call for demo-api?` — deeplink schedule URL for **platform-team** (local default).
- `/health` exposes `on_call_provider` and `on_call_live`.

## Configure

| Variable | Purpose |
| --- | --- |
| `ON_CALL_PROVIDER` | `deeplink` (default), `pagerduty`, `opsgenie`, or `none` |
| `ON_CALL_URL_TEMPLATE` | Fallback deeplink template with `{schedule_id}`, `{team}`, `{entity}` |
| `PAGERDUTY_API_TOKEN` | REST token for live on-call names |
| `PAGERDUTY_API_URL` | API base (default `https://api.pagerduty.com`) |
| `OPSGENIE_API_TOKEN` | Reserved for future live Opsgenie roster |

Registry example (`packages/platform-services/registry.yaml`):

```yaml
on_call:
  url_template: "https://company.pagerduty.com/schedules/{schedule_id}"
  teams:
    platform-team:
      schedule_id: YOUR_SCHEDULE
      pagerduty_escalation_policy_id: YOUR_POLICY
```

## Related

- [catalog-ownership.md](catalog-ownership.md) — Phase 2C.2
- [roadmap.md](roadmap.md) — Phase 2D safety and quality
