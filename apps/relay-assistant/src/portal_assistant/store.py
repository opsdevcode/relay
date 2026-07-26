from __future__ import annotations

from typing import Any, cast

import psycopg
from psycopg.rows import dict_row

from portal_assistant.chunking import Chunk
from portal_assistant.config import settings
from portal_assistant.embeddings import embed_text, to_vector_literal
from portal_assistant.retrieval import reciprocal_rank_fusion
from portal_assistant.retrieval_abac import AccessMode, resolve_access_mode
from portal_assistant.user_context import UserContext

_FTS_PUBLIC = """
    SELECT source, title, content,
           ts_rank(content_tsv, websearch_to_tsquery('english', %s)) AS rank
    FROM documents
    WHERE content_tsv @@ websearch_to_tsquery('english', %s)
    ORDER BY rank DESC
    LIMIT %s
    """

_FTS_ABAC_PUBLIC = """
    SELECT source, title, content,
           ts_rank(content_tsv, websearch_to_tsquery('english', %s)) AS rank
    FROM documents
    WHERE content_tsv @@ websearch_to_tsquery('english', %s)
      AND visibility = 'public'
    ORDER BY rank DESC
    LIMIT %s
    """

_FTS_ABAC_AUTH = """
    SELECT source, title, content,
           ts_rank(content_tsv, websearch_to_tsquery('english', %s)) AS rank
    FROM documents
    WHERE content_tsv @@ websearch_to_tsquery('english', %s)
      AND (visibility = 'public' OR visibility = 'internal')
    ORDER BY rank DESC
    LIMIT %s
    """

_FTS_ABAC_PRINCIPALS = """
    SELECT source, title, content,
           ts_rank(content_tsv, websearch_to_tsquery('english', %s)) AS rank
    FROM documents
    WHERE content_tsv @@ websearch_to_tsquery('english', %s)
      AND (
        visibility = 'public'
        OR visibility = 'internal'
        OR (visibility = 'restricted' AND doc_owner = ANY(%s))
        OR (visibility = 'restricted' AND allowed_groups && %s::text[])
      )
    ORDER BY rank DESC
    LIMIT %s
    """

_VEC_PUBLIC = """
    SELECT source, title, content,
           (1 - (embedding <=> %s::vector)) AS vec_score
    FROM documents
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT %s
    """

_VEC_ABAC_PUBLIC = """
    SELECT source, title, content,
           (1 - (embedding <=> %s::vector)) AS vec_score
    FROM documents
    WHERE embedding IS NOT NULL
      AND visibility = 'public'
    ORDER BY embedding <=> %s::vector
    LIMIT %s
    """

_VEC_ABAC_AUTH = """
    SELECT source, title, content,
           (1 - (embedding <=> %s::vector)) AS vec_score
    FROM documents
    WHERE embedding IS NOT NULL
      AND (visibility = 'public' OR visibility = 'internal')
    ORDER BY embedding <=> %s::vector
    LIMIT %s
    """

_VEC_ABAC_PRINCIPALS = """
    SELECT source, title, content,
           (1 - (embedding <=> %s::vector)) AS vec_score
    FROM documents
    WHERE embedding IS NOT NULL
      AND (
        visibility = 'public'
        OR visibility = 'internal'
        OR (visibility = 'restricted' AND doc_owner = ANY(%s))
        OR (visibility = 'restricted' AND allowed_groups && %s::text[])
      )
    ORDER BY embedding <=> %s::vector
    LIMIT %s
    """


SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'public',
    content_tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || content)
    ) STORED,
    UNIQUE (source, title, content)
);

CREATE INDEX IF NOT EXISTS documents_content_tsv_idx ON documents USING GIN (content_tsv);

