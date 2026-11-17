import pytest

from app.ingestion.chunking import chunk_text
from app.ingestion.cleaning import clean_pdf_text, clean_text


def test_short_text_is_single_chunk():
    chunks = chunk_text("Hello world.", 500, 50)
    assert len(chunks) == 1
    assert chunks[0].text == "Hello world."
    assert chunks[0].index == 0


def test_respects_chunk_size_and_overlap():
    para = " ".join(f"Sentence number {i} talks about retrieval." for i in range(200))
    chunks = chunk_text(para, 400, 80)
    assert len(chunks) > 5
    assert all(len(c.text) <= 400 for c in chunks)
    # Overlap: the start of each chunk repeats text from the end of the previous one.
    for prev, nxt in zip(chunks, chunks[1:], strict=False):
        head = nxt.text[:30]
        assert head.split()[0] in prev.text[-120:]


def test_heading_path_is_tracked():
    text = "# Project\nIntro text.\n\n## Architecture\n" + ("FastAPI and pgvector. " * 60) + "\n\n## Results\nDone."
    chunks = chunk_text(text, 300, 50)
    headings = {c.heading for c in chunks}
    assert "Project > Architecture" in headings


def test_headings_inside_code_blocks_are_ignored():
    text = "# Real\nSome text\n```\n# not a heading\n```\nmore"
    chunks = chunk_text(text, 1000, 100)
    assert all("not a heading" not in c.heading for c in chunks)


def test_duplicate_chunks_are_dropped():
    block = "Identical paragraph about embeddings. " * 20
    text = f"# A\n{block}\n\n# B\n{block}"
    chunks = chunk_text(text, 900, 0)
    texts = [" ".join(c.text.split()) for c in chunks]
    assert len(texts) == len(set(texts))


def test_overlap_must_be_smaller_than_size():
    with pytest.raises(ValueError):
        chunk_text("x", 100, 100)


def test_unbreakable_token_is_hard_split():
    chunks = chunk_text("a" * 1000, 300, 0)
    assert all(len(c.text) <= 300 for c in chunks)


def test_clean_text_removes_noise():
    raw = "Title\u200b\n\n\n\n![badge](x.svg) [![b](y.svg)](z) <img src='a.png'> <!-- hidden -->text  here\x07"
    out = clean_text(raw)
    assert "\u200b" not in out and "\x07" not in out
    assert "badge" not in out and "img" not in out and "hidden" not in out
    assert "\n\n\n" not in out
    assert "text here" in out


def test_clean_pdf_text_joins_lines():
    assert clean_pdf_text("infor-\nmation retri-\neval\nsystem") == "information retrieval system"
