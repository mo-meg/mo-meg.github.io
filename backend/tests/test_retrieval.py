from app.models import RetrievedChunk
from app.retrieval import Retriever, rrf_fuse


def _c(cid: int, sim: float) -> RetrievedChunk:
    return RetrievedChunk(cid, cid, f"s{cid}", "t", "l", "projects", None, "", "text", sim)


def test_rrf_fusion_rewards_agreement():
    a = [_c(1, 0.9), _c(2, 0.8), _c(3, 0.7)]
    b = [_c(3, 0.7), _c(1, 0.9)]
    fused = rrf_fuse([a, b])
    assert [c.chunk_id for c in fused][:2] == [1, 3]
    assert fused[0].score > fused[-1].score


def test_multi_turn_query_building(kb, embedder):
    r = Retriever(kb, embedder)
    assert r.build_queries("  What   database? ", []) == ["What database?"]
    qs = r.build_queries("Which database did it use?", ["Explain the Multimodal RAG project"])
    assert qs == ["Which database did it use?", "Explain the Multimodal RAG project Which database did it use?"]


async def test_relevant_document_is_retrieved(kb, embedder):
    r = Retriever(kb, embedder, top_k=4, min_score=0.15)
    results = await r.retrieve("speaker diarization and Whisper for sales conversations in CRM systems")
    assert results
    assert results[0].source_id == "file:experience/prolumios.md"


async def test_follow_up_uses_previous_question(kb, embedder):
    r = Retriever(kb, embedder, top_k=4, min_score=0.15)
    results = await r.retrieve(
        "Which vector database and monitoring did it use?", ["Explain his Multimodal RAG Moodle project"]
    )
    assert any(c.source_id == "file:projects/multimodal-rag-moodle.md" for c in results)


async def test_category_filter(kb, embedder):
    r = Retriever(kb, embedder, top_k=6, min_score=0.0)
    results = await r.retrieve("Mohamed experience", categories=["education"])
    assert results and all(c.category == "education" for c in results)


async def test_unrelated_question_returns_nothing(kb, embedder):
    r = Retriever(kb, embedder, top_k=6, min_score=0.35)
    assert await r.retrieve("zebra pancake recipe xylophone") == []


async def test_top_k_respected(kb, embedder):
    r = Retriever(kb, embedder, top_k=2, min_score=0.0)
    assert len(await r.retrieve("AI engineer")) <= 2
