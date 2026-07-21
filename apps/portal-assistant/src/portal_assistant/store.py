from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from portal_assistant.chunking import Chunk

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'public',
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(title, '') || ' ' || content)) STORED,
    UNIQUE (source, title, content)
);

CREATE INDEX IF NOT EXISTS documents_content_tsv_idx ON documents USING GIN (content_tsv);
"""


class DocumentStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(SCHEMA)
            conn.commit()

    def upsert_chunks(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        with self.connect() as conn:
            with conn.cursor() as cur:
                for chunk in chunks:
                    cur.execute(
                        """
                        INSERT INTO documents (source, title, content, visibility)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (source, title, content) DO NOTHING
                        """,
                        (chunk.source, chunk.title, chunk.content, chunk.visibility),
                    )
            conn.commit()
        return len(chunks)

    def search(self, query: str, limit: int = 6) -> list[dict]:
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
        return list(rows)

    def count(self) -> int:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()
            return int(row["c"]) if row else 0
