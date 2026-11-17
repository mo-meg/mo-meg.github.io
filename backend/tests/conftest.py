from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings
from app.embeddings import FakeEmbedder
from app.ingestion.loaders import discover, load_file
from app.ingestion.pipeline import Ingestor
from app.llm import FakeGenerator
from app.models import SourceDocument
from app.services import Services, build_services
from app.vectorstore import InMemoryVectorStore

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        ai_provider="fake",
        allowed_origins=["https://example.github.io"],
        chunk_size=800,
        chunk_overlap=120,
        retrieval_min_score=0.15,
        rate_limit_per_minute=100,
        rate_limit_per_day=1000,
        daily_request_budget=10_000,
        _env_file=None,  # type: ignore[call-arg]
    )


def make_doc(
    source_id: str, text: str, *, category: str = "projects", title: str | None = None, url: str | None = None
):
    return SourceDocument(
        source_id=source_id,
        title=title or source_id,
        source_label=f"{title or source_id} label",
        category=category,
        text=text,
        url=url,
    )


@pytest.fixture
def store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder(dim=256)


@pytest.fixture
async def kb(store: InMemoryVectorStore, embedder: FakeEmbedder, settings: Settings) -> InMemoryVectorStore:
    """The real knowledge base folder, ingested into the in-memory store."""
    ingestor = Ingestor(store, embedder, settings.chunk_size, settings.chunk_overlap)
    docs = [load_file(p, KNOWLEDGE_DIR) for p in discover(KNOWLEDGE_DIR)]
    report = await ingestor.ingest_many(docs)
    assert not report.errors, report.errors
    return store


@pytest.fixture
def generator() -> FakeGenerator:
    return FakeGenerator()


@pytest.fixture
def services(settings: Settings, kb: InMemoryVectorStore, embedder: FakeEmbedder, generator: FakeGenerator) -> Services:
    return build_services(settings, kb, embedder, generator)


@pytest.fixture
def client(settings: Settings, services: Services) -> Iterator[TestClient]:
    app = create_app(settings, services)
    with TestClient(app) as c:
        yield c


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        ev, data = "message", ""
        for line in block.split("\n"):
            if line.startswith("event:"):
                ev = line[6:].strip()
            elif line.startswith("data:"):
                data += line[5:].strip()
        if data:
            events.append((ev, json.loads(data)))
    return events
