from __future__ import annotations

from pathlib import Path

import pytest

from qa_generator.llm import EnglishDraft, EvalDraft, EvalDrafts, Plan, Translations
from qa_generator.paths import Paths
from qa_generator.schema import Localized, Source

PROFILE_TS = """export const navItems = [
  { id: 'about', label: 'About' },
  { id: 'projects', label: 'Projects' },
  { id: 'experience', label: 'Experience' },
  { id: 'contact', label: 'Contact' },
] as const
"""


def write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


@pytest.fixture
def repo(tmp_path: Path) -> Paths:
    write(tmp_path / "frontend/src/data/profile.ts", PROFILE_TS)
    write(
        tmp_path / "knowledge/experience/job.md",
        "---\ntitle: Job\n---\n# Job\nAI Engineer at Prolumios. Speaker diarization.",
    )
    write(
        tmp_path / "knowledge/projects/rag.md",
        "---\ntitle: RAG\nurl: https://github.com/o/rag\n---\n# RAG\nMultimodal RAG for Moodle.",
    )
    write(tmp_path / "knowledge/README.md", "ignored")
    return Paths(
        knowledge=tmp_path / "knowledge",
        qa_file=tmp_path / "frontend/src/data/qa.json",
        eval_file=tmp_path / "frontend/src/data/qa-eval.json",
        sections_file=tmp_path / "frontend/src/data/profile.ts",
    )


def loc(q: str, lang: str) -> Localized:
    prefix = {"en": "", "de": "DE ", "ar": "سؤال "}[lang]
    return Localized(
        question=f"{prefix}{q}",
        answer=f"{prefix}Answer to {q}",
        paraphrases=[f"{prefix}{q} variant {n}" for n in range(5)],
    )


class FakeWriter:
    """Deterministic stand-in for Gemini. Records calls."""

    def __init__(self, plan_items: list[EnglishDraft] | None = None) -> None:
        self.plan_items = plan_items
        self.calls: list[str] = []

    def plan(self, knowledge, links, existing, focus_files, count):
        self.calls.append(f"plan:{','.join(focus_files)}:{count}")
        if self.plan_items is not None:
            return Plan(items=self.plan_items)
        items = []
        for f in focus_files or ["experience/job.md"]:
            stem = f.split("/")[-1].removesuffix(".md")
            items.append(
                EnglishDraft(
                    id=f"about-{stem}",
                    category="experience" if f.startswith("experience") else "projects",
                    question=f"What about {stem}?",
                    answer=f"Answer about {stem}.",
                    paraphrases=[f"{stem} question {n}" for n in range(6)],
                    sources=[Source(label="x", href="#projects")],
                    source_files=[f],
                )
            )
        return Plan(items=items)

    def rewrite(self, knowledge, links, item):
        self.calls.append(f"rewrite:{item.id}")
        return item.model_copy(update={"answer": item.answer + " (updated)", "id": "changed-by-model"})

    def translate(self, item):
        self.calls.append(f"translate:{item.id}")
        return Translations(
            de=Localized(
                question="DE " + item.question, answer="DE " + item.answer, paraphrases=[f"de {n}" for n in range(5)]
            ),
            ar=Localized(
                question="سؤال " + item.question,
                answer="جواب " + item.answer,
                paraphrases=[f"سؤال {n}" for n in range(5)],
            ),
        )

    def eval_cases(self, item, negatives):
        self.calls.append(f"eval:{item.id if item else None}:{negatives}")
        pos = [EvalDraft(text=f"reworded {item.question}", lang="en")] if item else []
        neg = [EvalDraft(text=f"pizza {n}", lang="en") for n in range(negatives)]
        return EvalDrafts(positives=pos, negatives=neg)
