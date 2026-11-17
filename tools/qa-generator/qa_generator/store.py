"""Reading/writing the Q&A and eval files with stable formatting (clean git diffs)."""

from __future__ import annotations

import json
from pathlib import Path

from qa_generator.schema import CATEGORIES, EvalFile, QAFile, QAItem


def load_qa(path: Path) -> QAFile:
    if not path.exists():
        return QAFile()
    return QAFile.model_validate_json(path.read_text(encoding="utf-8"))


def save_qa(path: Path, qa: QAFile) -> None:
    order = {c: i for i, c in enumerate(CATEGORIES)}
    qa.items.sort(key=lambda i: (order[i.category], i.id))
    _write(path, qa.model_dump(mode="json"))


def load_eval(path: Path) -> EvalFile:
    if not path.exists():
        return EvalFile()
    return EvalFile.model_validate_json(path.read_text(encoding="utf-8"))


def save_eval(path: Path, ev: EvalFile) -> None:
    _write(path, ev.model_dump(mode="json"))


def _write(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compute_related(items: list[QAItem], limit: int = 3) -> None:
    """Deterministic 'related questions': shared knowledge files first, then same category."""
    for item in items:
        files = set(item.source_files)
        scored = []
        for other in items:
            if other.id == item.id:
                continue
            score = 2 * len(files & set(other.source_files)) + (1 if other.category == item.category else 0)
            if score:
                scored.append((-score, other.id))
        item.related = [oid for _, oid in sorted(scored)[:limit]]
