# Mohamed Megahed — AI Engineer Portfolio

Portfolio website plus a RAG-based AI assistant that answers visitor questions about my background,
grounded in a version-controlled knowledge base.

```
my_Portfolio/
├── frontend/     React 19 + TypeScript + Vite + Tailwind v4 + Motion → static site on GitHub Pages
├── backend/      FastAPI + Google Gen AI SDK (Gemini) + PostgreSQL/pgvector → deployed separately
├── knowledge/    Markdown knowledge base for the assistant (independent of the website)
└── .github/workflows/
    ├── deploy-pages.yml   builds and deploys the frontend to GitHub Pages
    └── backend-ci.yml     lint + tests (incl. pgvector integration) + Docker build
```

## Architecture

```
GitHub Pages (static)                     Backend host (Cloud Run / Render / Fly / VPS)
┌──────────────────────┐   POST /api/chat  ┌───────────────────────────────────────────┐
│ React portfolio      │ ───────────────▶  │ FastAPI                                   │
│  └ Chat widget (SSE) │ ◀─── stream ────  │  rate limit · CORS · size limits · timeouts│
└──────────────────────┘                   │  Retriever ─▶ Gemini embeddings            │
                                           │      └▶ PostgreSQL + pgvector (hybrid)     │
                                           │  Generator ─▶ Gemini (streaming)           │
                                           └───────────────────────────────────────────┘
knowledge/*.md ──(python -m app.cli sync)──▶ chunk → embed → pgvector   (no frontend rebuild)
```

The site works without the backend: if `VITE_CHAT_API_URL` is not set at build time, the chat button is simply not
rendered.

---

## 1. Local development

### Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (uses .env.development → chat API at http://localhost:8000)
npm run lint           # oxlint
npm run build          # type-check + production build into dist/
npm run preview        # serve the production build
```

### Backend (assistant)

```bash
cd backend
cp .env.example .env               # set GEMINI_API_KEY
docker compose up -d --build       # PostgreSQL + pgvector and the API on http://localhost:8000
docker compose run --rm api python -m app.cli sync --prune          # index knowledge/
docker compose run --rm api python -m app.cli github mmm-megahed/MR.Multi.RAG-Moodle
docker compose run --rm api python -m app.cli github mmm-megahed/MedEntity_NER_spaCy
curl localhost:8000/ready
```

No Gemini key yet? Set `AI_PROVIDER=fake` and `RETRIEVAL_MIN_SCORE=0.1` in `.env` to run the whole stack with
deterministic offline stand-ins (useful for UI work; answers are extractive and not meaningful).

See [`backend/README.md`](backend/README.md) for the API, configuration, knowledge-base administration, tests, and
evaluation.

---

## 2. Publish on GitHub Pages

1. **Create the repository** on GitHub under `mmm-megahed`:
   - `mmm-megahed.github.io` → site at `https://mmm-megahed.github.io/` (recommended for a portfolio), or
   - any name, e.g. `portfolio` → site at `https://mmm-megahed.github.io/portfolio/`.

   The workflow detects which case applies and sets the Vite base path (`/` or `/<repo>/`) automatically.

2. **Push** this folder:
   ```bash
   git remote add origin https://github.com/mmm-megahed/mmm-megahed.github.io.git
   git push -u origin main
   ```

3. **Enable Pages**: *Settings → Pages → Build and deployment → Source: GitHub Actions*.
   The `Deploy portfolio to GitHub Pages` workflow runs on every push to `main` that touches `frontend/`
   (or manually via *Actions → Run workflow*).

4. **Add your CV** (optional): put `frontend/public/cv/Mohamed_Megahed_CV.pdf` in the repo. The *Download CV*
   button only appears when that file exists at build time.

5. **Enable the assistant** once the backend is deployed (section 3): *Settings → Secrets and variables → Actions →
   Variables* → add `CHAT_API_URL` = `https://your-backend.example.com` (no trailing slash), then re-run the workflow.
   This is a public URL, not a secret — the Gemini key never leaves the backend.

### Custom domain (later)

1. Add a repository variable `CUSTOM_DOMAIN`, e.g. `megahed.dev`. The workflow then builds with base path `/`,
   uses it for canonical/Open Graph URLs, and writes `CNAME` into the artifact.
2. DNS at your registrar:
   - apex domain: `A` records → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
     (and `AAAA` → `2606:50c0:8000::153`, `…8001::153`, `…8002::153`, `…8003::153`)
   - subdomain (`www`/`portfolio`): `CNAME` → `mmm-megahed.github.io`
3. *Settings → Pages → Custom domain* → enter the domain, wait for the DNS check, then tick **Enforce HTTPS**.
4. Add the new origin to the backend's `ALLOWED_ORIGINS`.

---

## 3. Deploy the backend

GitHub Pages only serves static files, so the API runs elsewhere. It is a standard container
(`backend/Dockerfile`, listens on `$PORT`, health check at `/health`, readiness at `/ready`) and needs a PostgreSQL
database with the `pgvector` extension (e.g. Neon, Supabase, Cloud SQL, or a self-hosted `pgvector/pgvector` image).

Example — Google Cloud Run + a managed Postgres:

```bash
cd backend
gcloud run deploy portfolio-assistant --source . --region europe-west3 --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,ALLOWED_ORIGINS=https://mmm-megahed.github.io,TRUST_PROXY_HEADERS=true \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest,DATABASE_URL=portfolio-db-url:latest \
  --max-instances 1
```

Production checklist:

- `ENVIRONMENT=production` (disables `/docs`, rejects `AI_PROVIDER=fake` and wildcard origins).
- `ALLOWED_ORIGINS` = exactly your Pages origin (`https://mmm-megahed.github.io`, no path) and/or custom domain.
- `GEMINI_API_KEY` and `DATABASE_URL` from the platform's secret manager — never in the repo.
- `TRUST_PROXY_HEADERS=true` only behind a load balancer that sets `X-Forwarded-For` (Cloud Run, Render, Fly).
- Keep `DAILY_REQUEST_BUDGET` and the per-IP limits conservative; set a billing budget/alert in Google AI Studio.
- Sessions and rate-limit counters are in memory: run **one instance** (or replace them with Redis).
- `METRICS_TOKEN` set if `/metrics` is reachable publicly.
- Index the knowledge base against the production DB:
  `DATABASE_URL=… GEMINI_API_KEY=… uv run python -m app.cli sync --prune` (from `backend/`).

---

## 4. Updating content

| What changed | Do |
|---|---|
| Website text, projects, skills | edit `frontend/src/data/*.ts`, push → Pages redeploys |
| Assistant knowledge | edit/add `knowledge/**/*.md`, then `python -m app.cli sync --prune` — no frontend deploy |
| New GitHub project | `python -m app.cli github mmm-megahed/<repo>` (+ add a case study in `frontend/src/data/projects.ts`) |
| CV as PDF for the assistant | `python -m app.cli add cv.pdf --category profile --label "Professional CV"` |

Everything in `knowledge/` may be quoted to visitors — keep it factual.

## 5. Notes

- Fonts are self-hosted (`@fontsource`), no third-party requests from the site — relevant for GDPR in Germany.
- A German personal site used for job-seeking may need an *Impressum* and a privacy notice (the assistant sends
  visitor questions to Google Gemini). Add them before promoting the site widely.
