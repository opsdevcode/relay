from __future__ import annotations

from typing import Literal, Protocol
from urllib.parse import urljoin

from portal_assistant.config import Settings

ProviderName = Literal["anthropic", "azure_openai", "openai_compatible"]


class SynthesisClient(Protocol):
    async def complete(self, *, system: str, user: str) -> str: ...


def _normalized_provider(settings: Settings) -> str:
    return (settings.llm_provider or "").strip().lower()


def resolve_synthesis_provider(settings: Settings) -> ProviderName | None:
    """Pick synthesis backend from explicit config or legacy env auto-detect."""
    explicit = _normalized_provider(settings)
    if explicit in ("", "none", "off", "extractive"):
        if explicit:
            return None
    elif explicit == "anthropic":
        if settings.anthropic_api_key:
            return "anthropic"
        return None
    elif explicit == "azure_openai":
        if (
            settings.azure_openai_api_key
            and settings.azure_openai_endpoint
            and settings.azure_openai_deployment
        ):
            return "azure_openai"
        return None
    elif explicit in ("openai_compatible", "openai", "ollama"):
        if settings.openai_compatible_base_url and settings.openai_compatible_model:
            return "openai_compatible"
        return None
    else:
        msg = (
            f"Unknown LLM_PROVIDER {settings.llm_provider!r}; "
            "use anthropic, azure_openai, openai_compatible, or none"
        )
        raise ValueError(msg)

    if settings.anthropic_api_key:
        return "anthropic"
    if (
        settings.azure_openai_api_key
        and settings.azure_openai_endpoint
        and settings.azure_openai_deployment
    ):
        return "azure_openai"
    if settings.openai_compatible_base_url and settings.openai_compatible_model:
        return "openai_compatible"
    return None


def build_synthesis_client(settings: Settings) -> SynthesisClient | None:
    provider = resolve_synthesis_provider(settings)
    if provider == "anthropic":
        return AnthropicSynthesisClient(settings)
    if provider == "azure_openai":
        return AzureOpenAISynthesisClient(settings)
    if provider == "openai_compatible":
        return OpenAICompatibleSynthesisClient(settings)
    return None


class AnthropicSynthesisClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.anthropic_api_key
        self._model = settings.anthropic_model

    async def complete(self, *, system: str, user: str) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 1024,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            response.raise_for_status()
            payload = response.json()
            content_blocks = payload.get("content", [])
            parts = [
                block.get("text", "") for block in content_blocks if block.get("type") == "text"
            ]
            return "\n".join(parts).strip()


class AzureOpenAISynthesisClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.azure_openai_api_key
        base = settings.azure_openai_endpoint.rstrip("/")
        deployment = settings.azure_openai_deployment
        version = settings.azure_openai_api_version
        self._url = f"{base}/openai/deployments/{deployment}/chat/completions?api-version={version}"

    async def complete(self, *, system: str, user: str) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._url,
                headers={
                    "api-key": self._api_key,
                    "content-type": "application/json",
                },
                json={
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 1024,
                },
            )
            response.raise_for_status()
            payload = response.json()
            choices = payload.get("choices") or []
            if not choices:
                return ""
            message = choices[0].get("message") or {}
            return str(message.get("content", "")).strip()


class OpenAICompatibleSynthesisClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.openai_compatible_api_key
        self._model = settings.openai_compatible_model
        base = settings.openai_compatible_base_url.rstrip("/") + "/"
        self._url = urljoin(base, "chat/completions")

    async def complete(self, *, system: str, user: str) -> str:
        import httpx

        headers = {"content-type": "application/json"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._url,
                headers=headers,
                json={
                    "model": self._model,
                    "max_tokens": 1024,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()
            choices = payload.get("choices") or []
            if not choices:
                return ""
            message = choices[0].get("message") or {}
            return str(message.get("content", "")).strip()
