"""Data model of the published Q&A file (frontend/src/data/qa.json) and its evaluation set."""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["en", "de", "ar"]
LANGS: tuple[Lang, ...] = ("en", "de", "ar")
Status = Literal["draft", "approved", "needs-review"]
Category = Literal["profile", "experience", "projects", "skills", "cloud", "education", "contact"]
CATEGORIES: tuple[str, ...] = ("profile", "experience", "projects", "skills", "cloud", "education", "contact")

ID_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
MIN_PARAPHRASES = 5
MAX_PARAPHRASES = 10
MAX_ANSWER_WORDS = 120


class Source(BaseModel):
    label: str = Field(min_length=1)
    # "https://…" (e.g. a GitHub repository) or "#section" on the portfolio page
    href: str = Field(pattern=r"^(https://\S+|#[a-z][a-z0-9-]*)$")


class Localized(BaseModel):
    question: str = Field(min_length=3)
    answer: str = Field(min_length=1)
    paraphrases: list[str] = Field(default_factory=list)


class QAItem(BaseModel):
    id: str = Field(pattern=ID_PATTERN)
    category: Category
    status: Status = "draft"
    sources: list[Source] = Field(default_factory=list, max_length=3)
    related: list[str] = Field(default_factory=list)
    # knowledge file (relative to knowledge/) → fingerprint at generation/approval time
    source_files: dict[str, str] = Field(default_factory=dict)
    # hash of `i18n` when the generator last wrote it; None = written by a human
    generated_hash: str | None = None
    i18n: dict[Lang, Localized]

    def content_hash(self) -> str:
        return content_hash(self.i18n)

    @property
    def edited(self) -> bool:
        """True if a human wrote or changed the text since the generator produced it."""
        return self.generated_hash is None or self.generated_hash != self.content_hash()

    @property
    def protected(self) -> bool:
        """Protected items are never overwritten by the generator."""
        return self.status == "approved" or self.edited


class QAFile(BaseModel):
    version: int = 1
    items: list[QAItem] = Field(default_factory=list)

    def get(self, item_id: str) -> QAItem | None:
        return next((i for i in self.items if i.id == item_id), None)


class EvalCase(BaseModel):
    text: str = Field(min_length=1)
    lang: Lang
    # id of the item that must match, or None if the question must fall back to "contact me"
    expected: str | None = None


class EvalFile(BaseModel):
    version: int = 1
    cases: list[EvalCase] = Field(default_factory=list)


def content_hash(i18n: dict[str, Localized]) -> str:
    payload = {k: v.model_dump() for k, v in sorted(i18n.items())}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
