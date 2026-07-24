# Incident Runbook Template

Copy this template into your service repository as `docs/runbook.md` and keep it current after every postmortem.

---

## Service overview

**Name:**  
**Tier:** (1 / 2 / 3)  
**Owner team:**  
**On-call rotation:**  
**Primary dashboard:**  
**Pager policy:**

One paragraph describing what the service does for users and its critical dependencies.

## Symptoms and detection

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Example: elevated 503 | Deploy or dependency | Recent deploy graph |
| | | |

List alerts that fire for this service and what each means in plain language.

## Immediate mitigation

1. **Confirm impact** — Compare error rate to SLO dashboard; note regions affected.
2. **Stabilize** — Scale replicas, disable feature flag, or fail over read replica (circle applicable steps).
3. **Communicate** — Post in `#incidents` with severity, impact summary, and commander if assigned.

Include exact commands or links approved for production (rollback job, flag console, traffic shift).

## Diagnostics

- **Logs:** Saved query link filtered by service and `level=error`
- **Traces:** Example trace ID pattern or slow endpoint name
- **Dependencies:** Upstream health checks and contact teams

Document known false positives (cache warmers, batch jobs).

## Rollback and recovery

| Action | When | Owner | Rollback time |
| --- | --- | --- | --- |
| Revert deploy | After bad release | On-call | ~5 min |
| Database failover | Primary unavailable | DBA escalation | ~15 min |

Verify recovery with synthetic checks and a sample of real user flows.

## Escalation

| Condition | Escalate to | Contact method |
| --- | --- | --- |
| Budget exhausted | SRE lead | Pager |
| Data corruption suspected | DBA + Security | Incident bridge |

## Post-incident

- File postmortem within 48 hours for sev-1 and sev-2
- Update this runbook with new mitigations
- Track action items in the team backlog with due dates

---

Remove instructional prose above the divider before publishing; leave only filled sections for on-call use.
