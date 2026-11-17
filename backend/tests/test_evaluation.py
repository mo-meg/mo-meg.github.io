import json

from app.evaluation import ABSTAIN_PATTERNS, DATASET, Row, summarize


def test_dataset_is_well_formed():
    items = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(items) >= 20
    assert len({i["id"] for i in items}) == len(items)
    assert any(not i["answerable"] for i in items), "dataset must contain unanswerable questions"
    for i in items:
        assert i["answerable"] == bool(i["expected_sources"])


def test_summary_metrics():
    rows = [
        Row(
            "a",
            True,
            ["x", "y"],
            hit=True,
            recall=1.0,
            rr=1.0,
            answer="A [S1]",
            cited=["S1"],
            keyword_ok=True,
            faithful=True,
            abstained=False,
        ),
        Row(
            "b",
            True,
            ["z"],
            hit=False,
            recall=0.0,
            rr=0.0,
            answer="B",
            keyword_ok=False,
            faithful=True,
            abstained=False,
        ),
        Row("c", False, [], answer="This information is not currently available.", faithful=True, abstained=True),
    ]
    s = summarize(rows)
    assert s["hit@k"] == 0.5 and s["mrr"] == 0.5
    assert s["abstained_when_unanswerable"] == 1.0
    assert s["cited_when_answerable"] == 0.5


def test_abstain_patterns_multilingual():
    assert ABSTAIN_PATTERNS.search("That information is not currently available in the knowledge base.")
    assert ABSTAIN_PATTERNS.search("Diese Information ist nicht verfügbar.")
    assert ABSTAIN_PATTERNS.search("هذه المعلومات غير متوفرة")
