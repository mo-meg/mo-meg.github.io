---
title: RAG and LLM Engineering Approach
source_label: Technical Architecture Documentation
category: rag-llm
---

# How Mohamed approaches RAG and LLM systems

This document summarizes the architecture principles visible in Mohamed's projects (Multimodal RAG for Moodle and LLM analysis at Prolumios).

## RAG architecture

Documents → processing (extraction, cleaning) → chunking → embeddings → vector database → retrieval → LLM → grounded answer.

- Ingestion and querying are separated: ingestion is offline and idempotent; the query path only reads from the index.
- Every chunk keeps provenance metadata (document, title, source) from ingestion to the final answer, so answers can carry source attribution.
- Vectors are stored in PostgreSQL with pgvector, next to metadata and full-text indexes, which allows metadata filtering and hybrid search in one system.
- Chunk size, overlap, and top-k are tuned through evaluation (for example with RAGAS in the Moodle project) rather than guesswork.
- The LLM receives retrieved evidence and is instructed to say when the evidence is insufficient instead of guessing.

## Multimodal RAG

PDF / images / tables / videos → modality-specific processing (text extraction, image extraction with page context, Whisper transcription) → unified retrieval over one vector index → LLM → answer with sources.

- Normalize all modalities into a shared, searchable representation without losing the pointer to the original file.
- Move slow media processing off the request path with asynchronous workers (Celery + Redis).
- Local inference (Ollama) when data should stay on own infrastructure.

## AI meeting intelligence

Audio → ASR → speaker diarization → transcript → LLM analysis → business insights → CRM integration.

- Clear contracts between stages (audio → transcript → analysis), each producing an inspectable artefact.
- Deliver results inside existing business tools (CRM) rather than in a separate application.

## Choosing the right amount of AI

Not every problem needs a live LLM. For his portfolio assistant, Mohamed deliberately chose offline-generated, human-reviewed answers instead of a live RAG chatbot: for a small, well-known knowledge base this removes hallucination risk, hosting, API cost, and abuse surface, while Gemini still does the heavy lifting offline.

## LLM providers

Mohamed has worked with locally hosted open models through Ollama (e.g. Gemma, Phi-3), with provider abstractions supporting OpenAI and Cohere in the Moodle project, and with the Google Gemini API for offline content generation in his portfolio project.
