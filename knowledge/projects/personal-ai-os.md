---
title: Personal AI OS — Local Multi-Agent Assistant on Telegram
source_label: Personal AI OS — Project Documentation
category: projects
url: https://github.com/mo-meg/AI-Agent-System-Local
---

# Overview

Personal AI OS is a fully local, multi-agent assistant for daily life that Mohamed built as a personal project. It runs on his own machine with Ollama models and is controlled through Telegram. Repository: https://github.com/mo-meg/AI-Agent-System-Local

Type: personal project.

# Architecture

- Orchestrator / intent router: each message is classified into an intent — summarize, plan, capture, remind, list tasks, list notes, done, or chat. Regex fast-paths handle obvious cases (URLs, "remind me", "done 3"); otherwise a local LLM via Ollama classifies the message, and unknown outputs fall back to chat.
- Specialized agents: summarizer (URLs and text, with web page text extraction), capture agent (notes and tasks), planner agent (task-aware daily plan), reminder agent (natural-language reminders), chat agent (conversation with recent-turn memory), and a vision agent.
- Reminders: the LLM extracts the time in a constrained format (relative like +30m, "today 09:00", or ISO 8601), and code parses it deterministically into an exact time.
- Persistent memory: SQLite via SQLAlchemy stores tasks, notes, reminders, and per-user conversation context across restarts.
- Multimodal input: Telegram voice notes are transcribed locally with OpenAI Whisper and routed like text; photos are described with the LLaVA vision model via Ollama.
- Scheduling: APScheduler pushes a personalized morning plan at a configured time and checks for due reminders.
- Access control: an optional allow-list of Telegram user IDs.
- Telegram interface with commands such as /tasks, /notes, /plan, /clear, /help.

# Technologies

Python, Ollama (e.g. llama3, LLaVA), OpenAI Whisper, python-telegram-bot, SQLAlchemy, SQLite, APScheduler, BeautifulSoup, loguru.
