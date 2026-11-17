"""Answer generation. Retrieval happens elsewhere — the generator only phrases retrieved evidence."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal, Protocol

from google import genai
from google.genai import errors, types

from app import metrics
from app.logging_setup import log

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Turn:
    role: Literal["user", "model"]
    text: str


@dataclass(slots=True)
class Usage:
    prompt_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(slots=True)
class GenerationResult:
    usage: Usage = field(default_factory=Usage)


class GenerationError(Exception):
    """Raised for provider failures. ``public_message`` is safe to show to visitors."""

    def __init__(self, public_message: str, *, retryable: bool, status: int | None = None) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.retryable = retryable
        self.status = status


class Generator(Protocol):
    model_name: str

    def stream(self, system: str, turns: list[Turn], result: GenerationResult) -> AsyncIterator[str]: ...


def _map_error(e: Exception) -> GenerationError:
    if isinstance(e, GenerationError):
        return e
    if isinstance(e, (asyncio.TimeoutError, TimeoutError)):
        return GenerationError("The AI model took too long to respond. Please try again.", retryable=True)
    if isinstance(e, errors.APIError):
        code = getattr(e, "code", None)
        if code == 429:
            return GenerationError(
                "The assistant is busy right now. Please try again shortly.", retryable=True, status=429
            )
        if isinstance(e, errors.ServerError) or (code and code >= 500):
            return GenerationError(
                "The AI service is temporarily unavailable. Please try again.", retryable=True, status=code
            )
        return GenerationError("The assistant could not process this request.", retryable=False, status=code)
    name = type(e).__name__.lower()
    if "timeout" in name or "connect" in name:
        return GenerationError("The AI service could not be reached. Please try again.", retryable=True)
    return GenerationError("An unexpected error occurred while generating the answer.", retryable=False)


class GeminiGenerator:
    def __init__(
        self,
        client: genai.Client,
        model: str,
        *,
        temperature: float,
        max_output_tokens: int,
        timeout_s: float,
        thinking_level: str = "",
        max_attempts: int = 2,
    ) -> None:
        self._client = client
        self.model_name = model
        self._temperature = temperature
        self._max_tokens = max_output_tokens
        self._timeout = timeout_s
        self._thinking = thinking_level
        self._attempts = max_attempts

    def _config(self, system: str) -> types.GenerateContentConfig:
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            temperature=self._temperature,
            max_output_tokens=self._max_tokens,
        )
        if self._thinking:
            cfg.thinking_config = types.ThinkingConfig(thinking_level=self._thinking)  # type: ignore[arg-type]
        return cfg

    async def stream(self, system: str, turns: list[Turn], result: GenerationResult) -> AsyncIterator[str]:
        contents = [types.Content(role=t.role, parts=[types.Part(text=t.text)]) for t in turns]
        config = self._config(system)
        attempt = 0
        while True:
            attempt += 1
            emitted = False
            try:
                async with asyncio.timeout(self._timeout):
                    stream = await self._client.aio.models.generate_content_stream(
                        model=self.model_name, contents=contents, config=config
                    )
                    async for chunk in stream:
                        if chunk.usage_metadata:
                            um = chunk.usage_metadata
                            result.usage = Usage(
                                prompt_tokens=um.prompt_token_count or 0,
                                output_tokens=um.candidates_token_count or 0,
                                total_tokens=um.total_token_count or 0,
                            )
                        text = chunk.text if chunk.candidates else None
                        if text:
                            emitted = True
                            yield text
                metrics.TOKENS.labels("prompt").inc(result.usage.prompt_tokens)
                metrics.TOKENS.labels("output").inc(result.usage.output_tokens)
                return
            except Exception as e:
                err = _map_error(e)
                log(
                    logger,
                    logging.WARNING,
                    "generation_error",
                    error=type(e).__name__,
                    status=err.status,
                    attempt=attempt,
                )
                # Retry only if nothing was streamed yet — never duplicate partial output.
                if err.retryable and not emitted and attempt < self._attempts:
                    await asyncio.sleep(0.8 * attempt)
                    continue
                raise err from e


_SENT = re.compile(r"(?<=[.!?])\s+")


class FakeGenerator:
    """Extractive stand-in for tests and offline UI work: echoes the first sentence of each source."""

    model_name = "fake-extractive"

    def __init__(self, fail_times: int = 0, error: GenerationError | None = None) -> None:
        self.fail_times = fail_times
        self.error = error or GenerationError("The AI service is temporarily unavailable.", retryable=True)
        self.calls: list[tuple[str, list[Turn]]] = []

    async def stream(self, system: str, turns: list[Turn], result: GenerationResult) -> AsyncIterator[str]:
        self.calls.append((system, turns))
        if self.fail_times > 0:
            self.fail_times -= 1
            raise self.error
        prompt = turns[-1].text
        blocks = re.findall(r"\[(S\d+)\][^\n]*\n(.*?)(?=\n\[S\d+\]|\n</retrieved_context>)", prompt, re.DOTALL)
        if not blocks:
            answer = (
                "I don't have information about that in Mohamed's knowledge base. "
                "For anything else, please use the contact section."
            )
        else:
            parts = []
            for sid, body in blocks[:2]:
                body = " ".join(body.split())
                first = _SENT.split(body)[0][:280]
                parts.append(f"{first} [{sid}]")
            answer = "Here is what the knowledge base says:\n\n" + "\n\n".join(f"- {p}" for p in parts)
        result.usage = Usage(prompt_tokens=len(prompt) // 4, output_tokens=len(answer) // 4, total_tokens=0)
        for word in re.split(r"(\s+)", answer):
            await asyncio.sleep(0)
            yield word
