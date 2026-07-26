# Ticket system handoff (Phase 2A.2)

Sandbox **Confirm** routes through a pluggable intake provider instead of hard-coding GitHub Issues. Local compose keeps the **github_issue** default (no secrets). Production sets **Jira**, **ServiceNow**, or a **url_template** deeplink to your org-standard catalog.

## Flow

1. Chat: *"I need a sandbox for a POC"*
2. Assistant returns a draft → **Confirm**
3. Relay calls the configured provider and returns **`intake_url`** (and **`ticket_id`** when created via API)

The web UI and API keep **`issue_url`** for the GitHub provider only (backward compatible).

## Providers

| `TICKET_INTAKE_PROVIDER` | Behavior |
| --- | --- |
| `github_issue` (default) | GitHub issue template link (`sandbox-request.md`) |
| `jira` | REST create when username + API token + project are set; otherwise Jira create deeplink |
| `servicenow` | REST create on `TICKET_INTAKE_PROJECT` table (default `incident`); otherwise ServiceNow portal deeplink |
| `url_template` | Expand `TICKET_INTAKE_URL_TEMPLATE` with `{purpose_raw}`, `{budget_raw}`, `{requester_raw}`, etc. |

## Environment

| Variable | Purpose |
| --- | --- |
| `TICKET_INTAKE_PROVIDER` | Provider id (see table) |
| `TICKET_INTAKE_BASE_URL` | Jira or ServiceNow instance URL |
| `TICKET_INTAKE_USERNAME` | Jira email or ServiceNow user for Basic auth |
| `TICKET_INTAKE_API_TOKEN` | API token / password (**Secret**, not ConfigMap) |
| `TICKET_INTAKE_PROJECT` | Jira project key or ServiceNow table name |
| `TICKET_INTAKE_ISSUE_TYPE` | Jira issue type name (default `Task`) |
| `TICKET_INTAKE_URL_TEMPLATE` | Deeplink template for `url_template` provider |

`/health` exposes `ticket_intake_provider`.

## Examples

**ServiceNow catalog deeplink (no API):**

```bash
TICKET_INTAKE_PROVIDER=url_template
TICKET_INTAKE_URL_TEMPLATE='https://company.service-now.com/sp?id=sc_cat_item&sys_id=abc&description={purpose_raw}'
```

**Jira API create:**

```bash
TICKET_INTAKE_PROVIDER=jira
TICKET_INTAKE_BASE_URL=https://company.atlassian.net
TICKET_INTAKE_USERNAME=relay-bot@company.com
TICKET_INTAKE_API_TOKEN=...   # in K8s Secret
TICKET_INTAKE_PROJECT=SANDBOX
```

## Related

- [scaffolding.md](scaffolding.md) — golden-path scaffold (separate confirm path)
- [identity-ingress.md](identity-ingress.md) — confirm authorization by IdP group
