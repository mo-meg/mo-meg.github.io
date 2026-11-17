"""Wiring: builds embedder, generator, store, and services from settings."""

from __future__ import annotations

from dataclasses import dataclass

from google import genai
from google.genai import types
from psycopg_pool import AsyncConnectionPool

from app.config import Settings
from app.embeddings import Embedder, FakeEmbedder, GeminiEmbedder
from app.ingestion.pipeline import Ingestor
from app.llm import FakeGenerator, GeminiGenerator, Generator
from app.rag import ChatService
from app.retrieval import Retriever
from app.security import RateLimiter
from app.sessions import SessionStore
from app.vectorstore import VectorStore


def build_ai(settings: Settings) -> tuple[Embedder, Generator]:
    if settings.ai_provider == "fake":
        return FakeEmbedder(settings.embedding_dim), FakeGenerator()
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=int(settings.gemini_timeout_seconds * 1000)),
    )
    embedder = GeminiEmbedder(
        client, settings.gemini_embedding_model, settings.embedding_dim, settings.embedding_batch_size
    )
    generator = GeminiGenerator(
        client,
        settings.gemini_model,
        temperature=settings.gemini_temperature,
        max_output_tokens=settings.gemini_max_output_tokens,
        timeout_s=settings.gemini_timeout_seconds,
        thinking_level=settings.gemini_thinking_level,
    )
    return embedder, generator


@dataclass
class Services:
    store: VectorStore
    embedder: Embedder
    generator: Generator
    chat: ChatService
    limiter: RateLimiter
    sessions: SessionStore
    pool: AsyncConnectionPool | None = None

    def ingestor(self, settings: Settings) -> Ingestor:
        return Ingestor(self.store, self.embedder, settings.chunk_size, settings.chunk_overlap)


def build_services(
    settings: Settings,
    store: VectorStore,
    embedder: Embedder,
    generator: Generator,
    pool: AsyncConnectionPool | None = None,
) -> Services:
    sessions = SessionStore(
        ttl_seconds=settings.session_ttl_minutes * 60,
        max_sessions=settings.max_sessions,
        history_turns=settings.history_turns,
        max_history_chars=settings.max_history_chars,
    )
    retriever = Retriever(
        store,
        embedder,
        top_k=settings.retrieval_top_k,
        candidates=settings.retrieval_candidates,
        min_score=settings.retrieval_min_score,
    )
    return Services(
        store=store,
        embedder=embedder,
        generator=generator,
        chat=ChatService(retriever, generator, sessions),
        limiter=RateLimiter(settings.rate_limit_per_minute, settings.rate_limit_per_day, settings.daily_request_budget),
        sessions=sessions,
        pool=pool,
    )
