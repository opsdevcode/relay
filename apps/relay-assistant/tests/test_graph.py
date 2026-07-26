import pytest

from portal_assistant.graph import enforce_write_tool_result, run_chat_graph


def test_enforce_write_strips_workflow_url_from_draft():
    raw = {
        "answer": "confirm me",
        "citations": [],
        "draft": {
            "action": "scaffold_service",
            "workflow_url": "https://github.com/o/r/actions/workflows/x.yml",
            "inputs": {"service_name": "demo-api"},
            "message": "draft",
        },
    }
    out = enforce_write_tool_result("scaffold_service", raw)
    assert out["draft"]["requires_confirmation"] is True
    assert "workflow_url" not in out["draft"]
    assert out["draft"]["inputs"]["service_name"] == "demo-api"


def test_enforce_write_without_draft():
    raw = {"answer": "x", "citations": [], "draft": None}
    out = enforce_write_tool_result("scaffold_service", raw)
    assert out["draft"] is None
    assert "confirmation draft" in out["answer"]


@pytest.mark.asyncio
async def test_run_chat_graph_write_path():
    class FakeStore:
        def search(self, _query: str, **kwargs: object) -> list:
            return []

    result, trace = await run_chat_graph(
        "Create a new service called demo-api",
        FakeStore(),  # type: ignore[arg-type]
    )
    assert trace.path == "write"
    assert trace.tool_id == "scaffold_service"
    assert result["draft"]["requires_confirmation"] is True
    assert "workflow_url" not in result["draft"]


@pytest.mark.asyncio
async def test_run_chat_graph_read_path():
    class FakeStore:
        def search(self, _query: str, **kwargs: object) -> list:
            return []

    result, trace = await run_chat_graph(
        "What platform services are available?",
        FakeStore(),  # type: ignore[arg-type]
    )
    assert trace.path == "read"
    assert result.get("draft") is None
