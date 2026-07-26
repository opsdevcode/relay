from __future__ import annotations

from portal_assistant.risk_tiers import (
    SCAFFOLD_SERVICE_PATH_PREFIX,
    codeowners_for_path,
    draft_risk_metadata,
    parse_codeowners,
    tier_for_sandbox_request,
    tier_for_scaffold_service,
)


def test_tier_for_scaffold_is_l0():
    assert tier_for_scaffold_service().id == "L0"


def test_tier_for_sandbox_is_l1():
    assert tier_for_sandbox_request().id == "L1"


def test_codeowners_last_match_wins():
    rules = parse_codeowners("* @default\n/examples/services/ @platform\n/deploy/ @sre\n")
    assert codeowners_for_path("examples/services/demo-api/catalog-info.yaml", rules) == (
        "@platform",
    )
    assert codeowners_for_path("deploy/k8s/base/configmap.yaml", rules) == ("@sre",)


def test_draft_risk_metadata_includes_codeowners():
    meta = draft_risk_metadata(
        change_kind="scaffold_service",
        target_paths=[f"{SCAFFOLD_SERVICE_PATH_PREFIX}payments-api/"],
    )
    assert meta["risk_tier"] == "L0"
    assert "review_requirements" in meta
    assert meta["codeowners"]  # default repo CODEOWNERS has @erskaggs


def test_scaffold_pr_body_includes_tier_and_corpus_link():
    from portal_assistant.risk_tiers import scaffold_pr_body_markdown

    body = scaffold_pr_body_markdown(
        service_name="payments-api",
        description="Payments",
        github_org="opsdevcode",
        owner="platform-team",
    )
    assert "Risk tier" in body
    assert "**L0**" in body
    assert "gitops-workflow.md" in body
    assert "CODEOWNERS" in body
