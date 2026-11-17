import httpx
import pytest

from qa_generator.github import clean_readme, import_readme
from qa_generator.knowledge import load_knowledge
from qa_generator.schema import EvalCase, EvalFile, Localized, QAFile, QAItem, Source
from qa_generator.validate import validate
from tests.conftest import loc

SECTIONS = {"about", "projects", "contact", "top"}


def item(**kw) -> QAItem:
    base = dict(
        id="a",
        category="profile",
        status="approved",
        sources=[Source(label="About", href="#about")],
        i18n={lang: loc("Who is Mohamed?", lang) for lang in ("en", "de", "ar")},
    )
    base.update(kw)
    return QAItem(**base)


def test_valid_file_passes():
    r = validate(QAFile(items=[item()]), SECTIONS)
    assert r.ok, r.errors


def test_missing_translation_is_an_error():
    i = item()
    del i.i18n["ar"]
    assert any("missing 'ar'" in e for e in validate(QAFile(items=[i]), SECTIONS).errors)


def test_broken_section_link_is_an_error():
    r = validate(QAFile(items=[item(sources=[Source(label="x", href="#nowhere")])]), SECTIONS)
    assert any("#nowhere" in e for e in r.errors)


def test_empty_answer_and_paraphrase_count():
    i = item()
    i.i18n["en"] = Localized(question="Who?", answer="  ", paraphrases=["one"])
    errors = validate(QAFile(items=[i]), SECTIONS).errors
    assert any("empty en answer" in e for e in errors)
    assert any("paraphrases" in e for e in errors)


def test_arabic_must_be_arabic_and_answers_bounded():
    i = item()
    i.i18n["ar"] = loc("Who?", "en")
    i.i18n["en"].answer = "word " * 200
    errors = validate(QAFile(items=[i]), SECTIONS).errors
    assert any("no Arabic script" in e for e in errors)
    assert any("words" in e for e in errors)


def test_duplicate_ids_unknown_related_and_eval_refs():
    qa = QAFile(items=[item(), item(related=["ghost"])])
    ev = EvalFile(cases=[EvalCase(text="x", lang="en", expected="missing")])
    errors = validate(qa, SECTIONS, ev=ev).errors
    assert any("duplicate ids" in e for e in errors)
    assert any("ghost" in e for e in errors)
    assert any("unknown id 'missing'" in e for e in errors)


def test_missing_knowledge_file(tmp_path):
    (tmp_path / "p").mkdir()
    (tmp_path / "p/a.md").write_text("x")
    kb = load_knowledge(tmp_path)
    r = validate(QAFile(items=[item(source_files={"p/gone.md": "abc"})]), SECTIONS, kb)
    assert any("not found" in e for e in r.errors)


def test_no_approved_items_warns():
    r = validate(QAFile(items=[item(status="draft")]), SECTIONS)
    assert r.ok and any("no approved" in w for w in r.warnings)


def test_clean_readme():
    raw = "# T\n[![b](x.svg)](y)\n![img](a.png)\n<img src=x>\n<!-- c -->\n\n\n\nText"
    assert clean_readme(raw) == "# T\n\nText"


def test_import_readme(tmp_path):
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/repos/owner/My.Repo/readme"
        return httpx.Response(200, text="# Repo\n![b](x.png)\nFastAPI service.")

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        path = import_readme("owner/My.Repo", tmp_path, client=c)
    assert path.name == "my-repo-readme.md"
    kb = load_knowledge(tmp_path)
    f = kb["projects/my-repo-readme.md"]
    assert f.url == "https://github.com/owner/My.Repo"
    assert "FastAPI service." in f.text and "x.png" not in f.text
    with pytest.raises(FileExistsError):
        import_readme("owner/My.Repo", tmp_path, client=c)


def test_import_readme_rejects_bad_names(tmp_path):
    with pytest.raises(ValueError):
        import_readme("not a repo", tmp_path)
