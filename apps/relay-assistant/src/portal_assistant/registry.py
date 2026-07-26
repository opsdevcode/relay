from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REGISTERED_TOOL_IDS: frozenset[str] = frozenset(
    {
        "docs_search",
        "scaffold_service",
        "request_sandbox",
        "service_health",
        "list_platform_services",
    }
)

KNOWN_VIEWS: frozenset[str] = frozenset(
    {"techdocs", "scaffolder", "catalog", "grafana-embed"},
)


@dataclass(frozen=True)
class ToolDefinition:
    kind: str = "read"
    requires_confirmation: bool = False
    confirm_allowed_groups: tuple[str, ...] = ()


DEFAULT_TOOL_DEFINITIONS: dict[str, ToolDefinition] = {
    "docs_search": ToolDefinition(kind="read"),
    "list_platform_services": ToolDefinition(kind="read"),
    "service_health": ToolDefinition(kind="read"),
    "scaffold_service": ToolDefinition(
        kind="write",
        requires_confirmation=True,
        confirm_allowed_groups=("relay-platform-admins",),
    ),
    "request_sandbox": ToolDefinition(
        kind="write",
        requires_confirmation=True,
        confirm_allowed_groups=("relay-platform-admins", "relay-sandbox-users"),
    ),
}


def _parse_group_list(raw: object) -> tuple[str, ...]:
    if not raw:
        return ()
    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split(",") if part.strip())
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            token = str(item).strip()
            if token:
                out.append(token)
        return tuple(out)
    return ()


def _parse_tools(raw: dict[str, Any] | None) -> dict[str, ToolDefinition]:
    tools = dict(DEFAULT_TOOL_DEFINITIONS)
    if not raw:
        return tools
    for tool_id, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get("kind") or "read").strip().lower()
        if kind not in {"read", "write"}:
            kind = "read"
        tools[str(tool_id)] = ToolDefinition(
            kind=kind,
            requires_confirmation=bool(entry.get("requires_confirmation")),
            confirm_allowed_groups=_parse_group_list(entry.get("confirm_allowed_groups")),
        )
    return tools


@dataclass(frozen=True)
class RoutingRule:
    tool: str
    patterns: tuple[re.Pattern[str], ...] = ()
    default: bool = False


@dataclass(frozen=True)
class ObservabilityServiceEntry:
    dashboard_uid: str = ""
    slo_target: str = ""


@dataclass(frozen=True)
class ObservabilityRegistry:
    grafana_path_template: str = "/d/{dashboard_uid}?var-service={service}"
    grafana_embed_path_template: str = "/d/{dashboard_uid}?orgId=1&var-service={service}&kiosk"
    default_embed_service: str = "demo-api"
    catalog: dict[str, ObservabilityServiceEntry] = field(default_factory=dict)


@dataclass(frozen=True)
class RegistryConfig:
    services: list[dict[str, Any]]
    routing: list[RoutingRule]
    tools: dict[str, ToolDefinition]
    observability: ObservabilityRegistry | None = None

    def tool_definition(self, tool_id: str) -> ToolDefinition:
        return self.tools.get(tool_id, ToolDefinition(kind="read"))

    def is_write_tool(self, tool_id: str) -> bool:
        return self.tool_definition(tool_id).kind == "write"


def registry_path() -> Path:
    return Path(__file__).resolve().parents[4] / "packages" / "platform-services" / "registry.yaml"


def _parse_observability(raw: dict[str, Any] | None) -> ObservabilityRegistry | None:
    if not raw or not isinstance(raw, dict):
        return None
    path_template = str(
        raw.get("grafana_path_template") or "/d/{dashboard_uid}?var-service={service}"
    ).strip()
    embed_template = str(
        raw.get("grafana_embed_path_template")
        or "/d/{dashboard_uid}?orgId=1&var-service={service}&kiosk"
    ).strip()
    default_embed = str(raw.get("default_embed_service") or "demo-api").strip().lower()
    catalog: dict[str, ObservabilityServiceEntry] = {}
    catalog_raw = raw.get("catalog") or raw.get("services") or {}
    if isinstance(catalog_raw, dict):
        for key, entry in catalog_raw.items():
            if not isinstance(entry, dict):
                continue
            slug = str(key).strip().lower()
            if not slug:
                continue
            catalog[slug] = ObservabilityServiceEntry(
                dashboard_uid=str(
                    entry.get("dashboard_uid") or entry.get("dashboard") or ""
                ).strip(),
                slo_target=str(entry.get("slo_target") or entry.get("slo") or "").strip(),
            )
    return ObservabilityRegistry(
        grafana_path_template=path_template,
        grafana_embed_path_template=embed_template,
        default_embed_service=default_embed or "demo-api",
        catalog=catalog,
    )


def load_registry_config(path: Path | None = None) -> RegistryConfig:
    reg_path = path or registry_path()
    if not reg_path.exists():
        return RegistryConfig(services=[], routing=[], tools=_parse_tools(None))

    with reg_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if isinstance(raw, list):
        return RegistryConfig(
            services=raw,
            routing=_legacy_routing_from_agent(),
            tools=_parse_tools(None),
        )

    if not isinstance(raw, dict):
        return RegistryConfig(services=[], routing=[], tools=_parse_tools(None))

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

    tools_raw = raw.get("tools")
    tools = _parse_tools(tools_raw if isinstance(tools_raw, dict) else None)
    observability = _parse_observability(raw.get("observability"))

    return RegistryConfig(
        services=services,
        routing=routing,
        tools=tools,
        observability=observability,
    )


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

    for tool_id, definition in config.tools.items():
        if tool_id not in REGISTERED_TOOL_IDS:
            errors.append(f"tools catalog references unknown handler: {tool_id}")
        if definition.kind == "write" and not definition.requires_confirmation:
            errors.append(f"write tool {tool_id} must set requires_confirmation: true")

    service_tools: set[str] = set()
    for svc in config.services:
        if not isinstance(svc, dict):
            continue
        for view in svc.get("views") or []:
            token = str(view).strip()
            if token and token not in KNOWN_VIEWS:
                errors.append(f"service {svc.get('id')} declares unknown view: {token}")
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
