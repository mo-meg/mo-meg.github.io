from pathlib import Path

import httpx
import pytest

from app.ingestion.loaders import LoaderError, discover, load_file, load_github_readme, load_markdown
from app.ingestion.pipeline import Ingestor
from tests.conftest import KNOWLEDGE_DIR, make_doc


def _write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_markdown_front_matter(tmp_path: Path):
    p = _write(
        tmp_path / "projects" / "x.md",
        "---\ntitle: X Project\nsource_label: X Docs\nurl: https://example.com\nyear: 2025\n---\n# X\nBody text.",
    )
    d = load_markdown(p, tmp_path)
    assert d.source_id == "file:projects/x.md"
    assert d.title == "X Project"
    assert d.source_label == "X Docs"
    assert d.category == "projects"  # from folder
    assert d.url == "https://example.com"
    assert d.metadata["year"] == 2025
    assert "Body text." in d.text


def test_unknown_category_rejected(tmp_path: Path):
    p = _write(tmp_path / "misc" / "x.md", "hello")
    with pytest.raises(LoaderError):
        load_markdown(p, tmp_path)


def test_files_outside_root_get_upload_prefix(tmp_path: Path):
    p = _write(tmp_path / "a.md", "---\ncategory: profile\n---\nhello")
    d = load_markdown(p, tmp_path / "elsewhere")
    assert d.source_id == "upload:a.md"


def test_discover_skips_readme_and_underscore(tmp_path: Path):
    _write(tmp_path / "README.md", "x")
    _write(tmp_path / "profile" / "_draft.md", "x")
    _write(tmp_path / "profile" / "real.md", "x")
    _write(tmp_path / "profile" / "notes.txt", "x")
    assert [p.name for p in discover(tmp_path)] == ["real.md"]


def test_repository_knowledge_base_is_valid():
    files = discover(KNOWLEDGE_DIR)
    assert len(files) >= 8
    for f in files:
        d = load_file(f, KNOWLEDGE_DIR)
        assert d.title and d.source_label and d.text


def _minimal_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % off for off in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, xref)
    return out


def test_pdf_loader(tmp_path: Path):
    p = tmp_path / "profile" / "Mohamed_CV.pdf"
    p.parent.mkdir()
    p.write_bytes(_minimal_pdf("Mohamed Megahed AI Engineer"))
    d = load_file(p, tmp_path, source_label="Professional CV")
    assert "Mohamed Megahed AI Engineer" in d.text
    assert d.category == "profile"
    assert d.source_label == "Professional CV"
    assert d.metadata["kind"] == "pdf"


async def test_github_readme_loader():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/owner/repo/readme"
        return httpx.Response(200, text="# Repo\n![badge](b.svg)\nA FastAPI service.")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        d = await load_github_readme("owner/repo", client=c)
    assert d.source_id == "github:owner/repo"
    assert d.url == "https://github.com/owner/repo"
    assert "badge" not in d.text and "FastAPI" in d.text


async def test_github_invalid_repo_name():
    with pytest.raises(LoaderError):
        await load_github_readme("not a repo")


async def test_incremental_ingestion(store, embedder):
    ing = Ingestor(store, embedder, 500, 50)
    doc = make_doc("file:a.md", "# A\nRetrieval augmented generation with pgvector.")

    assert await ing.ingest(doc) == "created"
    calls = embedder.calls
    assert await ing.ingest(make_doc("file:a.md", doc.text)) == "unchanged"
    assert embedder.calls == calls, "unchanged documents must not be re-embedded"

    assert await ing.ingest(make_doc("file:a.md", doc.text + "\nNew sentence.")) == "updated"
    assert (await store.stats())["documents"] == 1

    assert await ing.ingest(make_doc("file:a.md", doc.text + "\nNew sentence."), force=True) == "updated"


async def test_metadata_change_triggers_update(store, embedder):
    ing = Ingestor(store, embedder, 500, 50)
    await ing.ingest(make_doc("file:a.md", "Same text", title="Old"))
    assert await ing.ingest(make_doc("file:a.md", "Same text", title="New")) == "updated"
    rec = await store.get_document("file:a.md")
    assert rec and rec.title == "New"


async def test_duplicate_content_is_skipped(store, embedder):
    ing = Ingestor(store, embedder, 500, 50)
    await ing.ingest(make_doc("file:a.md", "Exactly the same content."))
    assert await ing.ingest(make_doc("upload:copy.md", "Exactly   the same content.")) == "duplicate"
    assert (await store.stats())["documents"] == 1


async def test_prune_removes_deleted_files_only(store, embedder):
    ing = Ingestor(store, embedder, 500, 50)
    await ing.ingest(make_doc("file:keep.md", "keep me"))
    await ing.ingest(make_doc("file:gone.md", "delete me"))
    await ing.ingest(make_doc("github:o/r", "readme"))
    removed = await ing.prune({"file:keep.md"})
    assert removed == ["file:gone.md"]
    ids = {d.source_id for d in await store.list_documents()}
    assert ids == {"file:keep.md", "github:o/r"}


async def test_ingest_many_reports_errors(store, embedder):
    class Broken:
        model_name = "broken"
        dim = 8

        async def embed_documents(self, texts, titles=None):
            raise RuntimeError("quota")

    ing = Ingestor(store, Broken(), 500, 50)  # type: ignore[arg-type]
    report = await ing.ingest_many([make_doc("file:a.md", "x")])
    assert "file:a.md" in report.errors
    assert report.summary()["errors"] == 1
