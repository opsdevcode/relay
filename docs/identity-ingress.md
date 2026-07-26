# OIDC at ingress (Phase 1D.1)

Production and shared non-prod clusters should **not** expose Relay without authentication. **Local Docker Compose** stays open (no SSO) so design partners can run `make up` or `docker compose up` without an IdP.

## Local (no OIDC)

| Surface | Auth |
| --- | --- |
| `docker compose up` / `make up` | None — by design |
| `docker compose --profile backstage up` / `make up-backstage` | None — guest Backstage auth |
| Relay API `:8080` | No API keys required for read/chat in the working model |

See [local-compose.md](local-compose.md) for running portal + Backstage together.

## Kubernetes (OIDC required)

Use ingress-level OIDC so browsers never hit `relay-web` or `relay-assistant` without a session.

### Recommended pattern

1. Deploy **oauth2-proxy** (or your platform’s equivalent) in the `relay` namespace.
2. Apply overlay **`deploy/k8s/overlays/oidc-ingress`**, which patches the base Ingress with nginx **external auth** annotations.
3. Terminate TLS at ingress (cert-manager or cloud LB).
4. Map IdP groups to headers (`X-Auth-Request-Groups`) for ABAC (Phase 1D.2 — enable `USER_CONTEXT_HEADERS_ENABLED` on the assistant).

### Steps

```bash
# 1. Base stack (no auth yet)
kubectl apply -k deploy/k8s/base

# 2. Configure and apply oauth2-proxy (example manifest — edit IdP URLs/secrets)
kubectl apply -f deploy/k8s/overlays/oidc-ingress/oauth2-proxy.example.yaml

# 3. Ingress with auth annotations
kubectl apply -k deploy/k8s/overlays/oidc-ingress
```

Replace `portal.example.com`, `--oidc-issuer-url`, and `--redirect-url` in the example with your hostname and IdP (Entra ID, Okta, Google, Cognito, etc.).

### User context (1D.2)

When **`USER_CONTEXT_HEADERS_ENABLED=true`**, `/chat` reads oauth2-proxy headers:

| Header | Use |
| --- | --- |
| `X-Auth-Request-User` | Subject (required for context) |
| `X-Auth-Request-Email` | Email principal for `doc_owner` match |
| `X-Auth-Request-Groups` | Comma-separated groups |

Hybrid/FTS retrieval then filters chunks to **`visibility = public`**, **`doc_owner` null**, or **`doc_owner`** matching subject, email, or a group. Local compose keeps the flag **off** so behavior is unchanged without ingress.

Set in K8s via ConfigMap `relay-assistant-config` (see base manifest).

### Not done yet

- **1D.3** — Confirm/scaffold actions are not yet tied to IdP groups.

Ingress OIDC blocks anonymous **browser** access; lock down direct Service/ClusterIP access with NetworkPolicy in your environment repo.

## Related

- [kubernetes.md](kubernetes.md) — base vs cloud overlays
- [security-governance.md](security-governance.md) — branch protection and secrets
