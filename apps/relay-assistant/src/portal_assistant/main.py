from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from portal_assistant import __version__
from portal_assistant.agent import handle_message
from portal_assistant.config import settings
from portal_assistant.scaffold import build_workflow_dispatch, confirm_scaffold_draft
from portal_assistant.sessions import SessionStore, create_session_store
from portal_assistant.store import DocumentStore
from portal_assistant.tools import load_registry

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    thread_id: str | None = Field(default=None, max_length=64)


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict]
    draft: dict | None = None
    thread_id: str | None = None


class ConfirmRequest(BaseModel):
    draft: dict


store = DocumentStore(settings.database_url)
session_store: SessionStore | None = None


def _ensure_indexed() -> int:
    store.init_schema()
    if store.count() > 0:
        return store.count()
    try:
        from rag_ingestion.cli import ingest

        logger.info("Knowledge index empty — running startup ingestion")
        ingest()
    except Exception:
        logger.exception("Startup ingestion failed")
        raise
    return store.count()


@asynccontextmanager
async def lifespan(_: FastAPI):
    global session_store
    _ensure_indexed()
    session_store = create_session_store(
        settings.redis_url,
        ttl_seconds=settings.session_ttl_seconds,
        max_turns=settings.session_max_turns,
    )
    yield


app = FastAPI(title="Relay", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    count = store.count()
    return {
        "status": "ok",
        "version": __version__,
        "documents": count,
        "answer_mode": "llm" if settings.anthropic_api_key else "extractive",
        "api_keys_required": False,
    }


@app.get("/platform-services")
def platform_services() -> list[dict]:
    return load_registry()


@app.get("/actions/scaffold-link")
def scaffold_link(service_name: str, description: str = "") -> dict:
    try:
        return build_workflow_dispatch(service_name, description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    result = await handle_message(
        body.message.strip(),
        store,
        session_store=session_store,
        thread_id=body.thread_id,
    )
    return ChatResponse(**result)


@app.post("/actions/confirm")
async def confirm_action(body: ConfirmRequest) -> dict:
    draft = body.draft or {}
    action = draft.get("action")
    if not action:
        raise HTTPException(status_code=400, detail="Missing draft action")

    if action == "scaffold_service":
        return confirm_scaffold_draft(draft)

    if action == "request_sandbox":
        issue_url = (
            f"https://github.com/{settings.github_repo}/issues/new"
            "?template=sandbox-request.md"
            f"&title={draft.get('purpose', 'Sandbox request')[:80]}"
        )
        return {
            "status": "issue_template",
            "message": "Open the GitHub issue template to file your sandbox request.",
            "issue_url": issue_url,
        }

    raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
