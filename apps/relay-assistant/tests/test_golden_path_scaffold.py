"""Golden-path render + catalog registration (Phase 2A.1)."""

from __future__ import annotations

from pathlib import Path

import yaml

from portal_assistant.scaffold_catalog import catalog_target, register_scaffolded_service

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_catalog_template_has_relay_scaffold_stamp():
    path = REPO_ROOT / "templates" / "k8s-service" / "catalog-info.yaml"
    text = path.read_text(encoding="utf-8")
    assert "relay.dev/scaffold-template: k8s-golden-path" in text
    assert "relay.dev/scaffold-path: examples/services/{{ service_name }}" in text


def test_demo_api_catalog_has_scaffold_stamp():
    path = REPO_ROOT / "examples" / "services" / "demo-api" / "catalog-info.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    annotations = (doc.get("metadata") or {}).get("annotations") or {}
    assert annotations.get("relay.dev/scaffold-template") == "k8s-golden-path"


def test_scaffolded_services_location_lists_demo_api():
    path = REPO_ROOT / "catalog" / "entities" / "scaffolded-services.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc.get("kind") == "Location"
    targets = (doc.get("spec") or {}).get("targets") or []
    assert "../../examples/services/demo-api/catalog-info.yaml" in targets


def test_register_scaffolded_service_idempotent(tmp_path: Path):
    service = "widget-api"
    catalog_path = tmp_path / "examples" / "services" / service / "catalog-info.yaml"
    catalog_path.parent.mkdir(parents=True)
    catalog_path.write_text("metadata:\n  name: widget-api\n", encoding="utf-8")

    assert register_scaffolded_service(service, repo_root=tmp_path) is True
    assert register_scaffolded_service(service, repo_root=tmp_path) is False
    location = yaml.safe_load(
        (tmp_path / "catalog/entities/scaffolded-services.yaml").read_text(encoding="utf-8")
    )
    assert catalog_target(service) in location["spec"]["targets"]


def test_scaffold_workflow_verifies_catalog_stamp():
    workflow = (REPO_ROOT / ".github/workflows/scaffold-k8s-service.yml").read_text(
        encoding="utf-8"
    )
    assert "Verify catalog-info stamp" in workflow
    assert "relay.dev/scaffold-template" in workflow
    assert "Ensure target path is free" in workflow


def test_scaffold_workflow_uses_risk_tier_pr_body():
    workflow = (REPO_ROOT / ".github/workflows/scaffold-k8s-service.yml").read_text(
        encoding="utf-8"
    )
    assert "render-scaffold-pr-body.py" in workflow
    assert "body-path:" in workflow
