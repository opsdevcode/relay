# Kubernetes deployment (any managed cluster)

Manifests are **cloud-neutral** in `deploy/k8s/base/`. Only ingress class and load-balancer annotations differ per cloud — those live in overlays.

## Build and push images

```bash
make build-k8s
docker push ghcr.io/opsdevcode/portal-assistant:local
docker push ghcr.io/opsdevcode/portal-web:local
```

Tag `:latest` (or digest-pin) in your GitOps repo before prod.

## Apply base (generic / kind / minikube)

```bash
kubectl apply -k deploy/k8s/base
```

Create a real Secret before deploying (do not commit secrets):

```bash
kubectl create namespace developer-portal
kubectl -n developer-portal create secret generic portal-assistant-secrets \
  --from-literal=ANTHROPIC_API_KEY=... \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=REDIS_URL=redis://...
```

## Cloud overlays

| Overlay | Path | What changes |
| --- | --- | --- |
| **EKS** | `deploy/k8s/overlays/eks` | ALB ingress class + annotations |
| **AKS** | `deploy/k8s/overlays/aks` | Set ingress class for your AKS cluster (see overlay README) |
| **GKE** | `deploy/k8s/overlays/gke` | GCE ingress class |

```bash
kubectl apply -k deploy/k8s/overlays/eks   # or aks / gke
```

## Managed services (recommended for prod)

Run **Postgres** and **Redis** as managed services (RDS/Aurora, ElastiCache, Memorystore, etc.) instead of in-cluster StatefulSets. Update `DATABASE_URL` and `REDIS_URL` in the Secret.

## GitOps

Point Argo CD / Flux at `deploy/k8s/overlays/<cloud>` in this repo. Image tags and secrets should come from your live/env repo pattern — same as the proposal's `platform-live` model.

## What stays portable

- Deployment + Service + Ingress (standard API)
- GHCR images (works on any cluster with pull access)
- Health probes on `/health`
- No cloud-specific CRDs in base

## What you add per environment

- Ingress hostname + TLS cert (cert-manager)
- OIDC at ingress (corporate IdP, Cognito, Google IAP, etc.)
- External Secrets Operator → cloud secret store
- NetworkPolicy (optional)
- HPA (optional — add when load testing)

## Golden-path services

The `templates/k8s-service/` template ships plain `deploy/k8s/manifests.yaml` — no Helm provider or cloud-specific modules. Teams adjust ingress and registry per cluster.
