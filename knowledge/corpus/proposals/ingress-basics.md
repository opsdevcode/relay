# Ingress Basics Proposal

## Status

Draft reference — aligns application teams on shared ingress behavior before the next controller upgrade.

## Overview

Ingress resources declare how HTTP and HTTPS traffic reaches in-cluster services. The platform operates a managed ingress controller pair (public and internal classes) so teams avoid running their own edge proxies.

## Ingress classes

| Class | Audience | TLS | Typical use |
| --- | --- | --- | --- |
| `public` | Internet via WAF | Public CA certs | Customer APIs and web apps |
| `internal` | Corp network | Internal CA | Admin tools, backoffice |
| `mesh` | Service mesh only | mTLS inside mesh | East-west not for browsers |

Manifests must set `ingressClassName` explicitly; defaulting is disabled to prevent accidental exposure.

## Hostnames and DNS

Application teams request DNS names through the portal. Automated records point to the shared load balancer. Wildcard certificates cover `*.apps.example.internal`; customer-facing names receive individual certs.

Do not hard-code IP addresses in clients; use DNS and expect occasional balancer migrations.

## Path routing

Prefer host-based routing (`api.example.com`) over path splitting on one host unless a legacy constraint requires sharing. When splitting paths:

- Longest prefix wins
- Document precedence in the service README
- Keep health checks on dedicated paths without auth middleware

## Timeouts and body size

Platform defaults:

- Read timeout: 60 seconds (adjust via annotation up to 300 for approved batch APIs)
- Max body: 10 MiB on public class unless ticket raises limit
- WebSocket upgrades enabled on both classes

## Security headers

The controller injects HSTS, frame deny, and baseline CSP on public ingress. Teams add route-specific headers via annotations; security review required for permissive CSP.

## Observability

Access logs stream to the central logging pipeline with `host`, `path`, `status`, and `request_id`. Metrics include request rate and 5xx ratio per ingress object—wire alerts to your service SLOs.

## Migration note

Legacy `kubernetes.io/ingress.class` annotations are deprecated. Update manifests before the controller upgrade window announced in the change calendar.
