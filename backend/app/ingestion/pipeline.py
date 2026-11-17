"""Ingestion: document → chunks → embeddings → vector store, incrementally and idempotently."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Literal

from app.embeddings import Embedder
from app.ingestion.chunking import chunk_text
from app.logging_setup import log
from app.models import SourceDocument, StoredChunk
from app.vectorstore import VectorStore

logger = logging.getLogger(__name__)

Outcome = Literal["created", "updated", "unchanged", "duplicate", "empty"]


@dataclass
class IngestReport:
    results: dict[str, Outcome] = field(default_factory=dict)
    removed: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for o in self.results.values():
            out[o] = out.get(o, 0) + 1
        out["removed"] = len(self.removed)
        out["errors"] = len(self.errors)
        return out


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Ingestor:
    def __init__(self, store: VectorStore, embedder: Embedder, chunk_size: int, chunk_overlap: int) -> None:
        self.store = store
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def fingerprint(self, doc: SourceDocument) -> str:
        """Changes whenever content, citation metadata, or chunking parameters change."""
        basis = json.dumps(
            {
                "text": doc.text,
                "title": doc.title,
                "label": doc.source_label,
                "category": doc.category,
                "url": doc.url,
                "chunking": [self.chunk_size, self.chunk_overlap],
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return sha256(basis)

    async def ingest(self, doc: SourceDocument, *, force: bool = False) -> Outcome:
        fp = self.fingerprint(doc)
        existing = await self.store.get_document(doc.source_id)

        if (
            existing
            and not force
            and existing.content_hash == fp
            and existing.embedding_model == self.embedder.model_name
        ):
            return "unchanged"

        # Identical content already indexed under another id → skip, don't double-count evidence.
        content_hash = sha256(" ".join(doc.text.split()))
        dup = await self.store.find_by_text_hash(content_hash)
        if dup and dup != doc.source_id:
            log(logger, logging.WARNING, "duplicate_document", source_id=doc.source_id, duplicate_of=dup)
            return "duplicate"

        chunks = chunk_text(doc.text, self.chunk_size, self.chunk_overlap)
        if not chunks:
            return "empty"

        # Enrich each chunk with its document title and heading path before embedding:
        # short chunks then still carry their context ("Prolumios > Responsibilities").
        enriched = [f"{c.heading}\n{c.text}" if c.heading else c.text for c in chunks]
        vectors = await self.embedder.embed_documents(enriched, titles=[doc.title] * len(chunks))

        stored = [
            StoredChunk(
                document_id=0, index=c.index, text=c.text, heading=c.heading, content_hash=sha256(c.text), embedding=v
            )
            for c, v in zip(chunks, vectors, strict=True)
        ]
        doc.metadata["text_hash"] = content_hash
        await self.store.replace_document(doc, fp, self.embedder.model_name, stored)
        outcome: Outcome = "updated" if existing else "created"
        log(logger, logging.INFO, "document_ingested", source_id=doc.source_id, outcome=outcome, chunks=len(stored))
        return outcome

    async def ingest_many(self, docs: list[SourceDocument], *, force: bool = False) -> IngestReport:
        report = IngestReport()
        for d in docs:
            try:
                report.results[d.source_id] = await self.ingest(d, force=force)
            except Exception as e:  # noqa: BLE001 — continue with the remaining documents
                report.errors[d.source_id] = f"{type(e).__name__}: {e}"
                log(logger, logging.ERROR, "ingest_failed", source_id=d.source_id, error=str(e))
        return report

    async def prune(self, keep_source_ids: set[str], prefix: str = "file:") -> list[str]:
        """Remove documents with the given prefix that no longer exist in the source set."""
        removed = []
        for rec in await self.store.list_documents():
            if rec.source_id.startswith(prefix) and rec.source_id not in keep_source_ids:
                await self.store.delete_document(rec.source_id)
                removed.append(rec.source_id)
        return removed
