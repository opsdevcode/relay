from __future__ import annotations

import httpx

from portal_assistant.config import settings

SYSTEM_PROMPT = """You are the Platform Assistant for an internal developer portal.
Answer using ONLY the provided context. If the context is insufficient, say you do not know.
Always include a "Sources" section listing each source path you used.
Be concise and practical. Do not invent policies or numbers not present in the context."""


async def synthesize(question: str, contexts: list[dict]) -> str:
    if not settings.anthropic_api_key:
        if not contexts:
            return (
                "No indexed documents matched your question. "
                "Run `make ingest` after setting KNOWLEDGE_PATH to your sn repo clone.\n\n"
                "Set ANTHROPIC_API_KEY in .env for synthesized answers."
            )
        lines = ["Retrieved context (set ANTHROPIC_API_KEY for synthesized answers):\n"]
        for idx, ctx in enumerate(contexts, start=1):
            lines.append(f"{idx}. **{ctx['source']}** — {ctx['title']}\n   {ctx['content'][:400]}...")
        lines.append("\n**Sources**\n" + "\n".join(f"- {c['source']}" for c in contexts))
        return "\n".join(lines)

    context_block = "\n\n---\n\n".join(
        f"Source: {c['source']}\nTitle: {c['title']}\n{c['content']}" for c in contexts
    )
    user_message = f"Question: {question}\n\nContext:\n{context_block}"

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
        parts = [block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text"]
        return "\n".join(parts).strip()
