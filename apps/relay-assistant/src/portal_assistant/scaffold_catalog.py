from __future__ import annotations

from pathlib import Path

import yaml

REL_PREFIX = "../../examples/services/"


def catalog_target(service_name: str) -> str:
    return f"{REL_PREFIX}{service_name}/catalog-info.yaml"


def scaffolded_location_path(repo_root: Path) -> Path:
    return repo_root / "catalog" / "entities" / "scaffolded-services.yaml"


def register_scaffolded_service(service_name: str, *, repo_root: Path) -> bool:
    """Append examples/services/<name>/catalog-info.yaml to scaffolded-services Location."""
    location_file = scaffolded_location_path(repo_root)
    target = catalog_target(service_name)
    catalog_info = repo_root / "examples" / "services" / service_name / "catalog-info.yaml"
    if not catalog_info.is_file():
        raise FileNotFoundError(f"missing rendered catalog-info: {catalog_info}")

    if location_file.is_file():
        doc = yaml.safe_load(location_file.read_text(encoding="utf-8"))
    else:
        doc = {
            "apiVersion": "backstage.io/v1alpha1",
            "kind": "Location",
            "metadata": {
                "name": "scaffolded-service-examples",
                "description": "Golden-path services under examples/services/ (Phase 2A.1)",
            },
            "spec": {"type": "file", "targets": []},
        }

    if not isinstance(doc, dict):
        raise ValueError(f"invalid location file: {location_file}")

    spec = doc.setdefault("spec", {})
    targets = spec.setdefault("targets", [])
    if not isinstance(targets, list):
        raise ValueError("location spec.targets must be a list")

    if target in targets:
        return False

    targets.append(target)
    targets.sort()
    location_file.parent.mkdir(parents=True, exist_ok=True)
    location_file.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return True
