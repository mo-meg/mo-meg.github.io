from qa_generator.knowledge import load_knowledge, section_ids
from qa_generator.llm import EnglishDraft
from qa_generator.pipeline import approve, run_generate, stamp
from qa_generator.schema import QAFile, QAItem, Source
from qa_generator.store import load_eval, load_qa, save_qa
from tests.conftest import FakeWriter, loc, write


def test_first_run_creates_drafts_for_every_file(repo):
    w = FakeWriter()
    r = run_generate(repo, w, max_new=10, negatives_target=4)
    qa = load_qa(repo.qa_file)
    assert sorted(r.created) == ["about-job", "about-rag"]
    assert all(i.status == "draft" and not i.edited for i in qa.items)
    assert set(qa.items[0].i18n) == {"en", "de", "ar"}
    kb = load_knowledge(repo.knowledge)
    item = qa.get("about-job")
    assert item and item.source_files == {"experience/job.md": kb["experience/job.md"].fingerprint}
    ev = load_eval(repo.eval_file)
    assert sum(1 for c in ev.cases if c.expected is None) == 4
    assert {c.expected for c in ev.cases if c.expected} == {"about-job", "about-rag"}
    assert r.validation and r.validation.ok, r.validation.errors


def test_second_run_without_changes_is_a_noop(repo):
    run_generate(repo, FakeWriter(), negatives_target=2)
    before = repo.qa_file.read_text()
    w = FakeWriter()
    r = run_generate(repo, w, negatives_target=2)
    assert r.created == [] and r.regenerated == [] and r.flagged == []
    assert not any(c.startswith(("plan", "rewrite", "translate")) for c in w.calls)
    assert repo.qa_file.read_text() == before


def test_changed_knowledge_regenerates_unedited_draft(repo):
    run_generate(repo, FakeWriter(), negatives_target=0)
    write(repo.knowledge / "experience/job.md", "---\ntitle: Job\n---\n# Job\nAI Engineer at Prolumios. NEW FACT.")
    r = run_generate(repo, FakeWriter(), negatives_target=0)
    assert r.regenerated == ["about-job"]
    item = load_qa(repo.qa_file).get("about-job")
    assert item and "(updated)" in item.i18n["en"].answer
    assert item.id == "about-job", "the model must not be able to rename an item"
    assert item.status == "draft"


def test_human_edits_are_never_overwritten(repo):
    run_generate(repo, FakeWriter(), negatives_target=0)
    qa = load_qa(repo.qa_file)
    item = qa.get("about-job")
    assert item
    item.i18n["en"].answer = "My carefully edited answer."
    save_qa(repo.qa_file, qa)

    write(repo.knowledge / "experience/job.md", "changed")
    w = FakeWriter()
    r = run_generate(repo, w, negatives_target=0)
    assert r.flagged == ["about-job"] and r.regenerated == []
    item = load_qa(repo.qa_file).get("about-job")
    assert item and item.i18n["en"].answer == "My carefully edited answer."
    assert item.status == "needs-review"
    assert "rewrite:about-job" not in w.calls


def test_approved_items_are_flagged_not_rewritten_and_reapproval_refreshes(repo):
    run_generate(repo, FakeWriter(), negatives_target=0)
    approve(repo, ["about-rag"])
    write(repo.knowledge / "projects/rag.md", "---\ntitle: RAG\n---\nchanged")
    r = run_generate(repo, FakeWriter(), negatives_target=0)
    assert r.flagged == ["about-rag"]
    assert load_qa(repo.qa_file).get("about-rag").status == "needs-review"

    approve(repo, ["about-rag"])
    r = run_generate(repo, FakeWriter(), negatives_target=0)
    assert r.flagged == [] and load_qa(repo.qa_file).get("about-rag").status == "approved"


def test_new_knowledge_file_gets_new_items_only(repo):
    run_generate(repo, FakeWriter(), negatives_target=0)
    write(repo.knowledge / "projects/ner.md", "---\ntitle: NER\n---\nspaCy NER")
    w = FakeWriter()
    r = run_generate(repo, w, negatives_target=0)
    assert r.created == ["about-ner"]
    assert any(c.startswith("plan:projects/ner.md") for c in w.calls)


def test_model_output_is_sanitized(repo):
    bad = EnglishDraft(
        id="Weird ID!!",
        category="projects",
        question="What is Q?",
        answer="A",
        paraphrases=["What is Q?", "p1", "p1", "p2", "p3", "p4", "p5"] + [f"x{n}" for n in range(10)],
        sources=[
            Source(label="evil", href="https://evil.example"),
            Source(label="ok", href="https://github.com/o/rag"),
        ],
        source_files=["projects/rag.md", "does/not/exist.md"],
    )
    ungrounded = bad.model_copy(update={"id": "ungrounded", "source_files": ["nope.md"]})
    r = run_generate(repo, FakeWriter(plan_items=[bad, ungrounded]), negatives_target=0)
    assert r.created == ["weird-id"], "items citing no real knowledge file are dropped"
    item = load_qa(repo.qa_file).get("weird-id")
    assert item
    assert [s.href for s in item.sources] == ["https://github.com/o/rag"]
    assert list(item.source_files) == ["projects/rag.md"]
    assert "What is Q?" not in item.i18n["en"].paraphrases
    assert len(item.i18n["en"].paraphrases) == 10


def test_dry_run_writes_nothing(repo):
    run_generate(repo, FakeWriter(), dry_run=True)
    assert not repo.qa_file.exists()


def test_stamp_fills_fingerprints_for_hand_written_items(repo):
    item = QAItem(
        id="hand",
        category="profile",
        sources=[Source(label="About", href="#about")],
        source_files={"experience/job.md": ""},
        i18n={lang: loc("Who?", lang) for lang in ("en", "de", "ar")},
    )
    save_qa(repo.qa_file, QAFile(items=[item]))
    stamp(repo)
    item = load_qa(repo.qa_file).get("hand")
    assert item and item.source_files["experience/job.md"]
    assert item.edited, "without --mark-generated a hand-written item stays protected"
    stamp(repo, mark_generated=True)
    assert not load_qa(repo.qa_file).get("hand").edited


def test_section_ids_parsed_from_frontend(repo):
    assert section_ids(repo.sections_file) == {"about", "projects", "experience", "contact", "top"}
