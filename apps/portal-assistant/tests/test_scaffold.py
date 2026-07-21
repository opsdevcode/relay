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
