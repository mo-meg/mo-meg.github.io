"""Structure-aware chunking.

1. Split Markdown into sections by headings, keeping the heading path ("Project > Architecture").
2. Merge small neighbouring sections so chunks are not trivially short.
3. Split long sections on paragraph → sentence → word boundaries, packing up to ``chunk_size``
   characters and carrying ``overlap`` characters of trailing context into the next chunk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import Chunk

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_SENTENCE_END = re.compile(r"(?<=[.!?。؟])\s+")


@dataclass
class _Section:
    heading_path: list[str]
    body: str


def _split_sections(text: str) -> list[_Section]:
    sections: list[_Section] = []
    path: list[tuple[int, str]] = []
    buf: list[str] = []
    in_code = False

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            sections.append(_Section([t for _, t in path], body))
        buf.clear()

    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
        m = None if in_code else _HEADING.match(line)
        if m:
            flush()
            level = len(m.group(1))
            path = [(lvl, t) for lvl, t in path if lvl < level]
            path.append((level, m.group(2).strip()))
        else:
            buf.append(line)
    flush()
    return sections


def _split_long(text: str, size: int) -> list[str]:
    """Break text into pieces no longer than ``size`` on the most natural boundary available."""
    if len(text) <= size:
        return [text]
    for splitter in (re.compile(r"\n\s*\n"), re.compile(r"\n"), _SENTENCE_END, re.compile(r"\s+")):
        parts = [p.strip() for p in splitter.split(text) if p.strip()]
        if len(parts) > 1:
            out: list[str] = []
            for p in parts:
                out.extend(_split_long(p, size))
            return out
    # A single unbreakable token longer than size: hard cut.
    return [text[i : i + size] for i in range(0, len(text), size)]


def _tail(text: str, overlap: int) -> str:
    """Last ~overlap characters of text, starting at a word boundary."""
    if overlap <= 0 or len(text) <= overlap:
        return text if overlap > 0 else ""
    cut = text[-overlap:]
    space = cut.find(" ")
    return cut[space + 1 :] if 0 <= space < len(cut) - 1 else cut


def _pack(pieces: list[str], size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = f"{current}\n\n{piece}" if current else piece
        if len(candidate) <= size:
            current = candidate
            continue
        if current:
            chunks.append(current)
            carry = _tail(current, overlap)
            current = f"{carry} {piece}".strip() if carry and len(carry) + len(piece) + 1 <= size else piece
        else:
            current = piece
    if current:
        chunks.append(current)
    return chunks


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[Chunk]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    sections = _split_sections(text)

    # Merge consecutive short sections (keeping their headings inline) to avoid tiny chunks.
    merged: list[_Section] = []
    for s in sections:
        rendered = s.body
        if merged:
            prev = merged[-1]
            heading_line = f"{s.heading_path[-1]}:\n" if s.heading_path and s.heading_path != prev.heading_path else ""
            combined = f"{prev.body}\n\n{heading_line}{rendered}"
            if len(prev.body) < chunk_size // 3 and len(combined) <= chunk_size:
                merged[-1] = _Section(prev.heading_path, combined)
                continue
        merged.append(_Section(s.heading_path, rendered))

    chunks: list[Chunk] = []
    seen: set[str] = set()
    for s in merged:
        heading = " > ".join(s.heading_path)
        budget = chunk_size
        for piece in _pack(_split_long(s.body, budget), budget, overlap):
            norm = " ".join(piece.split()).lower()
            if norm in seen:  # drop exact duplicate chunks within a document
                continue
            seen.add(norm)
            chunks.append(Chunk(index=len(chunks), text=piece, heading=heading))
    return chunks
