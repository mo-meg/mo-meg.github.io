"""Application settings, loaded from environment variables (and an optional .env file)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

KNOWN_CATEGORIES = (
    "profile",
    "skills",
    "rag-llm",
    "ml-nlp",
    "cloud-devops",
    "experience",
    "education",
    "projects",
    "contact",
    "documents",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Environment ---------------------------------------------------------------
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"

    # --- AI provider -----------------------------------------------------------------
    # "gemini" for real use. "fake" uses deterministic local stand-ins (tests / offline UI work).
    ai_provider: Literal["gemini", "fake"] = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_temperature: float = Field(0.3, ge=0.0, le=2.0)
    gemini_max_output_tokens: int = Field(1024, ge=64, le=8192)
    gemini_thinking_level: Literal["", "MINIMAL", "LOW", "MEDIUM", "HIGH"] = ""
    gemini_timeout_seconds: float = Field(30.0, gt=0)
    embedding_dim: int = Field(768, ge=128, le=3072)
    embedding_batch_size: int = Field(32, ge=1, le=100)

    # --- Database --------------------------------------------------------------------
    database_url: str = "postgresql://portfolio:portfolio@localhost:5432/portfolio"
    db_pool_min: int = 1
    db_pool_max: int = 5
    auto_migrate: bool = True

    # --- Ingestion -------------------------------------------------------------------
    chunk_size: int = Field(1200, ge=200, le=8000)
    chunk_overlap: int = Field(200, ge=0)
    knowledge_dir: str = "../knowledge"
    github_token: str = ""

    # --- Retrieval -------------------------------------------------------------------
    retrieval_top_k: int = Field(6, ge=1, le=20)
    retrieval_candidates: int = Field(20, ge=1, le=100)
    retrieval_min_score: float = Field(0.40, ge=-1.0, le=1.0)

    # --- Conversation ----------------------------------------------------------------
    history_turns: int = Field(6, ge=0, le=20)  # user+assistant pairs kept per session
    session_ttl_minutes: int = Field(30, ge=1)
    max_sessions: int = Field(5000, ge=10)
    max_message_chars: int = Field(1000, ge=10, le=10000)
    max_history_chars: int = Field(8000, ge=500)

    # --- Abuse protection ------------------------------------------------------------
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    max_request_bytes: int = 16_384
    rate_limit_per_minute: int = 8
    rate_limit_per_day: int = 80
    daily_request_budget: int = 1500  # global cap on chat requests per UTC day (cost guard)
    trust_proxy_headers: bool = False  # only enable behind a proxy that sets X-Forwarded-For
    request_timeout_seconds: float = 60.0

    # --- Observability ---------------------------------------------------------------
    metrics_enabled: bool = True
    metrics_token: str = ""  # if set, /metrics requires "Authorization: Bearer <token>"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [o.strip().rstrip("/") for o in v.split(",") if o.strip()]
        return v

    @model_validator(mode="after")
    def _check(self) -> Settings:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.ai_provider == "gemini" and not self.gemini_api_key and self.environment != "test":
            raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")
        if self.environment == "production":
            if self.ai_provider == "fake":
                raise ValueError("AI_PROVIDER=fake is not allowed in production")
            if any(o == "*" for o in self.allowed_origins):
                raise ValueError("ALLOWED_ORIGINS must list explicit origins in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
