# Knowledge base

Source documents for the portfolio AI assistant. This folder is **independent of the website**:
edit or add files here and run `python -m app.cli sync --prune` (see `backend/README.md`) — no frontend
rebuild is needed.

## Rules

- **Only verified facts.** The assistant is instructed to answer *only* from these documents. Anything written here
  may be repeated to recruiters. Do not add metrics, dates, or claims you cannot back up.
- One topic per file. Short, well-headed sections retrieve better than long walls of text.
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

PDFs (e.g. a CV) can be placed in a category folder too; their title/label come from the PDF metadata or file name,
or can be set with `python -m app.cli add file.pdf --category profile --label "Professional CV"`.

GitHub READMEs are ingested with `python -m app.cli github owner/repo`.
