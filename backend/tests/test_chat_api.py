from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from google.genai import errors, types

from app.api import create_app
from app.llm import FakeGenerator, GeminiGenerator, GenerationError, GenerationResult, Turn
from app.services import build_services
from tests.conftest import parse_sse


def _chat(client: TestClient, message: str, session_id: str | None = None):
    body = {"message": message}
    if session_id:
        body["session_id"] = session_id
    r = client.post("/api/chat", json=body)
    return r, parse_sse(r.text) if r.status_code == 200 else []


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    r = client.get("/ready")
    assert r.status_code == 200 and r.json()["chunks"] > 0


def test_chat_streams_grounded_answer_with_sources(client):
    r, events = _chat(client, "What did Mohamed do at Prolumios with speaker diarization?")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    kinds = [e for e, _ in events]
    assert kinds[0] == "meta" and kinds[-1] == "done"
    assert "delta" in kinds and "sources" in kinds
    answer = "".join(d["text"] for e, d in events if e == "delta")
    sources = next(d["sources"] for e, d in events if e == "sources")
    assert sources, "a grounded answer must carry sources"
    # Every source shown was actually cited in the answer.
    for s in sources:
        assert f"[{s['id']}]" in answer
        assert s["label"]
    assert any("Prolumios" in s["label"] for s in sources)


def test_github_links_are_attached_to_sources(client):
    _, events = _chat(client, "Multimodal RAG Moodle Whisper Celery pgvector source attribution")
    sources = next(d["sources"] for e, d in events if e == "sources")
    assert any(s["url"] == "https://github.com/mmm-megahed/MR.Multi.RAG-Moodle" for s in sources)


def test_unsupported_question_gets_no_fabricated_sources(client, generator: FakeGenerator):
    _, events = _chat(client, "zebra pancake xylophone quantum recipe")
    system, turns = generator.calls[-1]
    assert "NONE" in turns[-1].text, "the model must be told that nothing relevant was found"
    sources = next(d["sources"] for e, d in events if e == "sources")
    assert sources == []
    answer = "".join(d["text"] for e, d in events if e == "delta")
    assert "don't have information" in answer


def test_multi_turn_history_and_reset(client, generator: FakeGenerator):
    _, ev1 = _chat(client, "Explain his Multimodal RAG project")
    sid = ev1[0][1]["session_id"]
    _, ev2 = _chat(client, "Which database did it use?", sid)
    assert ev2[0][1]["session_id"] == sid
    _, turns = generator.calls[-1]
    assert [t.role for t in turns] == ["user", "model", "user"]
    assert turns[0].text == "Explain his Multimodal RAG project"  # raw question, not the context block
    assert "[S" not in turns[1].text  # citation markers stripped from history

    assert client.post("/api/chat/reset", json={"session_id": sid}).json() == {"status": "ok"}
    _, ev3 = _chat(client, "Hello", sid)
    assert ev3[0][1]["session_id"] != sid


def test_generation_failure_is_reported_and_not_stored(settings, kb, embedder):
    gen = FakeGenerator(fail_times=1)
    services = build_services(settings, kb, embedder, gen)
    with TestClient(create_app(settings, services)) as c:
        _, ev = _chat(c, "Tell me about Prolumios")
        err = next(d for e, d in ev if e == "error")
        assert err["retryable"] is True
        assert "temporarily unavailable" in err["message"]
        sid = ev[0][1]["session_id"]
        _, ev2 = _chat(c, "Tell me about Prolumios", sid)
        assert ev2[-1][0] == "done"
        _, turns = gen.calls[-1]
        assert len(turns) == 1, "the failed exchange must not be in history"


