# Golden Path Kubernetes

The golden path is the supported way to run containerized workloads on the shared Kubernetes platform. Deviations require an architecture review and a documented exception.

## What the path includes

- Helm or Kustomize overlays generated from the service scaffold
- Distroless or hardened base images from the internal registry
- Network policies default-deny with explicit egress allow lists
- Pod security standards at the restricted profile
- Horizontal pod autoscaling on CPU or custom metrics
- GitOps delivery via the platform application controller

## Namespace model

Each team receives logical namespaces per environment:

| Environment | Purpose | Data |
| --- | --- | --- |
| `dev-*` | Individual experimentation | Synthetic only |
| `sandbox-*` | Integration and demos | Synthetic only |
| `staging-*` | Pre-production validation | Anonymized subsets |
| `prod-*` | Customer-facing | Production |

Resource quotas and limit ranges are applied at namespace creation. Request quota increases through a standard change ticket.

## Deployment contract

Every workload must expose:

- `/healthz` and `/readyz` HTTP probes
- Structured JSON logs on stdout
- OpenTelemetry traces exported to the cluster collector
- Prometheus metrics on `/metrics` or a documented port

The deploy pipeline rejects manifests missing probes or required labels (`app`, `team`, `version`).

## Ingress and TLS

External traffic uses the shared ingress controller and automatic certificates from the internal CA. Services do not run their own TLS termination at the pod unless approved for compliance reasons.

## Rollouts

Use rolling updates with `maxUnavailable: 0` for tier-1 services. Blue-green or canary patterns are available through the progressive delivery add-on; enable it in `values.yaml` under `delivery.strategy`.

## When not to use Kubernetes

Batch jobs under ten minutes may use the managed job runner instead. GPU workloads must land on the dedicated node pools documented in the compute guide.

## Migration off golden path

Teams maintaining custom clusters must publish a deprecation timeline and re-home workloads within two quarters or fund dedicated platform capacity.
