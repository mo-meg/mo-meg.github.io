import math
from types import SimpleNamespace

import pytest

from app.embeddings import FakeEmbedder, GeminiEmbedder


class FakeModels:
    def __init__(self, dim: int, wrong_count: bool = False):
        self.dim = dim
        self.wrong_count = wrong_count
        self.requests: list[dict] = []

    async def embed_content(self, *, model, contents, config):
        self.requests.append({"model": model, "contents": contents, "config": config})
        n = len(contents) - (1 if self.wrong_count else 0)
        return SimpleNamespace(
            embeddings=[SimpleNamespace(values=[3.0] + [4.0] + [0.0] * (self.dim - 2)) for _ in range(n)]
        )


def _client(models: FakeModels):
    return SimpleNamespace(aio=SimpleNamespace(models=models))


async def test_gemini_embedding_2_uses_prefixes_and_separate_contents():
    models = FakeModels(8)
    emb = GeminiEmbedder(_client(models), "gemini-embedding-2", 8, batch_size=2)  # type: ignore[arg-type]
    vecs = await emb.embed_documents(["a", "b", "c"], titles=["T", "T", "T"])
    assert len(vecs) == 3
    assert len(models.requests) == 2  # batched
    first = models.requests[0]
    assert len(first["contents"]) == 2  # one Content per input → one embedding per input
    assert first["contents"][0].parts[0].text == "title: T | text: a"
    assert first["config"].task_type is None
    assert first["config"].output_dimensionality == 8
    assert math.isclose(sum(x * x for x in vecs[0]), 1.0)  # normalized

    await emb.embed_query("who?")
    assert models.requests[-1]["contents"][0].parts[0].text == "task: search result | query: who?"


async def test_legacy_embedding_model_uses_task_type():
    models = FakeModels(8)
    emb = GeminiEmbedder(_client(models), "gemini-embedding-001", 8)  # type: ignore[arg-type]
    await emb.embed_query("q")
    req = models.requests[0]
    assert req["config"].task_type == "RETRIEVAL_QUERY"
    assert req["contents"][0].parts[0].text == "q"


async def test_dimension_mismatch_raises():
    emb = GeminiEmbedder(_client(FakeModels(16)), "gemini-embedding-2", 8)  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="dimension"):
        await emb.embed_query("x")


async def test_count_mismatch_raises():
    emb = GeminiEmbedder(_client(FakeModels(8, wrong_count=True)), "gemini-embedding-2", 8)  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="count"):
        await emb.embed_query("x")


async def test_fake_embedder_is_deterministic_and_lexical():
    e = FakeEmbedder(128)
    a = await e.embed_query("multimodal retrieval moodle")
    b = await e.embed_query("multimodal retrieval moodle")
    c = await e.embed_query("speaker diarization audio")
    assert a == b
    sim_same = sum(x * y for x, y in zip(a, b, strict=True))
    sim_diff = sum(x * y for x, y in zip(a, c, strict=True))
    assert sim_same > sim_diff
