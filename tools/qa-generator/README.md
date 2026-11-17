# Q&A generator (offline)

Drafts the portfolio assistant's prepared answers from `knowledge/` with the Gemini API and keeps them in
`frontend/src/data/qa.json`. Nothing here runs in production — the website is static.

```
knowledge/*.md ──generate──▶ qa.json (draft) ──you review/edit──▶ approve ──▶ git push ──▶ GitHub Pages
                                  │                                                 (approved items only)
                                  └──▶ qa-eval.json (matcher test questions)
```

## Setup

```bash
cd tools/qa-generator
uv sync
cp .env.example .env        # add GEMINI_API_KEY (https://aistudio.google.com/apikey)
```

## Workflow

```bash
uv run python -m qa_generator.cli generate            # draft new items / refresh changed ones
uv run python -m qa_generator.cli status              # what still needs review
git diff ../../frontend/src/data/qa.json              # read every change
#   …edit answers directly in qa.json if needed (your edits are protected from now on)
uv run python -m qa_generator.cli approve who-is-mohamed contact     # or: approve --all
uv run python -m qa_generator.cli validate
cd ../../frontend && npm test && npm run dev          # try it; drafts are visible locally with a badge
git commit -am "Update Q&A" && git push               # Pages rebuilds and publishes approved items
```

Other commands:

| Command | |
|---|---|
| `generate --dry-run` | show what would change, write nothing |
| `generate --max-new 5` | cap the number of new items per run |
| `github mmm-megahed/<repo>` | save a repository README as `knowledge/projects/<repo>-readme.md` |
| `stamp` | fill missing knowledge fingerprints after adding an item by hand |

## How regeneration treats your work

Each item records the fingerprints of the knowledge files it is based on (`source_files`) and a hash of the text
the generator wrote (`generated_hash`).

| Item state | Its knowledge file changed → |
|---|---|
| draft, never edited | regenerated (EN → DE/AR translation → new test questions) |
| edited by you (text ≠ generated) | **kept**, status → `needs-review` |
| approved | **kept**, status → `needs-review` |
| — new knowledge file not covered by any item | new draft items are created |

`approve` records the current fingerprints, so an approved item stays approved until its sources change again.

## What Gemini is asked to do

- Use **only** facts in `knowledge/` (passed whole — the knowledge base is small, no vector DB needed), ≤120 words,
  Markdown, cite 1–3 sources from an allow-list (page sections + repository URLs from front matter).
- Translate the English answer to German and Arabic (same facts), but write paraphrases **natively** per language.
- Produce reworded positives and off-topic negatives for `qa-eval.json`.

Outputs use Gemini structured output (Pydantic schemas) and are sanitized: ids are slugified and unique, unknown
links and files are dropped, and items that cite no real knowledge file are discarded. The model can never rename
an existing item. Default model: `gemini-3.8-flash` (`GEMINI_MODEL` to change).

## Tests

```bash
uv run pytest -q && uv run ruff check .
```

The frontend side (`frontend/src/qa/*.test.ts`) tests the matcher and runs a threshold sweep on `qa-eval.json`;
after large content changes, check its output and adjust `DEFAULT_THRESHOLD` in `frontend/src/qa/matcher.ts` if needed.
