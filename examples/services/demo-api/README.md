# demo-api

Containerized service scaffolded from the Relay golden path.
Runs on **any managed Kubernetes** (EKS, AKS, GKE, etc.).

## Layout

```text
.
├── Dockerfile
├── catalog-info.yaml
├── deploy/k8s/          # plain Kubernetes manifests
├── .github/workflows/
└── src/
```

## Local

```bash
docker build -t demo-api:local .
```

## Deploy

```bash
kubectl apply -f deploy/k8s/
```

Adjust `deploy/k8s/` ingress class and image registry for your cluster overlay.
