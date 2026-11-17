"""Text normalization applied to every document before chunking."""

from __future__ import annotations

import re
import unicodedata

_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_IMG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_HTML_TAG = re.compile(
    r"</?(?:div|span|p|br|hr|picture|source|a|sup|sub|center|details|summary)\b[^>]*>", re.IGNORECASE
)
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_BADGE_LINK = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)")
_TRAILING_WS = re.compile(r"[ \t]+\n")
_MULTI_BLANK = re.compile(r"\n{3,}")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


def clean_text(text: str) -> str:
    """Normalize unicode, strip invisible/control characters, images, badges and layout HTML."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _ZERO_WIDTH.sub("", text)
    text = _CONTROL.sub("", text)
    text = _HTML_COMMENT.sub("", text)
    text = _MD_BADGE_LINK.sub("", text)
    text = _MD_IMAGE.sub("", text)
    text = _HTML_IMG.sub("", text)
    text = _HTML_TAG.sub("", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _TRAILING_WS.sub("\n", text)
    text = _MULTI_BLANK.sub("\n\n", text)
    return text.strip()


def clean_pdf_text(text: str) -> str:
    """PDF extraction artefacts: hyphenated line breaks and hard-wrapped lines."""
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Join single newlines inside paragraphs, keep blank-line paragraph breaks.
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    return clean_text(text)
