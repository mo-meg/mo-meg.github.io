"""Evaluate retrieval quality and answer faithfulness on eval/dataset.jsonl.

    python -m app.evaluation                       # retrieval + answers + LLM-judged faithfulness
    python -m app.evaluation --retrieval-only      # only hit@k / recall@k / MRR (embedding calls only)
    python -m app.evaluation --out report.json

Metrics
- hit@k      : at least one expected source is among the retrieved documents (answerable questions)
- recall@k   : share of expected sources retrieved
- MRR        : reciprocal rank of the first expected source (document level)
- keyword    : answer contains the required facts (must_include)
- faithful   : an LLM judge confirms every claim is supported by the retrieved context
- abstained  : for unanswerable / injection questions, the answer declines instead of fabricating
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from google import genai
from google.genai import types

from app.config import Settings, get_settings
from app.db import create_pool
from app.llm import GenerationResult, Turn
from app.logging_setup import setup_logging
from app.prompts import SYSTEM_PROMPT, build_context, build_user_turn, extract_citations
from app.retrieval import Retriever
from app.services import build_ai
from app.vectorstore import PgVectorStore

DATASET = Path(__file__).resolve().parents[1] / "eval" / "dataset.jsonl"

JUDGE_PROMPT = """You are a strict evaluator of a retrieval-augmented assistant that answers questions about a person's professional profile.

<context>
{context}
</context>

<question>{question}</question>

<answer>
{answer}
</answer>

Evaluate:
1. faithful: true if EVERY factual claim about the person in the answer is supported by the context (general explanations of technology terms are allowed). false if any claim is unsupported or contradicts the context.
2. unsupported_claims: list the unsupported claims (empty if none).
3. abstained: true if the answer states that the requested information is not available / declines, instead of answering it.
Respond with JSON only: {{"faithful": bool, "unsupported_claims": [str], "abstained": bool}}"""

ABSTAIN_PATTERNS = re.compile(
    r"not (currently )?available|no information|don't have|do not have|isn't (included|available)|"
    r"nicht (verfügbar|enthalten)|keine information|غير متوفر|لا تتوفر|لا يوجد|can only help",
    re.I,
)


@dataclass
class Row:
    id: str
    answerable: bool
    retrieved: list[str]
    hit: bool | None = None
    recall: float | None = None
    rr: float | None = None
    answer: str | None = None
    cited: list[str] = field(default_factory=list)
    keyword_ok: bool | None = None
    faithful: bool | None = None
    abstained: bool | None = None
    unsupported: list[str] = field(default_factory=list)


async def judge(client: genai.Client, model: str, context: str, question: str, answer: str) -> dict:
    resp = await client.aio.models.generate_content(
        model=model,
        contents=JUDGE_PROMPT.format(context=context, question=question, answer=answer),
        config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
    )
    try:
        return json.loads(resp.text or "{}")
    except json.JSONDecodeError:
        return {}


async def run(settings: Settings, retrieval_only: bool, judge_model: str | None) -> list[Row]:
    pool = await create_pool(settings.database_url)
    try:
        store = PgVectorStore(pool)
        embedder, generator = build_ai(settings)
        retriever = Retriever(
            store, embedder, settings.retrieval_top_k, settings.retrieval_candidates, settings.retrieval_min_score
        )
        judge_client = (
            genai.Client(api_key=settings.gemini_api_key)
            if not retrieval_only and settings.ai_provider == "gemini"
            else None
        )
        rows: list[Row] = []
        for line in DATASET.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            chunks = await retriever.retrieve(item["question"])
            docs = list(dict.fromkeys(c.source_id for c in chunks))
            row = Row(item["id"], item["answerable"], docs)
            expected = set(item["expected_sources"])
            if item["answerable"] and expected:
                ranks = [i for i, d in enumerate(docs) if d in expected]
                row.hit = bool(ranks)
                row.recall = len(expected & set(docs)) / len(expected)
                row.rr = 1 / (ranks[0] + 1) if ranks else 0.0

            if not retrieval_only:
                ctx = build_context(chunks)
                res = GenerationResult()
                parts = [
                    t
                    async for t in generator.stream(
                        SYSTEM_PROMPT, [Turn("user", build_user_turn(ctx, item["question"]))], res
                    )
                ]
                row.answer = "".join(parts)
                row.cited = [c.id for c in extract_citations(row.answer, ctx.citations)]
                if item["must_include"]:
                    row.keyword_ok = all(k.lower() in row.answer.lower() for k in item["must_include"])
                row.abstained = bool(ABSTAIN_PATTERNS.search(row.answer))
                if judge_client:
                    verdict = await judge(
                        judge_client,
                        judge_model or settings.gemini_model,
                        ctx.prompt_block,
                        item["question"],
                        row.answer,
                    )
                    row.faithful = verdict.get("faithful")
                    row.unsupported = verdict.get("unsupported_claims") or []
                    if "abstained" in verdict:
                        row.abstained = bool(verdict["abstained"])
            rows.append(row)
            print(
                f"  {row.id:<11} retrieved={len(docs)} hit={row.hit} faithful={row.faithful} abstained={row.abstained}"
            )
        return rows
    finally:
        await pool.close()


def summarize(rows: list[Row]) -> dict[str, float | int | None]:
    def mean(vals: list[float]) -> float | None:
        return round(sum(vals) / len(vals), 3) if vals else None

    ans = [r for r in rows if r.answerable]
    neg = [r for r in rows if not r.answerable]
    return {
        "questions": len(rows),
        "hit@k": mean([float(r.hit) for r in ans if r.hit is not None]),
        "recall@k": mean([r.recall for r in ans if r.recall is not None]),
        "mrr": mean([r.rr for r in ans if r.rr is not None]),
        "keyword_accuracy": mean([float(r.keyword_ok) for r in ans if r.keyword_ok is not None]),
        "faithfulness": mean([float(r.faithful) for r in rows if r.faithful is not None]),
        "answered_when_answerable": mean([float(not r.abstained) for r in ans if r.abstained is not None]),
        "abstained_when_unanswerable": mean([float(bool(r.abstained)) for r in neg if r.abstained is not None]),
        "cited_when_answerable": mean([float(bool(r.cited)) for r in ans if r.answer is not None]),
    }


def main() -> int:
    p = argparse.ArgumentParser(prog="python -m app.evaluation")
    p.add_argument("--retrieval-only", action="store_true")
    p.add_argument("--judge-model", help="model used as faithfulness judge (default: GEMINI_MODEL)")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    settings = get_settings()
    setup_logging("WARNING")
    rows = asyncio.run(run(settings, args.retrieval_only, args.judge_model))
    summary = summarize(rows)
    print(json.dumps(summary, indent=2))
    if args.out:
        args.out.write_text(
            json.dumps({"summary": summary, "rows": [asdict(r) for r in rows]}, indent=2, ensure_ascii=False)
        )
        print(f"report written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
