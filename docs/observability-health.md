# Service health / observability (Phase 2B.1)

The **`service_health`** chat tool returns SLO context and a **Grafana deep link** for services listed under `observability.catalog` in [`registry.yaml`](../packages/platform-services/registry.yaml). Optionally, **Prometheus** instant queries supply firing alert counts (and burn rate when configured).

Local compose defaults to **`mock`** (no Grafana/Prometheus URLs). Production sets **`GRAFANA_BASE_URL`** and/or **`PROMETHEUS_BASE_URL`**.

## Flow

1. Chat: *"How's demo-api doing on SLO?"*
2. Router selects `service_health`
3. Relay resolves the service slug, looks up the catalog entry, and returns markdown with SLO target and Grafana URL (live metrics when Prometheus is configured)

## Providers

| `OBSERVABILITY_PROVIDER` | Behavior |
| --- | --- |
| *(empty)* | `mock` unless `GRAFANA_BASE_URL` or `PROMETHEUS_BASE_URL` is set (auto-detect) |
| `mock` | Placeholder insight for local dev |
| `grafana_deeplink` | Catalog SLO + Grafana URL (read-only; no metrics API) |
| `prometheus` | Grafana URL when configured + Prometheus instant queries |

## Environment

| Variable | Purpose |
| --- | --- |
| `OBSERVABILITY_PROVIDER` | Provider id (see table) |
| `GRAFANA_BASE_URL` | Grafana origin, e.g. `https://grafana.company.com` |
| `GRAFANA_DASHBOARD_PATH_TEMPLATE` | Path template with `{dashboard_uid}` and `{service}` |
| `GRAFANA_DEFAULT_DASHBOARD_UID` | Fallback dashboard when the service is not in the catalog |
| `PROMETHEUS_BASE_URL` | Prometheus server URL for `/api/v1/query` |
| `PROMETHEUS_API_TOKEN` | Bearer token (**Secret**) when required |
| `PROMETHEUS_ALERTS_QUERY_TEMPLATE` | PromQL with `{service}` (default: firing `ALERTS` count) |
| `PROMETHEUS_BURN_RATE_QUERY_TEMPLATE` | Optional PromQL for burn rate |

`/health` exposes `observability_provider`.

## Registry catalog

```yaml
observability:
  grafana_path_template: "/d/{dashboard_uid}?orgId=1&var-service={service}"
  catalog:
    demo-api:
      dashboard_uid: relay-demo
      slo_target: "99.9%"
```

Services not in `catalog` still get a link when `GRAFANA_DEFAULT_DASHBOARD_UID` is set.

## Examples

**Grafana only (pilot):**

```bash
OBSERVABILITY_PROVIDER=grafana_deeplink
GRAFANA_BASE_URL=https://grafana.company.com
```

**Prometheus alert count + Grafana:**

```bash
OBSERVABILITY_PROVIDER=prometheus
GRAFANA_BASE_URL=https://grafana.company.com
PROMETHEUS_BASE_URL=https://prometheus.company.com
PROMETHEUS_API_TOKEN=...   # in K8s Secret
```

## Related

- [roadmap.md](roadmap.md) — Phase 2B.2 embedded Grafana view
- [audit-log.md](audit-log.md) — tool invoke audit events
