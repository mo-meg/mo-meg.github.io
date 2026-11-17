"""Integration tests against a real PostgreSQL + pgvector. Skipped unless TEST_DATABASE_URL is set:

docker compose up -d db
    TEST_DATABASE_URL=postgresql://portfolio:portfolio@localhost:5432/portfolio \
        uv run pytest tests/test_pgvector_integration.py
"""

import os

import pytest

from app.db import create_pool, migrate
from app.embeddings import FakeEmbedder
from app.ingestion.loaders import discover, load_file
from app.ingestion.pipeline import Ingestor
from app.retrieval import Retriever
from app.vectorstore import PgVectorStore
from tests.conftest import KNOWLEDGE_DIR, make_doc

DSN = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="TEST_DATABASE_URL not set")
DIM = 768


@pytest.fixture
async def pg():
    assert DSN
    await migrate(DSN, DIM)
    pool = await create_pool(DSN)
    async with pool.connection() as conn:
        await conn.execute("TRUNCATE documents CASCADE")
    yield PgVectorStore(pool)
    await pool.close()


async def test_roundtrip_and_hybrid_search(pg):
    emb = FakeEmbedder(DIM)
    ing = Ingestor(pg, emb, 800, 120)
    docs = [load_file(p, KNOWLEDGE_DIR) for p in discover(KNOWLEDGE_DIR)]
    report = await ing.ingest_many(docs)
    assert not report.errors
    stats = await pg.stats()
    assert stats["documents"] == len(docs) and stats["chunks"] >= len(docs)

    # Second run is a no-op.
    report2 = await ing.ingest_many(docs)
    assert set(report2.results.values()) == {"unchanged"}

    r = Retriever(pg, emb, top_k=4, min_score=0.15)
    res = await r.retrieve("speaker diarization Whisper sales conversations CRM")
    assert res[0].source_id == "file:experience/prolumios.md"

    kw = await pg.keyword_search("pgvector Celery", await emb.embed_query("pgvector Celery"), 5, None)
    assert kw and any("pgvector" in c.text for c in kw)

    only_edu = await r.retrieve("degree university", categories=["education"])
    assert all(c.category == "education" for c in only_edu)


async def test_update_and_delete(pg):
    emb = FakeEmbedder(DIM)
    ing = Ingestor(pg, emb, 800, 120)
    assert await ing.ingest(make_doc("file:t.md", "first version about vectors")) == "created"
    assert await ing.ingest(make_doc("file:t.md", "second version about vectors")) == "updated"
    rec = await pg.get_document("file:t.md")
    assert rec and rec.chunk_count == 1
    assert await ing.ingest(make_doc("upload:dup.md", "second  version about vectors")) == "duplicate"
    assert await pg.delete_document("file:t.md")
    assert await pg.stats() == {"documents": 0, "chunks": 0}
