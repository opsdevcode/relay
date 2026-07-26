"""K8s overlay layout (Phase 1D.1 OIDC ingress)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OIDC_OVERLAY = REPO_ROOT / "deploy" / "k8s" / "overlays" / "oidc-ingress"


def test_oidc_ingress_overlay_files_exist():
    assert (OIDC_OVERLAY / "kustomization.yaml").is_file()
    assert (OIDC_OVERLAY / "ingress-oidc-patch.yaml").is_file()
    assert (OIDC_OVERLAY / "oauth2-proxy.example.yaml").is_file()


def test_oidc_ingress_overlay_kustomize_builds():
    if not shutil.which("kubectl"):
        return
    subprocess.run(
        ["kubectl", "kustomize", str(OIDC_OVERLAY)],
        check=True,
        capture_output=True,
        text=True,
    )