ALTER TABLE documents ADD COLUMN IF NOT EXISTS embedding vector(384);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS doc_owner TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS doc_updated TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS allowed_groups TEXT[] NOT NULL DEFAULT '{}';
"""


def _search_params(
    mode: AccessMode, query_or_vector: Any, limit: int, access_params: list[Any]
) -> list[Any]:
    if mode is AccessMode.PRINCIPALS:
        return [query_or_vector, query_or_vector, *access_params, limit]
    if mode in (AccessMode.NONE, AccessMode.PUBLIC_ONLY, AccessMode.AUTHENTICATED):
        return [query_or_vector, query_or_vector, limit]
    return [query_or_vector, query_or_vector, limit]


class DocumentStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(SCHEMA)
            conn.commit()

    def upsert_chunks(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        dims = settings.embedding_dimensions
        with self.connect() as conn:
            with conn.cursor() as cur:
                for chunk in chunks:
                    text = f"{chunk.title}\n{chunk.content}"
                    vector = to_vector_literal(embed_text(text, dimensions=dims))
                    groups = list(chunk.allowed_groups) if chunk.allowed_groups else []
                    cur.execute(
                        """
                        INSERT INTO documents (
                            source, title, content, visibility, embedding,
                            doc_owner, doc_updated, allowed_groups
                        )
                        VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s)
                        ON CONFLICT (source, title, content) DO UPDATE SET
                            visibility = EXCLUDED.visibility,
                            embedding = EXCLUDED.embedding,
                            doc_owner = EXCLUDED.doc_owner,
                            doc_updated = EXCLUDED.doc_updated,
                            allowed_groups = EXCLUDED.allowed_groups
                        """,
                        (
                            chunk.source,
                            chunk.title,
                            chunk.content,
                            chunk.visibility,
                            vector,
                            chunk.doc_owner or None,
                            chunk.doc_updated or None,
                            groups,
                        ),
                    )
            conn.commit()
        return len(chunks)

    def _fts_search(
        self, query: str, limit: int, user: UserContext | None = None
    ) -> list[dict[str, Any]]:
        mode, access_params = resolve_access_mode(user)
        sql_by_mode = {
            AccessMode.NONE: _FTS_PUBLIC,
            AccessMode.PUBLIC_ONLY: _FTS_ABAC_PUBLIC,
            AccessMode.AUTHENTICATED: _FTS_ABAC_AUTH,
            AccessMode.PRINCIPALS: _FTS_ABAC_PRINCIPALS,
        }
        sql = sql_by_mode[mode]
        params = _search_params(mode, query, limit, access_params)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return cast(list[dict[str, Any]], list(rows))

    def _vector_search(
        self, query: str, limit: int, user: UserContext | None = None
    ) -> list[dict[str, Any]]:
        dims = settings.embedding_dimensions
        vector = to_vector_literal(embed_text(query, dimensions=dims))
        mode, access_params = resolve_access_mode(user)
        sql_by_mode = {
            AccessMode.NONE: _VEC_PUBLIC,
            AccessMode.PUBLIC_ONLY: _VEC_ABAC_PUBLIC,
            AccessMode.AUTHENTICATED: _VEC_ABAC_AUTH,
            AccessMode.PRINCIPALS: _VEC_ABAC_PRINCIPALS,
        }
        sql = sql_by_mode[mode]
        if mode is AccessMode.PRINCIPALS:
            params: list[Any] = [vector, *access_params, vector, limit]
        else:
            params = [vector, vector, limit]
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return cast(list[dict[str, Any]], list(rows))

    def _embeddings_available(self) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT EXISTS (SELECT 1 FROM documents WHERE embedding IS NOT NULL LIMIT 1) AS ok"
            ).fetchone()
        if not row:
            return False
        return bool(cast(dict[str, Any], row)["ok"])

    def search(
        self, query: str, limit: int = 6, user: UserContext | None = None
    ) -> list[dict[str, Any]]:
        if not settings.hybrid_search_enabled or not self._embeddings_available():
            return self._fts_search(query, limit, user=user)[:limit]

        fetch = max(limit * 4, 12)
        fts_hits = self._fts_search(query, fetch, user=user)
        vec_hits = self._vector_search(query, fetch, user=user)
        if not vec_hits:
            return fts_hits[:limit]
        if not fts_hits:
            return vec_hits[:limit]
        return reciprocal_rank_fusion([fts_hits, vec_hits], limit=limit)

    def count(self) -> int:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()
            if not row:
                return 0
            return int(cast(dict[str, Any], row)["c"])

    def delete_all(self) -> int:
        """Remove every document row. Used by full corpus reindex."""
        with self.connect() as conn:
            row = conn.execute("DELETE FROM documents RETURNING id").fetchall()
            conn.commit()
        return len(list(row))

    def needs_embedding_backfill(self) -> bool:
        if not settings.hybrid_search_enabled or self.count() == 0:
            return False
        return not self._embeddings_available()

    def retrieval_mode(self) -> str:
        if settings.hybrid_search_enabled and self._embeddings_available():
            return "hybrid"
        return "fts"
