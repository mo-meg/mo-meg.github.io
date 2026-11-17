"""Plain data types shared across ingestion, retrieval, and generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceDocument:
    """A document ready for ingestion (already extracted and cleaned)."""

    source_id: str  # stable identity, e.g. "file:projects/multimodal-rag-moodle.md" or "github:owner/repo"
    title: str
    source_label: str  # human-facing citation label, e.g. "Professional CV"
    category: str
    text: str
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    index: int
    text: str
    heading: str = ""


@dataclass(slots=True)
class StoredChunk:
    document_id: int
    index: int
    text: str
    heading: str
    content_hash: str
    embedding: list[float]


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: int
    document_id: int
    source_id: str
    title: str
    source_label: str
    category: str
    url: str | None
    heading: str
    text: str
    similarity: float
    score: float = 0.0  # fused ranking score


@dataclass(slots=True)
class Citation:
    id: str  # "S1"
    title: str
    label: str
    url: str | None
    category: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "label": self.label, "url": self.url, "category": self.category}
