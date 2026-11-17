"""Vector storage: PostgreSQL + pgvector in production, an in-memory implementation for tests."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Protocol

from pgvector import Vector
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.models import RetrievedChunk, SourceDocument, StoredChunk


@dataclass(slots=True)
class DocumentRecord:
    id: int
    source_id: str
    title: str
    source_label: str
    category: str
    url: str | None
    content_hash: str
    embedding_model: str
    chunk_count: int
    metadata: dict[str, Any]


class VectorStore(Protocol):
    async def get_document(self, source_id: str) -> DocumentRecord | None: ...
    async def find_by_text_hash(self, text_hash: str) -> str | None: ...
    async def replace_document(
        self, doc: SourceDocument, content_hash: str, embedding_model: str, chunks: list[StoredChunk]
    ) -> int: ...
    async def delete_document(self, source_id: str) -> bool: ...
    async def list_documents(self) -> list[DocumentRecord]: ...
    async def vector_search(
        self, embedding: list[float], limit: int, categories: list[str] | None
    ) -> list[RetrievedChunk]: ...
    async def keyword_search(
        self, query: str, embedding: list[float], limit: int, categories: list[str] | None
    ) -> list[RetrievedChunk]: ...
    async def stats(self) -> dict[str, int]: ...


_SELECT_CHUNK = """
    c.id AS chunk_id, c.document_id, d.source_id, d.title, d.source_label, d.category, d.url,
    c.heading, c.content
"""


def _row_to_chunk(r: dict[str, Any]) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=r["chunk_id"],
        document_id=r["document_id"],
        source_id=r["source_id"],
        title=r["title"],
        source_label=r["source_label"],
        category=r["category"],
        url=r["url"],
        heading=r["heading"] or "",
        text=r["content"],
        similarity=float(r["similarity"]),
    )


class PgVectorStore:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def get_document(self, source_id: str) -> DocumentRecord | None:
        async with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """SELECT d.*, (SELECT count(*) FROM chunks c WHERE c.document_id = d.id) AS chunk_count
                   FROM documents d WHERE source_id = %s""",
                (source_id,),
            )
            r = await cur.fetchone()
        return _doc(r) if r else None

    async def find_by_text_hash(self, text_hash: str) -> str | None:
        async with self._pool.connection() as conn:
            cur = await conn.execute(
                "SELECT source_id FROM documents WHERE metadata->>'text_hash' = %s LIMIT 1", (text_hash,)
            )
            r = await cur.fetchone()
        return r[0] if r else None

    async def replace_document(
        self, doc: SourceDocument, content_hash: str, embedding_model: str, chunks: list[StoredChunk]
    ) -> int:
        """Insert or update a document and atomically replace all of its chunks."""
        async with self._pool.connection() as conn, conn.transaction():
            cur = await conn.execute(
                """INSERT INTO documents (source_id, title, source_label, category, url, content_hash,
                                          embedding_model, metadata)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (source_id) DO UPDATE SET
                     title = EXCLUDED.title, source_label = EXCLUDED.source_label,
                     category = EXCLUDED.category, url = EXCLUDED.url,
                     content_hash = EXCLUDED.content_hash, embedding_model = EXCLUDED.embedding_model,
                     metadata = EXCLUDED.metadata, updated_at = now()
                   RETURNING id""",
                (
                    doc.source_id,
                    doc.title,
                    doc.source_label,
                    doc.category,
                    doc.url,
                    content_hash,
                    embedding_model,
                    json.dumps(doc.metadata, default=str),
                ),
            )
            row = await cur.fetchone()
            assert row is not None
            doc_id = int(row[0])
            await conn.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))
            async with conn.cursor() as c:
                await c.executemany(
                    """INSERT INTO chunks (document_id, chunk_index, heading, content, content_hash, embedding)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    [
                        (
                            doc_id,
                            ch.index,
                            ch.heading,
                            ch.text,
                            ch.content_hash,
                            Vector(ch.embedding),
                        )
                        for ch in chunks
                    ],
                )
        return doc_id

    async def delete_document(self, source_id: str) -> bool:
        async with self._pool.connection() as conn:
            cur = await conn.execute("DELETE FROM documents WHERE source_id = %s", (source_id,))
            return cur.rowcount > 0

    async def list_documents(self) -> list[DocumentRecord]:
        async with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """SELECT d.*, count(c.id) AS chunk_count FROM documents d
                   LEFT JOIN chunks c ON c.document_id = d.id GROUP BY d.id ORDER BY d.category, d.source_id"""
            )
            return [_doc(r) for r in await cur.fetchall()]

    async def vector_search(
        self, embedding: list[float], limit: int, categories: list[str] | None
    ) -> list[RetrievedChunk]:
        q = Vector(embedding)
        async with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"""SELECT {_SELECT_CHUNK}, 1 - (c.embedding <=> %(q)s) AS similarity
                    FROM chunks c JOIN documents d ON d.id = c.document_id
                    WHERE %(cats)s::text[] IS NULL OR d.category = ANY(%(cats)s)
                    ORDER BY c.embedding <=> %(q)s
                    LIMIT %(n)s""",
                {"q": q, "cats": categories, "n": limit},
            )
            return [_row_to_chunk(r) for r in await cur.fetchall()]

    async def keyword_search(
        self, query: str, embedding: list[float], limit: int, categories: list[str] | None
    ) -> list[RetrievedChunk]:
        # OR-combine the query terms (websearch syntax is AND by default, too strict for questions).
        terms = [t for t in re.findall(r"[\w-]{3,}", query.lower()) if not t.isdigit()][:16]
        if not terms:
            return []
        q = Vector(embedding)
        async with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"""WITH q AS (SELECT websearch_to_tsquery('english', %(text)s) AS tsq)
                    SELECT {_SELECT_CHUNK}, 1 - (c.embedding <=> %(q)s) AS similarity
                    FROM chunks c JOIN documents d ON d.id = c.document_id, q
                    WHERE c.tsv @@ q.tsq AND (%(cats)s::text[] IS NULL OR d.category = ANY(%(cats)s))
                    ORDER BY ts_rank_cd(c.tsv, q.tsq) DESC
                    LIMIT %(n)s""",
                {"text": " or ".join(terms), "q": q, "cats": categories, "n": limit},
            )
            return [_row_to_chunk(r) for r in await cur.fetchall()]

    async def stats(self) -> dict[str, int]:
        async with self._pool.connection() as conn:
            cur = await conn.execute("SELECT (SELECT count(*) FROM documents), (SELECT count(*) FROM chunks)")
            r = await cur.fetchone()
        return {"documents": int(r[0]), "chunks": int(r[1])} if r else {"documents": 0, "chunks": 0}


