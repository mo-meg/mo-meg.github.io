---
title: Multimodal Retrieval-Augmented Generation with Source Attribution (MR. Multi@Moodle)
source_label: Multimodal RAG Moodle — Project Documentation
category: projects
url: https://github.com/mmm-megahed/MR.Multi.RAG-Moodle
---

# Overview

MR. Multi@Moodle is an end-to-end multimodal Retrieval-Augmented Generation (RAG) system integrated into the Moodle learning platform. It answers questions about course materials — PDFs, images and tables inside PDFs, and lecture video content — and provides source attribution back to the original course files.

Type: academic research project (FernUniversität in Hagen context), built by Mohamed. Repository: https://github.com/mmm-megahed/MR.Multi.RAG-Moodle

# Problem

Course knowledge is spread across modalities: text in PDFs, figures and tables embedded in those PDFs, and spoken explanations in lecture videos. Plain keyword search misses much of it, and an LLM answering without evidence is not acceptable in education — learners need to see where an answer comes from. The key challenge is retrieving relevant information across different educational modalities while keeping source attribution.

# Architecture and components

- Moodle block plugin (PHP and JavaScript) providing search and chat inside a Moodle course and triggering processing of course resources (text, images, videos).
- FastAPI backend (Python) for uploading and processing files, chunking, embedding, indexing into a vector database, semantic search, and answer generation.
- Pluggable provider architecture with factory interfaces: LLM providers (Ollama, OpenAI, Cohere) and vector database providers (pgvector, Qdrant).
- Local LLM inference with Ollama (models pulled in the setup include gemma3:1b and phi3 mini) and local embedding models via Ollama (nomic-embed-text, mxbai-embed-large).
- Video processing: lecture audio is transcribed with OpenAI Whisper; transcripts are indexed so video content becomes searchable.
- Image processing: images are extracted from PDFs together with their surrounding page context, producing searchable descriptions.
- Asynchronous processing: Celery workers with Redis as broker run video and image processing jobs, so the API returns immediately with a job id.
- PostgreSQL with pgvector as vector database; SQLAlchemy models and Alembic migrations.
- Prompt templates in English and Arabic.
- Nginx reverse proxy.
- Monitoring with Prometheus and Grafana (including node-exporter and postgres-exporter).
- Everything runs with Docker and Docker Compose (Moodle, FastAPI, workers, Redis, PostgreSQL, Ollama, Nginx, Prometheus, Grafana).

# Workflow

Moodle course resources (PDF, images, tables, video) → Celery workers (Whisper transcription, PDF image extraction) → chunking and embeddings → PostgreSQL + pgvector (unified index) → semantic retrieval → local LLM via Ollama → answer with sources shown in Moodle.

# Evaluation

The repository contains evaluation experiments using RAGAS:

- Experiment 1: a 40-question evaluation comparing chunk size / overlap settings (500/100 and 1200/200 characters) and retrieval depth (top-k 3 and 5).
- Experiment 2: a 30-question evaluation focused on multimodality (questions by modality).
- Experiment 3: comparisons with updated knowledge, including answers of a Gemma LLM without the knowledge base.

The knowledge base does not contain the numeric evaluation scores; see the repository for the reports.

# Key engineering challenges

- Bringing heterogeneous modalities into one retrievable representation without losing the link to the original file.
- Keeping slow, compute-heavy work (transcription, PDF image extraction) out of the request path with a task queue.
- Running inference locally with small open models to keep course data on own infrastructure (privacy-conscious design).
- Operating a multi-service stack reproducibly with Docker Compose and monitoring it.
- Choosing chunking and retrieval parameters through systematic evaluation.

# Mohamed's contribution

Mohamed designed and implemented the system: the Moodle plugin, FastAPI services, ingestion and media-processing workers, vector storage, prompt templates, containerized deployment with monitoring, and the evaluation experiments.
