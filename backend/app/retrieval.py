"""Query-side retrieval: query processing → embedding → hybrid search → fusion → threshold → top-k."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from app.embeddings import Embedder
from app.models import RetrievedChunk
from app.vectorstore import VectorStore

RRF_K = 60


def normalize_query(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def rrf_fuse(result_lists: list[list[RetrievedChunk]], k: int = RRF_K) -> list[RetrievedChunk]:
    """Reciprocal rank fusion: robust way to merge rankings whose scores are not comparable."""
    fused: dict[int, RetrievedChunk] = {}
    scores: dict[int, float] = {}
    for results in result_lists:
        for rank, c in enumerate(results):
            scores[c.chunk_id] = scores.get(c.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            prev = fused.get(c.chunk_id)
            if prev is None or c.similarity > prev.similarity:
                fused[c.chunk_id] = c
    out = []
    for cid, c in fused.items():
        c.score = scores[cid]
        out.append(c)
    return sorted(out, key=lambda c: (-c.score, -c.similarity))


@dataclass
class Retriever:
    store: VectorStore
    embedder: Embedder
    top_k: int = 6
    candidates: int = 20
    min_score: float = 0.40

    def build_queries(self, question: str, previous_user_turns: list[str]) -> list[str]:
        """The question itself, plus — in a multi-turn conversation — the question combined with
        the previous user turn, so follow-ups like "which database did it use?" stay on topic."""
        q = normalize_query(question)
        queries = [q]
        if previous_user_turns:
            prev = normalize_query(previous_user_turns[-1])[:500]
            if prev and prev.lower() != q.lower():
                queries.append(f"{prev} {q}")
        return queries

    async def retrieve(
        self,
        question: str,
        previous_user_turns: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        queries = self.build_queries(question, previous_user_turns or [])
        vectors = await asyncio.gather(*(self.embedder.embed_query(q) for q in queries))
        searches = []
        for q, v in zip(queries, vectors, strict=True):
            searches.append(self.store.vector_search(v, self.candidates, categories))
            searches.append(self.store.keyword_search(q, v, self.candidates, categories))
        lists = await asyncio.gather(*searches)
        fused = rrf_fuse(list(lists))
        # Relevance gate on semantic similarity: keyword overlap alone ("Mohamed", "project")
        # is not evidence. If nothing passes, the generator is told there is no context.
        relevant = [c for c in fused if c.similarity >= self.min_score]
        return relevant[: self.top_k]
