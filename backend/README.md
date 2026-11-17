# Portfolio AI Assistant — backend

FastAPI service that answers questions about Mohamed Megahed with Retrieval-Augmented Generation:
Gemini embeddings + PostgreSQL/pgvector hybrid retrieval + Gemini generation, streamed over Server-Sent Events,
with source attribution.

## Pipelines

**Ingestion** (`app/ingestion/`, run via CLI — separate from chat):

```
Markdown / PDF / GitHub README
  → loaders.py    text extraction, YAML front matter (title, category, source_label, url)
  → cleaning.py   unicode normalization, strip badges/images/HTML/control chars
  → chunking.py   heading-aware split, merge tiny sections, paragraph→sentence→word packing, overlap
  → pipeline.py   heading-path enrichment, fingerprint (skip unchanged), dedupe identical docs,
                  batch embeddings (RETRIEVAL_DOCUMENT), atomic replace of a document's chunks
  → PostgreSQL    documents + chunks(vector(768), tsvector)  [HNSW + GIN indexes]
```

**Query** (`app/retrieval.py`, `app/prompts.py`, `app/rag.py`, `app/llm.py`):

```
question (+ previous question for follow-ups)
  → query embeddings (task: search result)
  → pgvector cosine top-N  ∪  Postgres full-text top-N   (optional category filter)
  → reciprocal rank fusion → similarity gate (RETRIEVAL_MIN_SCORE) → top-k
  → context grouped per document as [S1], [S2] … (untrusted, delimiter-neutralized)
  → Gemini (system instructions + bounded history + context) → SSE stream
  → only sources actually cited by the answer are returned
```

Gemini never replaces retrieval: when nothing passes the relevance gate the model receives `NONE` and is
instructed to say the information is not available.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | `{"message": str, "session_id"?: str, "categories"?: [str]}` → `text/event-stream` |
| `POST` | `/api/chat/reset` | `{"session_id": str}` — forget a conversation |
| `GET`  | `/health` | liveness |
| `GET`  | `/ready` | DB reachable and knowledge base non-empty (503 otherwise) |
| `GET`  | `/metrics` | Prometheus metrics (optionally bearer-protected) |

SSE events: `meta {session_id}` → `delta {text}`* → `sources {sources:[{id,title,label,url,category}]}` → `done`,
or `error {message, retryable}` at any point. Session ids are issued by the server; unknown ids start a new session.

## Configuration

All settings are environment variables — see [`.env.example`](.env.example). Key ones:

| Variable | Default | |
|---|---|---|
| `GEMINI_API_KEY` | — | required for `AI_PROVIDER=gemini` |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | any Gemini text model |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | `gemini-embedding-001` also supported (uses `task_type`) |
| `EMBEDDING_DIM` | `768` | baked into the DB column at first migration |
| `DATABASE_URL` | local | PostgreSQL with pgvector |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 1200 / 200 | characters |
| `RETRIEVAL_TOP_K` / `RETRIEVAL_MIN_SCORE` | 6 / 0.40 | tune with the evaluation script |
| `HISTORY_TURNS` / `SESSION_TTL_MINUTES` | 6 / 30 | in-memory conversation memory |
| `RATE_LIMIT_PER_MINUTE` / `_PER_DAY` / `DAILY_REQUEST_BUDGET` | 8 / 80 / 1500 | per hashed client IP / global |
| `ALLOWED_ORIGINS` | localhost:5173 | comma-separated CORS allow-list |

Model IDs change over time — check https://ai.google.dev/gemini-api/docs/models and update `GEMINI_MODEL` without
code changes.

## Knowledge-base administration

```bash
uv sync
uv run python -m app.cli migrate
uv run python -m app.cli sync --prune                 # index ../knowledge incrementally; drop deleted files
uv run python -m app.cli add ~/Documents/cv.pdf --category profile --label "Professional CV"
uv run python -m app.cli github mmm-megahed/MR.Multi.RAG-Moodle
uv run python -m app.cli list
uv run python -m app.cli search "speaker diarization" --k 5
uv run python -m app.cli remove upload:cv.pdf
uv run python -m app.cli reindex                      # force re-embedding (e.g. after switching embedding model)
```

`sync` is idempotent: unchanged documents (same text, metadata, chunking, and embedding model) are skipped, so
running it in CI or a cron is cheap. In Docker: `docker compose run --rm api python -m app.cli <command>`.

## Security

- Gemini key and DB credentials only in backend env; the browser never talks to the DB or Gemini.
- CORS allow-list, request-body size limit, Pydantic validation, message length cap, control/bidi-character
  stripping.
- Sliding-window rate limits per pseudonymous client key (salted hash of the IP — raw IPs are not stored) plus a
  global daily request budget as a cost ceiling; `max_output_tokens` and history-size caps bound token usage.
- Request and Gemini timeouts; retries only before the first streamed token; provider errors mapped to safe messages.
- Prompt-injection hardening: retrieved text and visitor input are wrapped in delimited blocks, our delimiter tags
  are neutralized inside them, and the system instructions treat both as data and forbid revealing instructions.
- Privacy: no accounts, no persistence of conversations (in-memory, TTL), logs contain sizes/ids, never message text.
- `/docs` and OpenAPI are disabled in production.

## Tests and evaluation

```bash
uv run pytest -q                                   # unit + API tests (fake model clients, in-memory store)
docker compose up -d db
TEST_DATABASE_URL=postgresql://portfolio:portfolio@localhost:5432/portfolio uv run pytest -q   # + pgvector integration
uv run ruff check app tests
```

Covered: ingestion (Markdown/PDF/GitHub loaders, incremental updates, dedupe, prune), chunking, embedding client
(prefixes, batching, normalization, error cases), retrieval relevance and filtering, multi-turn query building,
grounding (empty-context path), source attribution (only cited, unknown labels dropped), sessions, rate limiting,
validation limits, CORS, Gemini failure handling (retry/no-retry/timeout/quota), prompt-injection containment.

Evaluation on [`eval/dataset.jsonl`](eval/dataset.jsonl) (27 recruiter/technical questions in EN/DE/AR, plus
unanswerable and prompt-injection cases), against the real index and Gemini:

```bash
uv run python -m app.evaluation --retrieval-only        # hit@k, recall@k, MRR
uv run python -m app.evaluation --out eval/report.json  # + keyword accuracy, LLM-judged faithfulness, abstention
```

Use it to tune `RETRIEVAL_MIN_SCORE`, `RETRIEVAL_TOP_K`, and chunking after changing the knowledge base or models.
