"""Backstage software template for k8s golden path (Phase 1C.4)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = REPO_ROOT / "templates" / "k8s-service" / "template.yaml"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "scaffold-k8s-service.yml"


def test_k8s_template_file_exists():
    assert TEMPLATE_PATH.is_file(), f"missing Backstage template: {TEMPLATE_PATH}"


def test_k8s_template_dispatches_scaffold_workflow():
    data = yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert data["kind"] == "Template"
    assert data["metadata"]["name"] == "k8s-golden-path"
    steps = (data.get("spec") or {}).get("steps") or []
    assert steps, "template must define scaffolder steps"
    dispatch = steps[0]
    assert dispatch.get("action") == "github:actions:dispatch"
    workflow_id = (dispatch.get("input") or {}).get("workflowId")
    assert workflow_id == "scaffold-k8s-service.yml"
    assert WORKFLOW_PATH.is_file()


def test_k8s_template_parameters_match_workflow_inputs():
    data = yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))
    props = data["spec"]["parameters"][0]["properties"]
    assert "service_name" in props
    assert "description" in props
    assert "github_org" in props

    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    for key in ("service_name", "description", "github_org"):
        assert f"{key}:" in workflow_text, f"workflow missing input {key!r}"
