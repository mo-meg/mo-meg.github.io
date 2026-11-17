# Knowledge base

Source of truth for the portfolio's Q&A assistant. The offline generator (`tools/qa-generator`) drafts questions and
answers from these files into `frontend/src/data/qa.json`; you review and approve them, then push.

## Rules

- **Only verified facts.** The generator is instructed to answer *only* from these documents. Anything written here
  may be repeated to recruiters. Do not add metrics, dates, or claims you cannot back up.
- One topic per file. Short, well-headed sections produce better questions.
- Files starting with `_` and `README.md` files are ignored.

## Format

Markdown with YAML front matter:

```markdown
---
title: Prolumios — AI Engineer            # document title
source_label: Prolumios Project Description  # shown to visitors as the citation
category: experience                       # defaults to the folder name
url: https://github.com/...                # optional; makes the citation clickable
---

# Heading
Content…
```

Categories: `profile`, `skills`, `rag-llm`, `ml-nlp`, `cloud-devops`, `experience`, `education`, `projects`,
`contact`, `documents`.

The generator reads Markdown only. To add a CV, summarize it into a Markdown file in `profile/`.

GitHub READMEs are imported as Markdown with
`uv run python -m qa_generator.cli github owner/repo` (run in `tools/qa-generator`).
