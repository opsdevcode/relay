from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from portal_assistant.config import Settings, settings

DISCOVERY_ANNOTATION = "relay.dev/discovered-from"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_discovery_config_path() -> Path:
    return repo_root() / "catalog" / "discovery.yaml"


def default_output_path() -> Path:
    return repo_root() / "catalog" / "entities" / "discovered-github.yaml"


@dataclass(frozen=True)
class GitHubDiscoveryConfig:
    org: str
    repos: tuple[str, ...]
    paths: tuple[str, ...]
    api_url: str
    max_repos: int


@dataclass(frozen=True)
class DiscoveryConfig:
    github: GitHubDiscoveryConfig | None
    output_path: Path


def _parse_github(raw: dict[str, Any] | None) -> GitHubDiscoveryConfig | None:
    if not raw or not isinstance(raw, dict):
        return None
    org = str(raw.get("org") or "").strip()
    if not org:
        return None
    repos_raw = raw.get("repos") or []
    repos: list[str] = []
    if isinstance(repos_raw, list):
        for item in repos_raw:
            token = str(item).strip()
            if token:
                repos.append(token)
    paths_raw = raw.get("paths") or ["catalog-info.yaml"]
    paths: list[str] = []
    if isinstance(paths_raw, list):
        for item in paths_raw:
            token = str(item).strip().lstrip("/")
            if token:
                paths.append(token)
    if not paths:
        paths = ["catalog-info.yaml"]
    api_url = str(raw.get("api_url") or "https://api.github.com").rstrip("/")
    max_repos = int(raw.get("max_repos") or 100)
    max_repos = max(1, min(max_repos, 500))
    return GitHubDiscoveryConfig(
        org=org,
        repos=tuple(repos),
        paths=tuple(paths),
        api_url=api_url,
        max_repos=max_repos,
    )


def load_discovery_config(path: Path | None = None) -> DiscoveryConfig:
    cfg_path = path or default_discovery_config_path()
    if not cfg_path.is_file():
        return DiscoveryConfig(github=None, output_path=default_output_path())
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return DiscoveryConfig(github=None, output_path=default_output_path())
    out = raw.get("output_path") or "catalog/entities/discovered-github.yaml"
    output = repo_root() / str(out).lstrip("/")
    github = _parse_github(raw.get("github"))
    return DiscoveryConfig(github=github, output_path=output)


def resolve_github_token(cfg: Settings | None = None) -> str:
    conf = cfg or settings
    env_token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_TOKEN") or "").strip()
    return (
        (conf.github_api_token or "").strip()
        or env_token
        or (conf.ticket_intake_api_token or "").strip()
    )


def discovery_enabled(config: DiscoveryConfig | None = None) -> bool:
    disc = config or load_discovery_config()
    return disc.github is not None
