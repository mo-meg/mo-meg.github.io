---
title: Portfolio AI Assistant — RAG Chatbot with Google Gemini
source_label: Portfolio AI Assistant — Technical Documentation
category: projects
---

# Overview

The AI assistant on Mohamed's portfolio website is a personal project he built. It is a Retrieval-Augmented Generation (RAG) chatbot that answers visitor questions about his background using a version-controlled knowledge base, and shows the sources it used.

Type: personal project.

# Architecture

Ingestion pipeline (offline, separate from chat): documents (Markdown, PDF, GitHub READMEs) → text extraction → cleaning → heading-aware chunking with configurable size and overlap → metadata enrichment (title, category, heading path, source label, URL) → Gemini embeddings → PostgreSQL with pgvector.

Query pipeline: visitor question → query processing (including the previous question for follow-ups) → query embedding → hybrid retrieval (pgvector cosine similarity + PostgreSQL full-text search, merged with reciprocal rank fusion) → relevance threshold and metadata filtering → numbered context → Google Gemini → streamed, grounded answer with source citations.

# Engineering details

- Backend: Python, FastAPI, official Google Gen AI SDK, psycopg with pgvector.
- Streaming answers over Server-Sent Events.
- Incremental, deduplicated ingestion using content hashes; an ingestion CLI supports adding, updating, removing, and re-indexing documents.
- Only sources the model actually cited are shown to the visitor.
- Retrieved documents and visitor messages are treated as untrusted data (prompt-injection resistance).
- Rate limiting per client, request-size limits, CORS restrictions, timeouts, and a daily request budget protect the public endpoint.
- Conversations are kept in memory for a limited time; visitors do not register and no personal data is stored.
- Tests use fake model clients; an evaluation dataset measures retrieval hit rate, MRR, and answer faithfulness.
- Frontend: React, TypeScript, Vite, Tailwind CSS, deployed on GitHub Pages. The backend is deployed separately.
- Supports answers in English, German, and Arabic.
