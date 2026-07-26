from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from portal_assistant.config import Settings
from portal_assistant.llm import synthesize
from portal_assistant.llm_providers import (
    AnthropicSynthesisClient,
    AzureOpenAISynthesisClient,
    OpenAICompatibleSynthesisClient,
    build_synthesis_client,
    resolve_synthesis_provider,
)


def test_resolve_provider_none_disables_synthesis():
    settings = Settings(llm_provider="none", anthropic_api_key="sk-test")
    assert resolve_synthesis_provider(settings) is None


def test_resolve_provider_auto_anthropic():
    settings = Settings(anthropic_api_key="sk-test")
    assert resolve_synthesis_provider(settings) == "anthropic"


def test_resolve_provider_explicit_azure():
    settings = Settings(
        llm_provider="azure_openai",
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_api_key="key",
        azure_openai_deployment="gpt-4o",
    )
    assert resolve_synthesis_provider(settings) == "azure_openai"


def test_resolve_provider_openai_compatible():
    settings = Settings(
        llm_provider="openai_compatible",
        openai_compatible_base_url="http://localhost:11434/v1",
        openai_compatible_model="llama3",
    )
    assert resolve_synthesis_provider(settings) == "openai_compatible"


def test_unknown_llm_provider_raises():
    settings = Settings(llm_provider="vendor-x")
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        resolve_synthesis_provider(settings)


def test_build_client_anthropic():
    settings = Settings(anthropic_api_key="sk-test")
    client = build_synthesis_client(settings)
    assert isinstance(client, AnthropicSynthesisClient)


@pytest.mark.asyncio
async def test_anthropic_client_complete():
    settings = Settings(anthropic_api_key="sk-test", anthropic_model="claude-test")
    client = AnthropicSynthesisClient(settings)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"content": [{"type": "text", "text": "Answer with Sources"}]}

    mock_http = AsyncMock()
    mock_http.post.return_value = mock_response
    mock_http.__aenter__.return_value = mock_http
    mock_http.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_http):
        text = await client.complete(system="sys", user="user")

    assert text == "Answer with Sources"
    call_kwargs = mock_http.post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "claude-test"


@pytest.mark.asyncio
async def test_azure_openai_client_complete():
    settings = Settings(
        azure_openai_endpoint="https://acct.openai.azure.com",
        azure_openai_api_key="azure-key",
        azure_openai_deployment="my-deploy",
    )
    client = AzureOpenAISynthesisClient(settings)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "Azure answer"}}]}

    mock_http = AsyncMock()
    mock_http.post.return_value = mock_response
    mock_http.__aenter__.return_value = mock_http
    mock_http.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_http):
        text = await client.complete(system="sys", user="user")

    assert text == "Azure answer"
    url = mock_http.post.call_args.args[0]
    assert "deployments/my-deploy/chat/completions" in url


@pytest.mark.asyncio
async def test_openai_compatible_client_complete():
    settings = Settings(
        openai_compatible_base_url="http://localhost:11434/v1",
        openai_compatible_model="llama3",
    )
    client = OpenAICompatibleSynthesisClient(settings)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "Local model answer"}}]}

    mock_http = AsyncMock()
    mock_http.post.return_value = mock_response
    mock_http.__aenter__.return_value = mock_http
    mock_http.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_http):
        text = await client.complete(system="sys", user="user")

    assert text == "Local model answer"
    url = mock_http.post.call_args.args[0]
    assert url.endswith("/chat/completions")


@pytest.mark.asyncio
async def test_synthesize_uses_configured_client():
    contexts = [
        {
            "source": "/knowledge/a.md",
            "title": "Doc",
            "content": "Body",
        }
    ]
    mock_client = AsyncMock()
    mock_client.complete.return_value = "Synthesized"

    with patch(
        "portal_assistant.llm.build_synthesis_client",
        return_value=mock_client,
    ):
        answer = await synthesize("Question?", contexts)

    assert answer == "Synthesized"
    mock_client.complete.assert_awaited_once()
