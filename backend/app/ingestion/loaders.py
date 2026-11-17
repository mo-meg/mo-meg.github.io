"""Load Markdown, PDF, and GitHub README sources into ``SourceDocument`` objects."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import httpx
import yaml
from pypdf import PdfReader

from app.config import KNOWN_CATEGORIES
from app.ingestion.cleaning import clean_pdf_text, clean_text
from app.models import SourceDocument

SUPPORTED_SUFFIXES = {".md", ".markdown", ".pdf"}
_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class LoaderError(ValueError):
    pass


def _source_id_for(path: Path, root: Path | None) -> str:
    """'file:<relative path>' for files in the knowledge dir (managed by `sync --prune`),
    'upload:<name>' for files added from elsewhere."""
    if root:
        try:
            return f"file:{path.resolve().relative_to(root.resolve()).as_posix()}"
        except ValueError:
            pass
    return f"upload:{path.name}"


def _category(meta: dict[str, Any], path: Path, root: Path | None, override: str | None) -> str:
    cat = override or meta.get("category")
    if not cat and root:
        try:
            cat = path.resolve().relative_to(root.resolve()).parts[0]
        except (ValueError, IndexError):
            cat = None
    cat = str(cat or "documents").strip().lower()
    if cat not in KNOWN_CATEGORIES:
        raise LoaderError(f"{path}: unknown category '{cat}'. Use one of: {', '.join(KNOWN_CATEGORIES)}")
    return cat


def parse_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    m = _FRONT_MATTER.match(raw)
    if not m:
        return {}, raw
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise LoaderError("front matter must be a YAML mapping")
    return meta, raw[m.end() :]


def load_markdown(path: Path, root: Path | None = None, **overrides: Any) -> SourceDocument:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    title = overrides.get("title") or meta.get("title") or path.stem.replace("-", " ").title()
    text = clean_text(body)
    if not text:
        raise LoaderError(f"{path}: document is empty")
    extra = {k: v for k, v in meta.items() if k not in {"title", "category", "source_label", "url"}}
    return SourceDocument(
        source_id=_source_id_for(path, root),
        title=str(title),
        source_label=str(overrides.get("source_label") or meta.get("source_label") or title),
        category=_category(meta, path, root, overrides.get("category")),
        url=overrides.get("url") or meta.get("url"),
        text=text,
        metadata={"kind": "markdown", "path": path.name, **extra},
    )


def load_pdf(path: Path, root: Path | None = None, **overrides: Any) -> SourceDocument:
    reader = PdfReader(str(path))
    pages = [(p.extract_text() or "") for p in reader.pages]
    text = clean_pdf_text("\n\n".join(pages))
    if not text:
        raise LoaderError(f"{path}: no extractable text (scanned PDF?)")
    title = overrides.get("title") or (reader.metadata.title if reader.metadata and reader.metadata.title else None)
    title = str(title or path.stem.replace("_", " ").replace("-", " "))
    return SourceDocument(
        source_id=_source_id_for(path, root),
        title=title,
        source_label=str(overrides.get("source_label") or title),
        category=_category({}, path, root, overrides.get("category")),
        url=overrides.get("url"),
        text=text,
        metadata={"kind": "pdf", "path": path.name, "pages": len(pages)},
    )


def load_file(path: Path, root: Path | None = None, **overrides: Any) -> SourceDocument:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return load_markdown(path, root, **overrides)
    if suffix == ".pdf":
        return load_pdf(path, root, **overrides)
    raise LoaderError(f"{path}: unsupported file type '{suffix}'")


def discover(root: Path) -> list[Path]:
    """All ingestible files under root. Files starting with '_' and README.md files are skipped."""
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_SUFFIXES
        and not p.name.startswith("_")
        and p.name.lower() != "readme.md"
    )


async def load_github_readme(
    repo: str,
    *,
    category: str = "projects",
    title: str | None = None,
    source_label: str | None = None,
    token: str = "",
    client: httpx.AsyncClient | None = None,
) -> SourceDocument:
    if not _REPO.match(repo):
        raise LoaderError(f"invalid repository '{repo}', expected owner/name")
    if category not in KNOWN_CATEGORIES:
        raise LoaderError(f"unknown category '{category}'")
    headers = {"Accept": "application/vnd.github.raw", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    own = client is None
    client = client or httpx.AsyncClient(timeout=20)
    try:
        r = await client.get(f"https://api.github.com/repos/{repo}/readme", headers=headers)
        if r.status_code == 404:
            raise LoaderError(f"{repo}: README not found (private repository or no README)")
        r.raise_for_status()
        text = clean_text(r.text)
    finally:
        if own:
            await client.aclose()
    name = repo.split("/", 1)[1]
    return SourceDocument(
        source_id=f"github:{repo}",
        title=title or f"{name} — GitHub README",
        source_label=source_label or f"{name} – GitHub README",
        category=category,
        url=f"https://github.com/{repo}",
        text=text,
        metadata={"kind": "github", "repo": repo},
    )
