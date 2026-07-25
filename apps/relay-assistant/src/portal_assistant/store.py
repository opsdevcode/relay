from __future__ import annotations

from typing import Any, cast

import psycopg
from psycopg.rows import dict_row

from portal_assistant.chunking import Chunk
from portal_assistant.config import settings
from portal_assistant.embeddings import embed_text, to_vector_literal
from portal_assistant.retrieval import reciprocal_rank_fusion

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
"""


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
                    cur.execute(
                        """
                        INSERT INTO documents (
                            source, title, content, visibility, embedding, doc_owner, doc_updated
                        )
                        VALUES (%s, %s, %s, %s, %s::vector, %s, %s)
                        ON CONFLICT (source, title, content) DO UPDATE SET
                            visibility = EXCLUDED.visibility,
                            embedding = EXCLUDED.embedding,
                            doc_owner = EXCLUDED.doc_owner,
                            doc_updated = EXCLUDED.doc_updated
                        """,
                        (
                            chunk.source,
                            chunk.title,
                            chunk.content,
                            chunk.visibility,
                            vector,
                            chunk.doc_owner or None,
                            chunk.doc_updated or None,
                        ),
                    )
            conn.commit()
        return len(chunks)

    def _fts_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT source, title, content,
                       ts_rank(content_tsv, websearch_to_tsquery('english', %s)) AS rank
                FROM documents
                WHERE content_tsv @@ websearch_to_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT %s
                """,
                (query, query, limit),
            ).fetchall()
        return cast(list[dict[str, Any]], list(rows))

    def _vector_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        dims = settings.embedding_dimensions
        vector = to_vector_literal(embed_text(query, dimensions=dims))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT source, title, content,
                       (1 - (embedding <=> %s::vector)) AS vec_score
                FROM documents
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vector, vector, limit),
            ).fetchall()
        return cast(list[dict[str, Any]], list(rows))

    def _embeddings_available(self) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT EXISTS (SELECT 1 FROM documents WHERE embedding IS NOT NULL LIMIT 1) AS ok"
            ).fetchone()
        if not row:
            return False
        return bool(cast(dict[str, Any], row)["ok"])

    def search(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        if not settings.hybrid_search_enabled or not self._embeddings_available():
            return self._fts_search(query, limit)[:limit]

        fetch = max(limit * 4, 12)
        fts_hits = self._fts_search(query, fetch)
        vec_hits = self._vector_search(query, fetch)
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
