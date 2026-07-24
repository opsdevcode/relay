from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Protocol

from redis import Redis

logger = logging.getLogger(__name__)

REFINE_SERVICE_NAME = re.compile(
    r"(?i)^(?:please\s+)?(?:call|name|make)\s+it\s+(.+)$",
)


class SessionBackend(Protocol):
    def get_turns(self, thread_id: str) -> list[dict[str, Any]]: ...

    def save_turns(self, thread_id: str, turns: list[dict[str, Any]]) -> None: ...


class RedisSessionBackend:
    def __init__(
        self,
        client: Redis,
        *,
        key_prefix: str = "relay:thread:",
        ttl_seconds: int = 86_400,
    ) -> None:
        self._client = client
        self._prefix = key_prefix
        self._ttl = ttl_seconds

    def _key(self, thread_id: str) -> str:
        return f"{self._prefix}{thread_id}"

    def get_turns(self, thread_id: str) -> list[dict[str, Any]]:
        raw = self._client.get(self._key(thread_id))
        if not raw:
            return []
        data = json.loads(raw)
        return data if isinstance(data, list) else []

    def save_turns(self, thread_id: str, turns: list[dict[str, Any]]) -> None:
        self._client.set(
            self._key(thread_id),
            json.dumps(turns),
            ex=self._ttl,
        )


class MemorySessionBackend:
    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, Any]]] = {}

    def get_turns(self, thread_id: str) -> list[dict[str, Any]]:
        return list(self._data.get(thread_id, []))

    def save_turns(self, thread_id: str, turns: list[dict[str, Any]]) -> None:
        self._data[thread_id] = list(turns)


class SessionStore:
    def __init__(
        self,
        backend: SessionBackend,
        *,
        max_turns: int = 20,
    ) -> None:
        self._backend = backend
        self._max_turns = max_turns

    @classmethod
    def from_redis_url(
        cls,
        redis_url: str,
        *,
        ttl_seconds: int = 86_400,
        max_turns: int = 20,
    ) -> SessionStore:
        client = Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        backend = RedisSessionBackend(client, ttl_seconds=ttl_seconds)
        return cls(backend, max_turns=max_turns)

    @classmethod
    def in_memory(cls, *, max_turns: int = 20) -> SessionStore:
        return cls(MemorySessionBackend(), max_turns=max_turns)

    def ensure_thread_id(self, thread_id: str | None) -> str:
        if thread_id and thread_id.strip():
            return thread_id.strip()
        return str(uuid.uuid4())

    def get_turns(self, thread_id: str) -> list[dict[str, Any]]:
        return self._backend.get_turns(thread_id)

    def append_exchange(
        self,
        thread_id: str,
        *,
        user_message: str,
        assistant_message: str,
        meta: dict[str, Any],
    ) -> None:
        turns = self.get_turns(thread_id)
        turns.append({"role": "user", "content": user_message})
        turns.append(
            {
                "role": "assistant",
                "content": assistant_message,
                "meta": meta,
            }
        )
        max_messages = self._max_turns * 2
        if len(turns) > max_messages:
            turns = turns[-max_messages:]
        self._backend.save_turns(thread_id, turns)


def last_assistant_meta(turns: list[dict[str, Any]]) -> dict[str, Any]:
    for turn in reversed(turns):
        if turn.get("role") == "assistant":
            meta = turn.get("meta")
            return meta if isinstance(meta, dict) else {}
    return {}


def apply_follow_up_refinement(message: str, turns: list[dict[str, Any]]) -> str:
    """Rewrite short follow-ups after a scaffold draft (e.g. 'call it payments-api')."""
    match = REFINE_SERVICE_NAME.match(message.strip())
    if not match:
        return message

    raw_name = match.group(1).strip().strip("\"'").rstrip(".")
    if not raw_name:
        return message

    meta = last_assistant_meta(turns)
    draft_raw = meta.get("draft")
    draft = draft_raw if isinstance(draft_raw, dict) else {}
    if meta.get("tool") == "scaffold_service" or draft.get("action") == "scaffold_service":
        return f"Create a new service called {raw_name}"

    return message


def create_session_store(
    redis_url: str,
    *,
    ttl_seconds: int = 86_400,
    max_turns: int = 20,
) -> SessionStore:
    try:
        return SessionStore.from_redis_url(
            redis_url,
            ttl_seconds=ttl_seconds,
            max_turns=max_turns,
        )
    except Exception:
        logger.warning("Redis unavailable for sessions; using in-memory store", exc_info=True)
        return SessionStore.in_memory(max_turns=max_turns)
