"""Repository locations used by the tool (overridable for tests)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Paths:
    knowledge: Path
    qa_file: Path
    eval_file: Path
    sections_file: Path  # frontend file that defines the page section ids

    @classmethod
    def default(cls) -> Paths:
        root = Path(os.environ.get("PORTFOLIO_ROOT", REPO_ROOT))
        return cls(
            knowledge=root / "knowledge",
            qa_file=root / "frontend" / "src" / "data" / "qa.json",
            eval_file=root / "frontend" / "src" / "data" / "qa-eval.json",
            sections_file=root / "frontend" / "src" / "data" / "profile.ts",
        )
