import pytest

from portal_assistant.scaffold import build_workflow_dispatch, normalize_service_name


def test_normalize_service_name():
    assert normalize_service_name("Demo-API") == "demo-api"


def test_build_workflow_dispatch():
    payload = build_workflow_dispatch("demo-api", "My demo service")
    assert payload["mode"] == "workflow_dispatch"
    assert "scaffold-k8s-service.yml" in payload["workflow_url"]
    assert payload["inputs"]["service_name"] == "demo-api"
    assert payload["inputs"]["description"] == "My demo service"


def test_invalid_service_name():
    with pytest.raises(ValueError):
        normalize_service_name("!!!")


def test_confirm_scaffold_draft_uses_chat_draft_shape():
    """Draft from /chat stores service_name under inputs (same as build_workflow_dispatch)."""
    from portal_assistant.scaffold import confirm_scaffold_draft
    from portal_assistant.tools import draft_scaffold

    draft = draft_scaffold("payments-api", "Payments service")
    result = confirm_scaffold_draft(draft)
    assert result["inputs"]["service_name"] == "payments-api"
    assert result["risk_tier"] == "L0"
    assert "gitops-workflow.md" in result["pr_body_preview"]
