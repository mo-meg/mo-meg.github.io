"""Knowledge base access: files, fingerprints, and the links answers may cite."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


@dataclass(frozen=True)
class KnowledgeFile:
    path: str  # relative posix path, e.g. "projects/multimodal-rag-moodle.md"
    title: str
    url: str | None
    text: str  # full file content including front matter
    fingerprint: str


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_knowledge(root: Path) -> dict[str, KnowledgeFile]:
    """All Markdown files except README.md and files starting with '_'."""
    files: dict[str, KnowledgeFile] = {}
    for p in sorted(root.rglob("*.md")):
        if p.name.lower() == "readme.md" or p.name.startswith("_"):
            continue
        text = p.read_text(encoding="utf-8")
        meta: dict = {}
        m = _FRONT_MATTER.match(text)
        if m:
            meta = yaml.safe_load(m.group(1)) or {}
        rel = p.relative_to(root).as_posix()
        files[rel] = KnowledgeFile(
            path=rel,
            title=str(meta.get("title") or p.stem),
            url=meta.get("url"),
            text=text,
            fingerprint=fingerprint(text),
        )
    return files


def section_ids(sections_file: Path) -> set[str]:
    """Page section ids (nav items) declared in the frontend, plus the hero anchor."""
    text = sections_file.read_text(encoding="utf-8")
    block = re.search(r"navItems\s*=\s*\[(.*?)\]", text, re.S)
    ids = set(re.findall(r"id:\s*'([a-z][a-z0-9-]*)'", block.group(1) if block else ""))
    return ids | {"top"}


def allowed_links(kb: dict[str, KnowledgeFile], sections: set[str]) -> list[str]:
    urls = sorted({f.url for f in kb.values() if f.url})
    return [f"#{s}" for s in sorted(sections)] + urls


def render_for_prompt(kb: dict[str, KnowledgeFile]) -> str:
    return "\n\n".join(f'<file path="{f.path}">\n{f.text.strip()}\n</file>' for f in kb.values())
