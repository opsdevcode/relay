# AKS overlay

Sets a default ingress class for clusters on **AKS**. Replace `ingressClassName` in `kustomization.yaml` with whatever your AKS cluster uses (for example `nginx`, or a cluster-specific class from your ingress controller add-on).

No cloud-specific CRDs beyond ingress class tuning for **AKS** — base manifests remain portable Kubernetes.
