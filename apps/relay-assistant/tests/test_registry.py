import pytest

from portal_assistant.registry import (
    DEFAULT_TOOL_DEFINITIONS,
    RegistryConfig,
    RoutingRule,
    ToolDefinition,
    load_registry_config,
    resolve_tool,
    validate_registry_config,
)


def test_load_registry_config_has_services_and_routing():
    config = load_registry_config()
    assert len(config.services) >= 4
    assert len(config.routing) >= 5
    assert validate_registry_config(config) == []


@pytest.mark.parametrize(
    ("message", "expected_tool"),
    [
        ("What platform services are available?", "list_platform_services"),
        ("Create a new service called demo-api", "scaffold_service"),
        ("I need a sandbox for a POC", "request_sandbox"),
        ("How's payments-api doing on SLO?", "service_health"),
        ("What are the required resource tags?", "docs_search"),
    ],
)
def test_resolve_tool_from_registry(message: str, expected_tool: str):
    config = load_registry_config()
    assert resolve_tool(message, config) == expected_tool


def test_validate_registry_rejects_missing_default():
    config = RegistryConfig(
        services=[],
        routing=[
            RoutingRule(tool="docs_search", patterns=(__import__("re").compile("x"),)),
        ],
        tools=dict(DEFAULT_TOOL_DEFINITIONS),
    )
    errors = validate_registry_config(config)
    assert any("default: true" in err for err in errors)


def test_validate_registry_rejects_unknown_tool():
    config = RegistryConfig(
        services=[{"id": "x", "tools": ["not_a_real_tool"]}],
        routing=[RoutingRule(tool="not_a_real_tool", default=True)],
        tools={"not_a_real_tool": ToolDefinition(kind="read")},
    )
    errors = validate_registry_config(config)
    assert any("unknown tool" in err for err in errors)