def _doc(r: dict[str, Any]) -> DocumentRecord:
    meta = r.get("metadata") or {}
    if isinstance(meta, str):
        meta = json.loads(meta)
    return DocumentRecord(
        id=r["id"],
        source_id=r["source_id"],
        title=r["title"],
        source_label=r["source_label"],
        category=r["category"],
        url=r["url"],
        content_hash=r["content_hash"],
        embedding_model=r["embedding_model"],
        chunk_count=int(r.get("chunk_count") or 0),
        metadata=meta,
    )


class InMemoryVectorStore:
    """Behaviourally equivalent store used by unit tests (no database needed)."""

    def __init__(self) -> None:
        self.docs: dict[str, tuple[DocumentRecord, SourceDocument]] = {}
        self.chunks: dict[int, list[StoredChunk]] = {}
        self._next = 1

    async def get_document(self, source_id: str) -> DocumentRecord | None:
        d = self.docs.get(source_id)
        return d[0] if d else None

    async def find_by_text_hash(self, text_hash: str) -> str | None:
        return next((sid for sid, (rec, _) in self.docs.items() if rec.metadata.get("text_hash") == text_hash), None)

    async def replace_document(
        self, doc: SourceDocument, content_hash: str, embedding_model: str, chunks: list[StoredChunk]
    ) -> int:
        existing = self.docs.get(doc.source_id)
        doc_id = existing[0].id if existing else self._next
        if not existing:
            self._next += 1
        rec = DocumentRecord(
            doc_id,
            doc.source_id,
            doc.title,
            doc.source_label,
            doc.category,
            doc.url,
            content_hash,
            embedding_model,
            len(chunks),
            dict(doc.metadata),
        )
        self.docs[doc.source_id] = (rec, doc)
        self.chunks[doc_id] = [
            StoredChunk(doc_id, c.index, c.text, c.heading, c.content_hash, c.embedding) for c in chunks
        ]
        return doc_id

    async def delete_document(self, source_id: str) -> bool:
        d = self.docs.pop(source_id, None)
        if d:
            self.chunks.pop(d[0].id, None)
        return d is not None

    async def list_documents(self) -> list[DocumentRecord]:
        return [rec for rec, _ in self.docs.values()]

    def _all(self, categories: list[str] | None, embedding: list[float]) -> list[RetrievedChunk]:
        out = []
        for rec, _ in self.docs.values():
            if categories and rec.category not in categories:
                continue
            for c in self.chunks.get(rec.id, []):
                sim = sum(a * b for a, b in zip(embedding, c.embedding, strict=True))
                out.append(
                    RetrievedChunk(
                        chunk_id=rec.id * 10_000 + c.index,
                        document_id=rec.id,
                        source_id=rec.source_id,
                        title=rec.title,
                        source_label=rec.source_label,
                        category=rec.category,
                        url=rec.url,
                        heading=c.heading,
                        text=c.text,
                        similarity=sim,
                    )
                )
        return out

    async def vector_search(
        self, embedding: list[float], limit: int, categories: list[str] | None
    ) -> list[RetrievedChunk]:
        return sorted(self._all(categories, embedding), key=lambda c: -c.similarity)[:limit]

    async def keyword_search(
        self, query: str, embedding: list[float], limit: int, categories: list[str] | None
    ) -> list[RetrievedChunk]:
        terms = {t for t in re.findall(r"\w{4,}", query.lower())}
        if not terms:
            return []
        scored = []
        for c in self._all(categories, embedding):
            words = set(re.findall(r"\w{4,}", c.text.lower()))
            hits = len(terms & words)
            if hits:
                scored.append((hits / math.sqrt(len(words) + 1), c))
        return [c for _, c in sorted(scored, key=lambda x: -x[0])[:limit]]

    async def stats(self) -> dict[str, int]:
        return {"documents": len(self.docs), "chunks": sum(len(v) for v in self.chunks.values())}
