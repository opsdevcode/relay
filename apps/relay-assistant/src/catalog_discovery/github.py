from __future__ import annotations

import base64
from typing import Any

import httpx
import yaml

from catalog_discovery.config import DISCOVERY_ANNOTATION, GitHubDiscoveryConfig


def _headers(token: str) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def list_org_repos(
    gh: GitHubDiscoveryConfig,
    *,
    token: str = "",
    client: httpx.Client | None = None,
) -> list[str]:
    if gh.repos:
        return [f"{gh.org}/{name}" if "/" not in name else name for name in gh.repos]

    repos: list[str] = []
    page = 1
    own_client = client is None
    http = client or httpx.Client(timeout=30.0)
    try:
        while len(repos) < gh.max_repos:
            url = f"{gh.api_url}/orgs/{gh.org}/repos"
            response = http.get(
                url,
                params={"per_page": 100, "page": page, "type": "all"},
                headers=_headers(token),
            )
            response.raise_for_status()
            batch = response.json()
            if not isinstance(batch, list) or not batch:
                break
            for entry in batch:
                if not isinstance(entry, dict):
                    continue
                full_name = str(entry.get("full_name") or "").strip()
                if full_name:
                    repos.append(full_name)
                if len(repos) >= gh.max_repos:
                    break
            if len(batch) < 100:
                break
            page += 1
    finally:
        if own_client:
            http.close()
    return repos[: gh.max_repos]


def fetch_catalog_file(
    repo_full_name: str,
    path: str,
    gh: GitHubDiscoveryConfig,
    *,
    token: str = "",
    client: httpx.Client | None = None,
) -> str | None:
    own_client = client is None
    http = client or httpx.Client(timeout=30.0)
    try:
        url = f"{gh.api_url}/repos/{repo_full_name}/contents/{path}"
        response = http.get(url, headers=_headers(token))
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return None
        content = payload.get("content")
        if not isinstance(content, str):
            return None
        encoding = payload.get("encoding") or "base64"
        if encoding != "base64":
            return None
        raw = base64.b64decode(content, validate=False)
        return raw.decode("utf-8", errors="replace")
    finally:
        if own_client:
            http.close()


def parse_catalog_documents(text: str) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for doc in yaml.safe_load_all(text):
        if isinstance(doc, dict) and doc.get("kind") and doc.get("apiVersion"):
            docs.append(doc)
    return docs


def stamp_discovered_entity(
    entity: dict[str, Any],
    *,
    repo_full_name: str,
    path: str,
) -> dict[str, Any]:
    stamped = dict(entity)
    metadata = dict(stamped.get("metadata") or {})
    annotations = dict(metadata.get("annotations") or {})
    annotations[DISCOVERY_ANNOTATION] = f"{repo_full_name}@{path}"
    annotations.setdefault("github.com/project-slug", repo_full_name)
    metadata["annotations"] = annotations
    stamped["metadata"] = metadata
    return stamped


def discover_entities_from_github(
    gh: GitHubDiscoveryConfig,
    *,
    token: str = "",
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (entities, log lines)."""
    logs: list[str] = []
    entities: list[dict[str, Any]] = []
    with httpx.Client(timeout=30.0) as client:
        repos = list_org_repos(gh, token=token, client=client)
        logs.append(f"repos_in_scope={len(repos)}")
        for repo in repos:
            for path in gh.paths:
                text = fetch_catalog_file(repo, path, gh, token=token, client=client)
                if not text:
                    continue
                docs = parse_catalog_documents(text)
                if not docs:
                    logs.append(f"skip {repo}/{path}: no valid entities")
                    continue
                for doc in docs:
                    entities.append(stamp_discovered_entity(doc, repo_full_name=repo, path=path))
                logs.append(f"ingested {repo}/{path} ({len(docs)} entities)")
    return entities, logs
