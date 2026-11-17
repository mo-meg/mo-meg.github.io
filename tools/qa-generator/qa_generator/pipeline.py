"""Generation run: detect knowledge changes, protect human work, draft new items, translate, test data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from qa_generator.knowledge import KnowledgeFile, allowed_links, load_knowledge, render_for_prompt, section_ids
from qa_generator.llm import EnglishDraft, Writer
from qa_generator.paths import Paths
from qa_generator.schema import MAX_PARAPHRASES, EvalCase, EvalFile, Localized, QAFile, QAItem, Source
from qa_generator.store import compute_related, load_eval, load_qa, save_eval, save_qa
from qa_generator.validate import Report, validate

CATEGORY_SECTION = {
    "profile": "about",
    "experience": "experience",
    "projects": "projects",
    "skills": "expertise",
    "cloud": "expertise",
    "education": "education",
    "contact": "contact",
}


@dataclass
class RunReport:
    created: list[str] = field(default_factory=list)
    regenerated: list[str] = field(default_factory=list)
    flagged: list[str] = field(default_factory=list)  # protected items whose sources changed → needs-review
    unchanged: int = 0
    skipped: dict[str, str] = field(default_factory=dict)  # model output that failed validation
    eval_added: int = 0
    validation: Report | None = None


def changed_sources(item: QAItem, kb: dict[str, KnowledgeFile]) -> list[str]:
    return [f for f, fp in item.source_files.items() if f not in kb or kb[f].fingerprint != fp]


def to_draft(item: QAItem) -> EnglishDraft:
    en = item.i18n["en"]
    return EnglishDraft(
        id=item.id,
        category=item.category,
        question=en.question,
        answer=en.answer,
        paraphrases=en.paraphrases,
        sources=item.sources,
        source_files=list(item.source_files),
    )


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48].strip("-") or "item"


def sanitize(d: EnglishDraft, kb: dict[str, KnowledgeFile], links: list[str], taken: set[str]) -> EnglishDraft:
    """Make model output safe to store: unique id, real files, allowed links only, bounded paraphrases."""
    base = _slug(d.id or d.question)
    new_id, n = base, 2
    while new_id in taken:
        new_id, n = f"{base}-{n}", n + 1
    allowed = set(links)
    sources = [s for s in d.sources if s.href in allowed][:3]
    if not sources:
        section = CATEGORY_SECTION[d.category]
        sources = [Source(label=f"Portfolio — {section.capitalize()}", href=f"#{section}")]
    paraphrases = list(dict.fromkeys(p.strip() for p in d.paraphrases if p.strip() and p.strip() != d.question))
    return d.model_copy(
        update={
            "id": new_id,
            "sources": sources,
            "source_files": [f for f in dict.fromkeys(d.source_files) if f in kb],
            "paraphrases": paraphrases[:MAX_PARAPHRASES],
        }
    )


def build_item(d: EnglishDraft, writer: Writer, kb: dict[str, KnowledgeFile]) -> QAItem:
    tr = writer.translate(d)
    for loc in (tr.de, tr.ar):
        loc.paraphrases = list(dict.fromkeys(p.strip() for p in loc.paraphrases if p.strip()))[:MAX_PARAPHRASES]
    item = QAItem(
        id=d.id,
        category=d.category,
        status="draft",
        sources=d.sources,
        source_files={f: kb[f].fingerprint for f in d.source_files},
        i18n={
            "en": Localized(question=d.question, answer=d.answer, paraphrases=d.paraphrases),
            "de": tr.de,
            "ar": tr.ar,
        },
    )
    item.generated_hash = item.content_hash()
    return item


def run_generate(
    paths: Paths,
    writer: Writer,
    *,
    max_new: int = 10,
    negatives_target: int = 30,
    dry_run: bool = False,
) -> RunReport:
    kb = load_knowledge(paths.knowledge)
    sections = section_ids(paths.sections_file)
    links = allowed_links(kb, sections)
    knowledge = render_for_prompt(kb)
    qa = load_qa(paths.qa_file)
    ev = load_eval(paths.eval_file)
    report = RunReport()
    touched: list[QAItem] = []

    # 1. Existing items whose knowledge changed.
    for idx, item in enumerate(qa.items):
        if not changed_sources(item, kb):
            report.unchanged += 1
            continue
        if item.protected:
            item.status = "needs-review"
            report.flagged.append(item.id)
            continue
        taken = {i.id for i in qa.items} - {item.id}
        draft = sanitize(writer.rewrite(knowledge, links, to_draft(item)), kb, links, taken)
        draft = draft.model_copy(update={"id": item.id, "category": item.category})
        qa.items[idx] = build_item(draft, writer, kb)
        report.regenerated.append(item.id)
        touched.append(qa.items[idx])

    # 2. New items for knowledge files no question is based on yet (or a first full run).
    covered = {f for i in qa.items for f in i.source_files}
    uncovered = [f for f in kb if f not in covered]
    if max_new > 0 and (uncovered or not qa.items):
        count = max_new if not qa.items else min(max_new, 2 * len(uncovered))
        existing = [i.i18n["en"].question for i in qa.items]
        plan = writer.plan(knowledge, links, existing, uncovered, count)
        taken = {i.id for i in qa.items}
        for d in plan.items[:count]:
            clean = sanitize(d, kb, links, taken)
            if not clean.source_files:
                continue  # an answer that cites no knowledge file is not grounded — drop it
            try:
                item = build_item(clean, writer, kb)
            except ValidationError as e:
                report.skipped[clean.id] = str(e).splitlines()[0]
                continue
            taken.add(clean.id)
            qa.items.append(item)
            report.created.append(item.id)
            touched.append(item)

    # 3. Matcher test data: positives for touched items, negatives topped up to the target.
    have_positive = {c.expected for c in ev.cases if c.expected}
    for item in touched:
        if item.id in have_positive:
            continue
        for c in writer.eval_cases(to_draft(item), 0).positives:
            ev.cases.append(EvalCase(text=c.text, lang=c.lang, expected=item.id))
            report.eval_added += 1
    missing_neg = negatives_target - sum(1 for c in ev.cases if c.expected is None)
    if missing_neg > 0:
        for c in writer.eval_cases(None, missing_neg).negatives:
            ev.cases.append(EvalCase(text=c.text, lang=c.lang, expected=None))
            report.eval_added += 1
    ev.cases = [c for c in ev.cases if c.expected is None or qa.get(c.expected) is not None]

    compute_related(qa.items)
    report.validation = validate(qa, sections, kb, ev)
    if not dry_run:
        save_qa(paths.qa_file, qa)
        save_eval(paths.eval_file, ev)
    return report


def approve(paths: Paths, ids: list[str], all_pending: bool = False) -> list[str]:
    """Mark items approved and record the knowledge fingerprints they were reviewed against."""
    kb = load_knowledge(paths.knowledge)
    qa = load_qa(paths.qa_file)
    done = []
    for item in qa.items:
        if item.id in ids or (all_pending and item.status != "approved"):
            item.status = "approved"
            item.source_files = {f: kb[f].fingerprint for f in item.source_files if f in kb}
            done.append(item.id)
    missing = set(ids) - {i.id for i in qa.items}
    if missing:
        raise KeyError(f"unknown ids: {sorted(missing)}")
    save_qa(paths.qa_file, qa)
    return done


def stamp(paths: Paths, mark_generated: bool = False) -> int:
    """Fill in missing fingerprints (and optionally mark text as generator-written). For hand-made drafts."""
    kb = load_knowledge(paths.knowledge)
    qa = load_qa(paths.qa_file)
    n = 0
    for item in qa.items:
        for f in list(item.source_files):
            if not item.source_files[f] and f in kb:
                item.source_files[f] = kb[f].fingerprint
                n += 1
        if mark_generated and item.generated_hash is None:
            item.generated_hash = item.content_hash()
            n += 1
    compute_related(qa.items)
    save_qa(paths.qa_file, qa)
    return n


def summary(qa: QAFile, ev: EvalFile) -> dict[str, int]:
    out: dict[str, int] = {"items": len(qa.items)}
    for i in qa.items:
        out[i.status] = out.get(i.status, 0) + 1
    out["edited"] = sum(1 for i in qa.items if i.edited)
    out["eval_positive"] = sum(1 for c in ev.cases if c.expected)
    out["eval_negative"] = sum(1 for c in ev.cases if c.expected is None)
    return out
