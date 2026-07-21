# Scaffolding via GitHub Actions (no tokens in the portal)

The working model uses **draft-and-route**: the Portal Assistant prepares a scaffold draft; on **Confirm** it returns a **Run workflow** link. The portal never holds a GitHub PAT or app private key.

## Flow

1. Chat: *"Create a new service called demo-api"*
2. Assistant shows a draft → click **Confirm**
3. UI opens `Scaffold K8s Service` on GitHub Actions with suggested inputs
4. You click **Run workflow** in GitHub
5. Actions renders `templates/k8s-service/` into `examples/services/<name>/` and opens a PR using the built-in `GITHUB_TOKEN`

## Enable the workflow (one-time, in GitHub UI)

In **`opsdevcode/ai-developer-portal`**:

1. **Settings → Actions → General → Workflow permissions**
2. Select **Read and write permissions**
3. Save

No repository secrets are required for the default same-repo scaffold PR.

## Workflow inputs

| Input | Description |
| --- | --- |
| `service_name` | Kebab-case name (e.g. `demo-api`) |
| `description` | Catalog/description string |
| `github_org` | Org for image/catalog slug (default `opsdevcode`) |

## API

```bash
curl "http://localhost:8080/actions/scaffold-link?service_name=demo-api"
```

Returns `workflow_url` and `inputs` JSON — no authentication on the portal side.

## Production notes

- Target a different repo by extending the workflow (checkout + PR to another repository) using org-level secrets — still not stored in the portal app.
- Ticket-system intake can replace the sandbox issue template link using the same pattern.
