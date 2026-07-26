# Scaffolded services

Services created via the **Scaffold K8s Service** GitHub Actions workflow land here as pull requests under `examples/services/<service-name>/`.

Each PR includes a **`catalog-info.yaml`** with `relay.dev/scaffold-*` stamps and registers the entity in `catalog/entities/scaffolded-services.yaml` for Backstage import.

Trigger the workflow from the assistant UI (**Confirm** on a scaffold draft) or from:

`Actions → Scaffold K8s Service → Run workflow`

No API tokens are required in the portal — GitHub Actions uses the built-in `GITHUB_TOKEN` to open the PR.
