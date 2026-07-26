from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RiskTier:
    """Mirrors knowledge/corpus/docs/gitops-workflow.md risk tiers."""

    id: str
    label: str
    review: str
    examples: str


TIERS: dict[str, RiskTier] = {
    "L0": RiskTier(
        id="L0",
        label="Low — docs / non-prod config",
        review="Peer review",
        examples="Docs, non-prod config",
    ),
    "L1": RiskTier(
        id="L1",
        label="Medium — team-scoped change",
        review="Team lead approval",
        examples="Module version bump",
    ),
    "L2": RiskTier(
        id="L2",
        label="High — production infra",
        review="Engineering + SRE",
        examples="Prod infra change",
    ),
    "L3": RiskTier(
        id="L3",
        label="Critical — security-sensitive",
        review="Engineering + SRE + Security",
        examples="Security-sensitive changes",
    ),
}

SCAFFOLD_SERVICE_PATH_PREFIX = "examples/services/"
SANDBOX_INTAKE_KIND = "sandbox_request"


def tier_for_scaffold_service() -> RiskTier:
    """New golden-path example under examples/services/ (non-prod sample)."""
    return TIERS["L0"]


def tier_for_sandbox_request() -> RiskTier:
    """Environment provisioning intake — team lead tier."""
    return TIERS["L1"]


def tier_for_change_kind(kind: str) -> RiskTier:
    if kind == "scaffold_service":
        return tier_for_scaffold_service()
    if kind == SANDBOX_INTAKE_KIND or kind == "request_sandbox":
        return tier_for_sandbox_request()
    return TIERS["L1"]


def draft_risk_metadata(*, change_kind: str, target_paths: list[str]) -> dict[str, str]:
    tier = tier_for_change_kind(change_kind)
    owners = codeowners_for_paths(target_paths)
    owner_text = ", ".join(owners) if owners else "(see .github/CODEOWNERS)"
    return {
        "risk_tier": tier.id,
        "risk_tier_label": tier.label,
        "review_requirements": tier.review,
        "codeowners": owner_text,
        "change_paths": ", ".join(target_paths),
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _codeowners_path() -> Path:
    return _repo_root() / ".github" / "CODEOWNERS"


def parse_codeowners(text: str) -> list[tuple[str, tuple[str, ...]]]:
    rules: list[tuple[str, tuple[str, ...]]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        pattern = parts[0]
        owners = tuple(parts[1:])
        rules.append((pattern, owners))
    return rules


def _match_pattern(pattern: str, path: str) -> bool:
    path = path.lstrip("/")
    if pattern == "*":
        return True
    pat = pattern.lstrip("/")
    if pat.endswith("/"):
        return path.startswith(pat) or path.startswith(pat.rstrip("/") + "/")
    return path == pat or path.startswith(pat + "/")


def codeowners_for_path(path: str, rules: list[tuple[str, tuple[str, ...]]]) -> tuple[str, ...]:
    path = path.replace("\\", "/").lstrip("/")
    matched: tuple[str, ...] = ()
    for pattern, owners in rules:
        if _match_pattern(pattern, path):
            matched = owners
    return matched


def codeowners_for_paths(paths: list[str], codeowners_file: Path | None = None) -> list[str]:
    path = codeowners_file or _codeowners_path()
    if not path.is_file():
        return []
    rules = parse_codeowners(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    out: list[str] = []
    for target in paths:
        for owner in codeowners_for_path(target, rules):
            if owner not in seen:
                seen.add(owner)
                out.append(owner)
    return out


def scaffold_pr_body_markdown(
    *,
    service_name: str,
    description: str,
    github_org: str,
    owner: str,
) -> str:
    target = f"{SCAFFOLD_SERVICE_PATH_PREFIX}{service_name}/"
    meta = draft_risk_metadata(change_kind="scaffold_service", target_paths=[target])
    tier = TIERS[meta["risk_tier"]]
    return f"""## Summary
Scaffold **`{service_name}`** from the k8s-service golden path via Relay workflow dispatch.

## Inputs
- **service_name:** `{service_name}`
- **description:** {description}
- **github_org:** `{github_org}`
- **owner:** `{owner}`

## Risk tier (GitOps)
| Field | Value |
| --- | --- |
| **Tier** | **{tier.id}** — {tier.label} |
| **Review** | {tier.review} |
| **Corpus** | [gitops-workflow.md](knowledge/corpus/docs/gitops-workflow.md) |
| **CODEOWNERS** | {meta["codeowners"]} for `{target}` |

## Review checklist
- [ ] Risk tier **{tier.id}** approvals satisfied ({tier.review})
- [ ] CODEOWNERS for `{target}` have reviewed or will auto-request on GitHub
- [ ] `catalog-info.yaml` relay.dev scaffold stamp and Backstage owner look correct
- [ ] Service name and catalog metadata look correct
- [ ] K8s manifests fit your cluster conventions
- [ ] CI/CD wiring added (if needed) before merge
"""