def test_validation_errors(client, settings):
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "session_id": "bad id!"}).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "categories": ["secrets"]}).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * (settings.max_message_chars + 1)}).status_code == 413
    huge = "x" * (settings.max_request_bytes + 10)
    r = client.post("/api/chat", content=f'{{"message": "{huge}"}}', headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_rate_limiting(settings, kb, embedder):
    settings.rate_limit_per_minute = 2
    services = build_services(settings, kb, embedder, FakeGenerator())
    with TestClient(create_app(settings, services)) as c:
        assert _chat(c, "hi")[0].status_code == 200
        assert _chat(c, "hi")[0].status_code == 200
        r, _ = _chat(c, "hi")
        assert r.status_code == 429
        assert int(r.headers["retry-after"]) > 0


def test_cors_only_for_allowed_origin(client):
    ok = client.options(
        "/api/chat",
        headers={"Origin": "https://example.github.io", "Access-Control-Request-Method": "POST"},
    )
    assert ok.headers.get("access-control-allow-origin") == "https://example.github.io"
    bad = client.options(
        "/api/chat",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in bad.headers


def test_metrics_endpoint(client):
    _chat(client, "Prolumios")
    body = client.get("/metrics").text
    assert "chat_requests_total" in body


# --- Gemini generator error handling ----------------------------------------------------


def _resp(text: str, usage: bool = False):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=text)]))],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=10, candidates_token_count=3, total_token_count=13
        )
        if usage
        else None,
    )


class FlakyModels:
    def __init__(self, failures: list[Exception], fail_after_first_chunk: bool = False):
        self.failures = failures
        self.fail_after_first_chunk = fail_after_first_chunk
        self.calls = 0

    async def generate_content_stream(self, *, model, contents, config):
        self.calls += 1
        failures = self.failures
        mid = self.fail_after_first_chunk

        async def gen():
            if failures and not mid:
                raise failures.pop(0)
            yield _resp("Hello ")
            if failures and mid:
                raise failures.pop(0)
            yield _resp("world", usage=True)

        return gen()


def _gemini(models) -> GeminiGenerator:
    client = SimpleNamespace(aio=SimpleNamespace(models=models))
    return GeminiGenerator(client, "m", temperature=0.2, max_output_tokens=100, timeout_s=5)  # type: ignore[arg-type]


async def _collect(gen: GeminiGenerator) -> tuple[str, GenerationResult]:
    res = GenerationResult()
    out = "".join([t async for t in gen.stream("sys", [Turn("user", "q")], res)])
    return out, res


async def test_gemini_retries_transient_error_before_output():
    models = FlakyModels([errors.ServerError(503, {"error": {"message": "x"}})])
    out, res = await _collect(_gemini(models))
    assert out == "Hello world"
    assert models.calls == 2
    assert res.usage.total_tokens == 13


async def test_gemini_does_not_retry_after_partial_output():
    models = FlakyModels([errors.ServerError(503, {"error": {"message": "x"}})], fail_after_first_chunk=True)
    with pytest.raises(GenerationError) as ei:
        await _collect(_gemini(models))
    assert models.calls == 1
    assert ei.value.retryable


async def test_gemini_quota_error_maps_to_safe_message():
    models = FlakyModels([errors.ClientError(429, {"error": {"message": "secret internal detail"}})] * 3)
    with pytest.raises(GenerationError) as ei:
        await _collect(_gemini(models))
    assert ei.value.status == 429
    assert "secret" not in ei.value.public_message


async def test_gemini_bad_request_not_retried():
    models = FlakyModels([errors.ClientError(400, {"error": {"message": "bad"}})])
    with pytest.raises(GenerationError) as ei:
        await _collect(_gemini(models))
    assert not ei.value.retryable
    assert models.calls == 1


async def test_gemini_timeout():
    import asyncio

    class Slow:
        async def generate_content_stream(self, **_):
            async def gen():
                await asyncio.sleep(10)
                yield _resp("late")

            return gen()

    client = SimpleNamespace(aio=SimpleNamespace(models=Slow()))
    g = GeminiGenerator(client, "m", temperature=0, max_output_tokens=10, timeout_s=0.05, max_attempts=1)  # type: ignore[arg-type]
    with pytest.raises(GenerationError) as ei:
        await _collect(g)
    assert ei.value.retryable and "too long" in ei.value.public_message
