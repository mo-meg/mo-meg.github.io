"""Chat orchestration: session → retrieval → grounded generation → citations → session update."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from app import metrics
from app.llm import GenerationError, GenerationResult, Generator, Turn
from app.logging_setup import log
from app.prompts import (
    SYSTEM_PROMPT,
    build_context,
    build_user_turn,
    extract_citations,
    strip_citations,
)
from app.retrieval import Retriever
from app.sessions import SessionStore

logger = logging.getLogger(__name__)


@dataclass
class ChatEvent:
    type: str  # meta | delta | sources | done | error
    data: dict[str, Any]


class ChatService:
    def __init__(self, retriever: Retriever, generator: Generator, sessions: SessionStore) -> None:
        self.retriever = retriever
        self.generator = generator
        self.sessions = sessions

    async def chat(
        self, message: str, session_id: str | None, categories: list[str] | None = None
    ) -> AsyncIterator[ChatEvent]:
        session = self.sessions.get_or_create(session_id)
        yield ChatEvent("meta", {"session_id": session.id})

        history = self.sessions.history(session)
        previous_user = [t.text for t in history if t.role == "user"]

        t0 = time.perf_counter()
        try:
            chunks = await self.retriever.retrieve(message, previous_user, categories)
        except Exception as e:  # noqa: BLE001
            log(logger, logging.ERROR, "retrieval_failed", error=type(e).__name__, detail=str(e)[:200])
            metrics.CHAT_REQUESTS.labels("retrieval_error").inc()
            yield ChatEvent(
                "error",
                {"message": "The knowledge base is temporarily unavailable. Please try again.", "retryable": True},
            )
            return
        metrics.RETRIEVAL_SECONDS.observe(time.perf_counter() - t0)
        metrics.RETRIEVED_CHUNKS.observe(len(chunks))

        context = build_context(chunks)
        turns = [*history, Turn("user", build_user_turn(context, message))]

        answer_parts: list[str] = []
        result = GenerationResult()
        t1 = time.perf_counter()
        try:
            async for delta in self.generator.stream(SYSTEM_PROMPT, turns, result):
                answer_parts.append(delta)
                yield ChatEvent("delta", {"text": delta})
        except GenerationError as e:
            metrics.CHAT_REQUESTS.labels("generation_error").inc()
            # Partial output stays visible; the turn is not stored so a retry starts clean.
            yield ChatEvent("error", {"message": e.public_message, "retryable": e.retryable})
            return
        metrics.GENERATION_SECONDS.observe(time.perf_counter() - t1)

        answer = "".join(answer_parts).strip()
        if not answer:
            metrics.CHAT_REQUESTS.labels("empty").inc()
            yield ChatEvent(
                "error",
                {
                    "message": "The assistant returned an empty answer. Please rephrase your question.",
                    "retryable": True,
                },
            )
            return

        cited = extract_citations(answer, context.citations)
        yield ChatEvent("sources", {"sources": [c.to_dict() for c in cited]})

        self.sessions.append_exchange(session, message, strip_citations(answer))
        metrics.CHAT_REQUESTS.labels("ok").inc()
        log(
            logger,
            logging.INFO,
            "chat_completed",
            chunks=len(chunks),
            sources_available=len(context.citations),
            sources_cited=len(cited),
            prompt_tokens=result.usage.prompt_tokens,
            output_tokens=result.usage.output_tokens,
            message_chars=len(message),
            answer_chars=len(answer),
            history_turns=len(history),
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )
        yield ChatEvent("done", {})
