from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from portal_assistant.config import settings
from portal_assistant.user_context import UserContext

AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type TEXT NOT NULL,
    thread_id TEXT,
    actor_subject TEXT,
    actor_email TEXT,
    tool_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS audit_events_created_at_idx ON audit_events (created_at DESC);
CREATE INDEX IF NOT EXISTS audit_events_thread_id_idx ON audit_events (thread_id);
CREATE INDEX IF NOT EXISTS audit_events_event_type_idx ON audit_events (event_type);
"""

EVENT_CHAT_PROMPT = "chat_prompt"
EVENT_TOOL_INVOKE = "tool_invoke"
EVENT_RETRIEVAL = "retrieval"
EVENT_CONFIRM = "confirm_action"


@dataclass(frozen=True)
class AuditActor:
    subject: str = ""
    email: str = ""

    @classmethod
    def from_user(cls, user: UserContext | None) -> AuditActor:
        if user is None:
            return cls()
        return cls(subject=user.subject, email=user.email)


class AuditLogStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(AUDIT_SCHEMA)
            conn.commit()

    def record(
        self,
        event_type: str,
        *,
        payload: dict[str, Any] | None = None,
        thread_id: str | None = None,
        actor: AuditActor | None = None,
        tool_id: str | None = None,
    ) -> None:
        if not settings.audit_log_enabled:
            return
        act = actor or AuditActor()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (
                    event_type, thread_id, actor_subject, actor_email, tool_id, payload
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    event_type,
                    thread_id,
                    act.subject or None,
                    act.email or None,
                    tool_id,
                    Jsonb(payload or {}),
                ),
            )
            conn.commit()

    def query(
        self,
        *,
        limit: int = 50,
        thread_id: str | None = None,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        with self.connect() as conn:
            if thread_id and event_type:
                rows = conn.execute(
                    """
                    SELECT id, created_at, event_type, thread_id, actor_subject, actor_email,
                           tool_id, payload
                    FROM audit_events
                    WHERE thread_id = %s AND event_type = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (thread_id, event_type, limit),
                ).fetchall()
            elif thread_id:
                rows = conn.execute(
                    """
                    SELECT id, created_at, event_type, thread_id, actor_subject, actor_email,
                           tool_id, payload
                    FROM audit_events
                    WHERE thread_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (thread_id, limit),
                ).fetchall()
            elif event_type:
                rows = conn.execute(
                    """
                    SELECT id, created_at, event_type, thread_id, actor_subject, actor_email,
                           tool_id, payload
                    FROM audit_events
                    WHERE event_type = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (event_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, created_at, event_type, thread_id, actor_subject, actor_email,
                           tool_id, payload
                    FROM audit_events
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                ).fetchall()
        return [dict(cast(dict[str, Any], row)) for row in rows]

    def count(self) -> int:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM audit_events").fetchone()
        if not row:
            return 0
        return int(cast(dict[str, Any], row)["c"])
