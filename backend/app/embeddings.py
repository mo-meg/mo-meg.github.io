"""Embedding clients.

``GeminiEmbedder`` uses the official Google Gen AI SDK. It supports both
- ``gemini-embedding-2`` (task expressed as a text prefix, auto-normalized), and
- ``gemini-embedding-001`` (``task_type`` parameter; needs manual normalization below 3072 dims).
Vectors are always L2-normalized so cosine distance behaves consistently.

``FakeEmbedder`` is a deterministic hashed bag-of-words model for tests and offline development.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import re
from typing import Protocol

from google import genai
from google.genai import types


class Embedder(Protocol):
    model_name: str
    dim: int

    async def embed_documents(self, texts: list[str], titles: list[str] | None = None) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


def l2_normalize(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n > 0 else v


class GeminiEmbedder:
    def __init__(self, client: genai.Client, model: str, dim: int, batch_size: int = 32) -> None:
        self._client = client
        self.model_name = model
        self.dim = dim
        self._batch = batch_size
        self._legacy = "embedding-001" in model  # uses task_type instead of prompt prefixes

    def _prep_doc(self, text: str, title: str | None) -> str:
        return text if self._legacy else f"title: {title or 'none'} | text: {text}"

    def _prep_query(self, text: str) -> str:
        return text if self._legacy else f"task: search result | query: {text}"

    async def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        config = types.EmbedContentConfig(output_dimensionality=self.dim)
        if self._legacy:
            config.task_type = task_type
        # Each input wrapped in its own Content → one embedding per input
        # (a bare list of parts would produce one aggregated embedding on gemini-embedding-2).
        contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]
        resp = await self._client.aio.models.embed_content(model=self.model_name, contents=contents, config=config)
        embeddings = resp.embeddings or []
        if len(embeddings) != len(texts):
            raise RuntimeError(f"embedding count mismatch: sent {len(texts)}, got {len(embeddings)}")
        out = []
        for e in embeddings:
            values = list(e.values or [])
            if len(values) != self.dim:
                raise RuntimeError(f"embedding dimension {len(values)} != configured {self.dim}")
            out.append(l2_normalize(values))
        return out

    async def embed_documents(self, texts: list[str], titles: list[str] | None = None) -> list[list[float]]:
        titles = titles or [None] * len(texts)  # type: ignore[list-item]
        prepared = [self._prep_doc(t, ti) for t, ti in zip(texts, titles, strict=True)]
        out: list[list[float]] = []
        for i in range(0, len(prepared), self._batch):
            batch = prepared[i : i + self._batch]
            for attempt in range(3):
                try:
                    out.extend(await self._embed(batch, "RETRIEVAL_DOCUMENT"))
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2**attempt)
        return out

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([self._prep_query(text)], "RETRIEVAL_QUERY"))[0]


_TOKEN = re.compile(r"[\w]+", re.UNICODE)


class FakeEmbedder:
    """Deterministic hashed bag-of-words embeddings. Lexical only — for tests and offline demos."""

    model_name = "fake-hash-embedding"

    def __init__(self, dim: int = 768) -> None:
        self.dim = dim
        self.calls = 0

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for tok in _TOKEN.findall(text.lower()):
            if len(tok) < 3:
                continue
            stem = tok[:6]
            h = int(hashlib.md5(stem.encode(), usedforsecurity=False).hexdigest(), 16)
            v[h % self.dim] += 1.0 if (h >> 64) & 1 else -1.0
        return l2_normalize(v) if any(v) else [1.0 / math.sqrt(self.dim)] * self.dim

    async def embed_documents(self, texts: list[str], titles: list[str] | None = None) -> list[list[float]]:
        self.calls += 1
        return [self._vec(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        self.calls += 1
        return self._vec(text)
