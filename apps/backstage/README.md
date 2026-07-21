# Backstage (phase 2)

Backstage is the planned catalog / TechDocs / scaffolder backbone per the proposal.

For the working model, the standalone web chat (`apps/web/`) proves the conversational layer first. **Teams and Slack** bot adapters will call the same Portal Assistant API. Backstage will:

1. Import entities from `catalog/entities/catalog.yaml` and GitHub org discovery
2. Host the chat plugin pointing at `portal-assistant:8080`
3. Expose software templates from `templates/k8s-service/`

Bootstrap when ready:

```bash
cd apps
npx @backstage/create-app@latest backstage
```

Configure GitHub OAuth and catalog locations for `opsdevcode/*`.
