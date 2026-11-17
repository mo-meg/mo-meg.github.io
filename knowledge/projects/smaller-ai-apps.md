---
title: Smaller AI Apps — EN/DE Practice Coach and DecideForMe
source_label: Smaller AI Projects — Project Documentation
category: projects
url: https://github.com/mo-meg
---

# Local EN/DE Practice Coach

A personal project: a local app for English and German conversation practice at B1/B2 level, with practice focus and role-play scenarios, gentle grammar and phrasing corrections, and follow-up questions. Built with Streamlit; the coach runs on a local LLM via Ollama (llama3.2), spoken replies use a local OpenAI-compatible text-to-speech API, and optional voice input uses NVIDIA NeMo Parakeet speech recognition. Repository: https://github.com/mo-meg/local_en-de_coach

# DecideForMe

A personal project: an LLM decision assistant that compares two options against the user's stored life priorities and returns a structured answer — verdict, justification, and a concrete first step. Built with React, TypeScript, Vite, and Tailwind CSS; priorities are stored in Firestore with Firebase Authentication. Inference runs either through Firebase AI Logic in the cloud or a local Ollama model. Repository: https://github.com/mo-meg/DecideForMe
