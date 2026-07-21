from __future__ import annotations

import re

from portal_assistant.llm import synthesize
from portal_assistant.store import DocumentStore
from portal_assistant.tools import (
    draft_sandbox_request,
    draft_scaffold,
    list_platform_services,
    service_health,
)


def classify_intent(message: str) -> str:
    lower = message.lower()
    if re.search(r"\b(create|scaffold|new service|golden path)\b", lower):
        return "scaffold"
    if re.search(r"\b(sandbox|poc|proof of concept)\b", lower):
        return "sandbox"
    if re.search(r"\b(health|slo|alert|how'?s .+ doing)\b", lower):
        return "health"
    if re.search(r"\b(platform services|what services|capabilities)\b", lower):
        return "services"
    return "qa"


def extract_service_name(message: str) -> str:
    quoted = re.search(r"['\"]([^'\"]+)['\"]", message)
    if quoted:
        return slugify_name(quoted.group(1))
    tokens = re.findall(r"\b[a-z][a-z0-9-]{2,}\b", message.lower())
    skip = {"create", "service", "scaffold", "called", "named", "new", "the", "for", "please"}
    for token in tokens:
        if token not in skip:
            return token
    return "demo-service"


def slugify_name(name: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-") or "demo-service"


async def handle_message(message: str, store: DocumentStore) -> dict:
    intent = classify_intent(message)

    if intent == "services":
        return {"answer": list_platform_services(), "citations": [], "draft": None}

    if intent == "scaffold":
        name = extract_service_name(message)
        draft = draft_scaffold(name)
        return {
            "answer": draft["message"],
            "citations": [],
            "draft": draft,
        }

    if intent == "sandbox":
        draft = draft_sandbox_request(message[:200])
        return {"answer": draft["message"], "citations": [], "draft": draft}

    if intent == "health":
        name = extract_service_name(message)
        health = service_health(name)
        return {
            "answer": (
                f"**{health['service']}** (mock insight)\n"
                f"- SLO target: {health['slo']['target']}\n"
                f"- Burn rate: {health['slo']['burn_rate']}\n"
                f"- {health['note']}"
            ),
            "citations": [],
            "draft": None,
        }

    hits = store.search(message)
    citations = [{"source": h["source"], "title": h["title"]} for h in hits]
    answer = await synthesize(message, hits)
    return {"answer": answer, "citations": citations, "draft": None}
