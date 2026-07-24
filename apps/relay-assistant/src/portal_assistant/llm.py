from __future__ import annotations

import re

from portal_assistant.config import settings

SYSTEM_PROMPT = """You are Relay, the assistant for an internal developer portal.
Answer using ONLY the provided context. If the context is insufficient, say you do not know.
Always include a "Sources" section listing each source path you used.
Be concise and practical. Do not invent policies or numbers not present in the context."""

_EXCERPT_MAX = 480


def _best_excerpt(content: str, question: str) -> str:
    """Pick the most relevant paragraph from a chunk (offline / no API key)."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    if not paragraphs:
        return content[:_EXCERPT_MAX].strip()

    stop = {"what", "are", "the", "how", "does", "for", "and", "with"}
    terms = [t for t in re.findall(r"[a-z0-9-]{3,}", question.lower()) if t not in stop]
    if not terms:
        return paragraphs[0][:_EXCERPT_MAX].strip()

    def score(paragraph: str) -> int:
        lower = paragraph.lower()
        return sum(1 for term in terms if term in lower)

    best = max(paragraphs, key=score)
    if len(best) > _EXCERPT_MAX:
        return best[:_EXCERPT_MAX].rstrip() + "…"
    return best


def format_extractive_answer(question: str, contexts: list[dict]) -> str:
    if not contexts:
        return (
            "I couldn't find anything in the indexed docs for that question. "
            "If you just ran `make up`, wait a few seconds for startup indexing "
            "or run `make ingest`."
        )

    parts: list[str] = [
        "Here's what the indexed documentation says (extractive mode — no API keys required):"
    ]
    seen: set[str] = set()
    for ctx in contexts[:3]:
        source = ctx["source"]
        if source in seen:
            continue
        seen.add(source)
        excerpt = _best_excerpt(ctx["content"], question)
        parts.append(f"**{ctx['title']}** (`{source}`)\n{excerpt}")

    return "\n\n".join(parts)


async def synthesize(question: str, contexts: list[dict]) -> str:
    if not settings.anthropic_api_key:
        return format_extractive_answer(question, contexts)

    if not contexts:
        return (
            "I couldn't find anything in the indexed docs for that question. "
            "Run `make ingest` after confirming the knowledge corpus is mounted."
        )

    context_block = "\n\n---\n\n".join(
        f"Source: {c['source']}\nTitle: {c['title']}\n{c['content']}" for c in contexts
    )
    user_message = f"Question: {question}\n\nContext:\n{context_block}"

    import httpx

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.anthropic_model,
                "max_tokens": 1024,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_message}],
            },
        )
        response.raise_for_status()
        payload = response.json()
        content_blocks = payload.get("content", [])
        parts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
        return "\n".join(parts).strip()
