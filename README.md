# Mohamed Megahed — AI Engineer Portfolio

A fully static portfolio site (GitHub Pages) with a multilingual assistant that answers visitor questions with
**prepared, human-reviewed answers** — no backend, no API key in the browser, nothing to host.

```
my_Portfolio/
├── frontend/            React 19 + TypeScript + Vite + Tailwind v4 + Motion  → GitHub Pages
│   ├── src/data/qa.json        the assistant's Q&A (EN/DE/AR, status draft/approved/needs-review)
│   ├── src/data/qa-eval.json   matcher test set (reworded + off-topic questions)
│   └── src/qa/                 in-browser matcher, language detection, validation
├── knowledge/           Markdown facts the Q&A is generated from (source of truth)
├── tools/qa-generator/  offline Python tool: Gemini drafts → you review → approve
└── .github/workflows/
    ├── deploy-pages.yml        lint + tests + validate + build + deploy
    └── qa-generator-ci.yml     generator tests + qa.json ↔ knowledge/ consistency
```

## How the assistant works

1. **Offline:** `tools/qa-generator` sends `knowledge/` to Gemini (structured output) and drafts questions, answers,
   sources, German/Arabic versions, paraphrases, and test questions into `qa.json`.
2. **Review:** you edit and `approve` items. Only approved items are compiled into the production bundle.
3. **In the browser:** visitors click a question or type their own. The matcher detects the language (EN/DE/AR),
   normalizes and stems the text, and scores it against every question and paraphrase. Above the threshold the
   prepared answer is shown in the visitor's language; below it, the visitor gets a pre-filled email to you,
   a LinkedIn link, and "did you mean…" suggestions. Typed questions never leave the browser.

Details: [`tools/qa-generator/README.md`](tools/qa-generator/README.md).

## Local development

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 — drafts are shown with a "draft" badge
npm test           # matcher + validation + threshold sweep
npm run lint
npm run build      # validates qa.json, type-checks, builds dist/ (approved items only)
npm run preview
```

Preview the production build *with* drafts: `QA_INCLUDE_DRAFTS=true npm run build && npm run preview`.

## Current state of the Q&A

`qa.json` contains **47 draft items** in English, German, and Arabic, written strictly from `knowledge/` so the site
works immediately. **None are approved yet**, so the published site hides the assistant until you review them:

```bash
cd tools/qa-generator && uv sync
uv run python -m qa_generator.cli status
uv run python -m qa_generator.cli approve <id> …     # or --all after reviewing
```

## Publish on GitHub Pages

1. The repository is `mo-meg/mo-meg.github.io` → site at `https://mo-meg.github.io/`. (Any other repo name would
   publish to `https://mo-meg.github.io/<repo>/`; the workflow detects which and sets the Vite base path.)
2. Push:
   ```bash
   git remote add origin https://github.com/mo-meg/mo-meg.github.io.git
   git push -u origin main
   ```
3. *Settings → Pages → Build and deployment → Source: **GitHub Actions***.
4. Optional: add `frontend/public/cv/Mohamed_Megahed_CV.pdf` — the *Download CV* button appears only when it exists.

### Custom domain (later)

1. Repository variable `CUSTOM_DOMAIN` (e.g. `megahed.dev`) — the workflow then builds with base `/`, uses it for
   canonical/Open Graph URLs, and writes `CNAME`.
2. DNS: apex → `A` 185.199.108.153 / .109.153 / .110.153 / .111.153 (and `AAAA` 2606:50c0:8000::153 … 8003::153);
   subdomain → `CNAME mo-meg.github.io`.
3. *Settings → Pages → Custom domain*, then **Enforce HTTPS**.

## Updating content

| Change | Do |
|---|---|
| Website sections (projects, skills, experience) | edit `frontend/src/data/*.ts`, push |
| Facts for the assistant | edit `knowledge/**/*.md` → `generate` → review → `approve` → push |
| New GitHub project | `uv run python -m qa_generator.cli github mmm-megahed/<repo>` → `generate` → review |
| An answer's wording | edit `frontend/src/data/qa.json` directly (protected from regeneration), push |
| New course or certificate | add one line to `frontend/src/data/training.ts` (+ `knowledge/education/training.md`), push — see below |

## Courses and certificates

All entries live in `frontend/src/data/training.ts`. To add one, append a line, e.g.

```ts
dc('Multi-Modal Systems with the OpenAI API', 'LLMs & Generative AI', { url: 'https://www.datacamp.com/statement-of-accomplishment/course/…' }),
{ title: 'AWS Certified AI Practitioner', provider: 'AWS', topic: 'DevOps, cloud & Git', kind: 'certification', year: 2026, url: 'https://…' },
```

- `url`: public verification link (preferred). Or `pdf: 'file.pdf'` with the file in `frontend/public/certificates/`
  (the build fails if it is missing).
- `featured: true` puts it in the "Highlights" list (keep ~10). `kind: 'certification'` is for exam-based
  certifications only; they are shown above the courses.
- Also add it to `knowledge/education/training.md`, then run the Q&A generator (`generate`) so the assistant's
  answer is refreshed for review.

## GitHub accounts

`github.com/mo-meg` is the main account (hero, footer, contact, structured data); `github.com/mmm-megahed` is linked
as "academic projects" (Moodle RAG, MedEntity). Both live in `frontend/src/data/profile.ts` (`github`, `githubAcademic`).
Prolumios work (commercial) is described only at a high level — no repository names or links.

## Notes

- Fonts are self-hosted; the site makes no third-party requests (relevant for GDPR in Germany).
- A German personal site used for job-seeking may need an *Impressum* and a short privacy notice.
