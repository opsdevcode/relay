from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Handlers implemented in portal_assistant.tools (registry routing must reference these).
REGISTERED_TOOL_IDS: frozenset[str] = frozenset(
    {
        "docs_search",
        "scaffold_service",
        "request_sandbox",
        "service_health",
        "list_platform_services",
    }
)


@dataclass(frozen=True)
class RoutingRule:
    tool: str
    patterns: tuple[re.Pattern[str], ...] = ()
    default: bool = False


@dataclass(frozen=True)
class RegistryConfig:
    services: list[dict[str, Any]]
    routing: list[RoutingRule]


def registry_path() -> Path:
    return Path(__file__).resolve().parents[4] / "packages" / "platform-services" / "registry.yaml"


def load_registry_config(path: Path | None = None) -> RegistryConfig:
    reg_path = path or registry_path()
    if not reg_path.exists():
        return RegistryConfig(services=[], routing=[])

    with reg_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if isinstance(raw, list):
        return RegistryConfig(services=raw, routing=_legacy_routing_from_agent())

    if not isinstance(raw, dict):
        return RegistryConfig(services=[], routing=[])

    services = raw.get("services") or []
    if not isinstance(services, list):
        services = []

    routing: list[RoutingRule] = []
    for entry in raw.get("routing") or []:
        if not isinstance(entry, dict):
            continue
        tool = str(entry.get("tool") or "").strip()
        if not tool:
            continue
        compiled: list[re.Pattern[str]] = []
        for pattern in entry.get("patterns") or []:
            compiled.append(re.compile(str(pattern)))
        routing.append(
            RoutingRule(
                tool=tool,
                patterns=tuple(compiled),
                default=bool(entry.get("default")),
            )
        )

    return RegistryConfig(services=services, routing=routing)


def _legacy_routing_from_agent() -> list[RoutingRule]:
    """Fallback when registry.yaml is still a bare services list."""
    return [
        RoutingRule(
            tool="list_platform_services",
            patterns=(re.compile(r"(?i)\b(platform services|what services|capabilities)\b"),),
        ),
        RoutingRule(
            tool="scaffold_service",
            patterns=(re.compile(r"(?i)\b(create|scaffold|new service|golden path)\b"),),
        ),
        RoutingRule(
            tool="request_sandbox",
            patterns=(re.compile(r"(?i)\b(sandbox|poc|proof of concept)\b"),),
        ),
        RoutingRule(
            tool="service_health",
            patterns=(re.compile(r"(?i)\b(health|slo|alert|how'?s .+ doing)\b"),),
        ),
        RoutingRule(tool="docs_search", default=True),
    ]


def resolve_tool(message: str, config: RegistryConfig | None = None) -> str:
    cfg = config or load_registry_config()
    for rule in cfg.routing:
        if rule.default:
            continue
        for pattern in rule.patterns:
            if pattern.search(message):
                return rule.tool

    for rule in cfg.routing:
        if rule.default:
            return rule.tool

    return "docs_search"


def validate_registry_config(config: RegistryConfig) -> list[str]:
    """Return human-readable validation errors (empty list = OK)."""
    errors: list[str] = []

    defaults = [r for r in config.routing if r.default]
    if len(defaults) != 1:
        errors.append("routing must contain exactly one entry with default: true")

    seen_tools: set[str] = set()
    for rule in config.routing:
        if rule.tool in seen_tools:
            errors.append(f"duplicate routing tool: {rule.tool}")
        seen_tools.add(rule.tool)

        if rule.tool not in REGISTERED_TOOL_IDS:
            errors.append(f"routing references unknown tool (no handler): {rule.tool}")

        if not rule.default and not rule.patterns:
            errors.append(f"routing tool {rule.tool} needs patterns or default: true")

    service_tools: set[str] = set()
    for svc in config.services:
        if not isinstance(svc, dict):
            continue
        for tool in svc.get("tools") or []:
            service_tools.add(str(tool))

    for tool in service_tools:
        if tool not in REGISTERED_TOOL_IDS:
            errors.append(f"service declares unknown tool (no handler): {tool}")

    default_tool = next((r.tool for r in config.routing if r.default), None)
    for tool in service_tools:
        if tool in seen_tools or tool == default_tool:
            continue
        errors.append(
            f"service tool {tool} is not reachable via routing "
            "(add a routing rule or set default to docs_search)"
        )

    return errors
