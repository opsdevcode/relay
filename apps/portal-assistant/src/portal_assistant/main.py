from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from portal_assistant.agent import handle_message
from portal_assistant.config import settings
from portal_assistant.scaffold import build_workflow_dispatch, confirm_scaffold_draft
from portal_assistant.store import DocumentStore
from portal_assistant.tools import draft_sandbox_request, load_registry


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict]
    draft: dict | None = None


class ConfirmRequest(BaseModel):
    draft: dict


store = DocumentStore(settings.database_url)


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init_schema()
    yield


app = FastAPI(title="Portal Assistant", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "documents": store.count()}


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
    result = await handle_message(body.message.strip(), store)
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
