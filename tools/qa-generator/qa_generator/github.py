"""Import a GitHub README into knowledge/ as a Markdown file with front matter."""

from __future__ import annotations

import re
from pathlib import Path

import httpx
import yaml

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_CLEAN = [
    (re.compile(r"<!--.*?-->", re.S), ""),
    (re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)"), ""),  # badge links
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), ""),  # images
    (re.compile(r"<img\b[^>]*>", re.I), ""),
    (re.compile(r"</?(?:div|p|br|picture|source|center|a|sup|sub)\b[^>]*>", re.I), ""),
    (re.compile(r"\n{3,}"), "\n\n"),
]


def clean_readme(text: str) -> str:
    for pattern, repl in _CLEAN:
        text = pattern.sub(repl, text)
    return text.strip()


def import_readme(
    repo: str,
    knowledge_dir: Path,
    *,
    token: str = "",
    force: bool = False,
    client: httpx.Client | None = None,
) -> Path:
    if not _REPO.match(repo):
        raise ValueError(f"invalid repository '{repo}', expected owner/name")
    name = repo.split("/", 1)[1]
    target = knowledge_dir / "projects" / f"{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')}-readme.md"
    if target.exists() and not force:
        raise FileExistsError(f"{target} exists (use --force to overwrite)")

    headers = {"Accept": "application/vnd.github.raw", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    own = client is None
    client = client or httpx.Client(timeout=20)
    try:
        r = client.get(f"https://api.github.com/repos/{repo}/readme", headers=headers)
        if r.status_code == 404:
            raise FileNotFoundError(f"{repo}: README not found (private repository or no README)")
        r.raise_for_status()
        body = clean_readme(r.text)
    finally:
        if own:
            client.close()

    meta = {
        "title": f"{name} — GitHub README",
        "source_label": f"{name} – GitHub README",
        "category": "projects",
        "url": f"https://github.com/{repo}",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"---\n{yaml.safe_dump(meta, allow_unicode=True, sort_keys=False)}---\n\n{body}\n", encoding="utf-8"
    )
    return target
