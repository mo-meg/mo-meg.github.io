"""Consistency checks for the Q&A file. Errors block publishing; warnings are informational."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from qa_generator.knowledge import KnowledgeFile
from qa_generator.schema import LANGS, MAX_ANSWER_WORDS, MAX_PARAPHRASES, MIN_PARAPHRASES, EvalFile, QAFile

_ARABIC = re.compile(r"[\u0600-\u06ff]")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def words(text: str) -> int:
    return len(re.findall(r"\S+", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)))


def validate(
    qa: QAFile,
    sections: set[str],
    kb: dict[str, KnowledgeFile] | None = None,
    ev: EvalFile | None = None,
) -> Report:
    r = Report()
    ids = [i.id for i in qa.items]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        r.errors.append(f"duplicate ids: {sorted(dupes)}")
    known = set(ids)

    for item in qa.items:
        p = f"[{item.id}]"
        for lang in LANGS:
            loc = item.i18n.get(lang)
            if loc is None:
                r.errors.append(f"{p} missing '{lang}' translation")
                continue
            if not loc.answer.strip():
                r.errors.append(f"{p} empty {lang} answer")
            if not loc.question.strip():
                r.errors.append(f"{p} empty {lang} question")
            n = len([x for x in loc.paraphrases if x.strip()])
            if not MIN_PARAPHRASES <= n <= MAX_PARAPHRASES:
                r.errors.append(f"{p} {lang} has {n} paraphrases (expected {MIN_PARAPHRASES}–{MAX_PARAPHRASES})")
            if len({x.strip().lower() for x in loc.paraphrases}) != len(loc.paraphrases):
                r.warnings.append(f"{p} duplicate {lang} paraphrases")
            if words(loc.answer) > MAX_ANSWER_WORDS * 1.25:
                r.errors.append(f"{p} {lang} answer has {words(loc.answer)} words (limit ~{MAX_ANSWER_WORDS})")
            elif words(loc.answer) > MAX_ANSWER_WORDS:
                r.warnings.append(f"{p} {lang} answer has {words(loc.answer)} words")
            if lang == "ar" and not _ARABIC.search(loc.answer + loc.question):
                r.errors.append(f"{p} 'ar' text contains no Arabic script")
            if lang != "ar" and _ARABIC.search(loc.question):
                r.errors.append(f"{p} '{lang}' question contains Arabic script")

        if not item.sources:
            r.warnings.append(f"{p} has no sources")
        for s in item.sources:
            if s.href.startswith("#") and s.href[1:] not in sections:
                r.errors.append(f"{p} source link {s.href} is not a page section ({', '.join(sorted(sections))})")
        for rel in item.related:
            if rel not in known:
                r.errors.append(f"{p} related id '{rel}' does not exist")
        if kb is not None:
            for f in item.source_files:
                if f not in kb:
                    r.errors.append(f"{p} source file '{f}' not found in knowledge/")
                elif item.status == "approved" and item.source_files[f] != kb[f].fingerprint:
                    r.warnings.append(f"{p} approved but '{f}' changed since — run `generate` to flag for review")

    if ev is not None:
        for c in ev.cases:
            if c.expected is not None and c.expected not in known:
                r.errors.append(f"eval case '{c.text}' expects unknown id '{c.expected}'")

    if not any(i.status == "approved" for i in qa.items):
        r.warnings.append("no approved items — the published site will hide the assistant")
    return r
