---
title: Portfolio Assistant — Offline-Generated, Human-Reviewed Q&A
source_label: Portfolio Assistant — Technical Documentation
category: projects
---

# Overview

The assistant on Mohamed's portfolio website is a personal project. It answers visitor questions with curated, prepared answers in English, German, and Arabic — not with a live chatbot. The website is fully static and hosted on GitHub Pages.

Type: personal project.

# Why no live RAG chatbot

Mohamed first built a live RAG chatbot (FastAPI, Gemini, PostgreSQL/pgvector) and then deliberately replaced it. For a small, well-known knowledge base a live model adds hallucination risk, hosting, API cost, abuse surface, and privacy questions without adding much value. Prepared answers that a human reviewed are faster, cheaper, and always accurate.

# How it works

- Offline generation: a Python tool sends the version-controlled Markdown knowledge base to the Google Gemini API with structured output. It drafts English questions and answers with sources, translates them into German and Arabic, writes native paraphrases in each language, and creates test questions for the matcher.
- Human review: every item has a status (draft, approved, needs-review). Only approved items are published. When a knowledge file changes, items based on it are regenerated if untouched, or flagged for review if Mohamed edited or approved them — human edits are never overwritten.
- In the browser: visitors click suggested questions or type their own. A lightweight multilingual matcher (language detection, normalization, light stemming, fuzzy token matching, IDF-weighted coverage) finds the closest prepared question. If nothing is close enough, the assistant invites the visitor to email Mohamed, with the question pre-filled.
- Quality gates: Python and Vitest tests, a validation step that blocks the build on missing translations, broken links, or empty answers, and a threshold test set of matching and off-topic questions.

# Technologies

Python, Google Gemini API (structured output), Pydantic, React, TypeScript, Vite, Tailwind CSS, Vitest, GitHub Actions, GitHub Pages.
