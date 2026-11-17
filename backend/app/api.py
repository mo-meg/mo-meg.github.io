"""FastAPI application: streaming chat endpoint, health checks, metrics."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field, field_validator

from app import metrics
from app.config import KNOWN_CATEGORIES, Settings, get_settings
from app.logging_setup import log, setup_logging
from app.security import client_key, sanitize_message
from app.services import Services, build_ai, build_services

logger = logging.getLogger(__name__)
SESSION_ID_PATTERN = r"^[A-Za-z0-9_-]{8,64}$"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
    session_id: str | None = Field(default=None, pattern=SESSION_ID_PATTERN)
    categories: list[str] | None = Field(default=None, max_length=len(KNOWN_CATEGORIES))

    @field_validator("categories")
    @classmethod
    def _known(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        bad = [c for c in v if c not in KNOWN_CATEGORIES]
        if bad:
            raise ValueError(f"unknown categories: {bad}")
        return v or None


class ResetRequest(BaseModel):
    session_id: str = Field(pattern=SESSION_ID_PATTERN)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def create_app(settings: Settings | None = None, services: Services | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if services is not None:
            app.state.services = services
            yield
            return
        from app.db import create_pool, migrate
        from app.vectorstore import PgVectorStore

        if settings.auto_migrate:
            await migrate(settings.database_url, settings.embedding_dim)
        pool = await create_pool(settings.database_url, settings.db_pool_min, settings.db_pool_max)
        embedder, generator = build_ai(settings)
        app.state.services = build_services(settings, PgVectorStore(pool), embedder, generator, pool)
        log(
            logger,
            logging.INFO,
            "startup",
            provider=settings.ai_provider,
            model=generator.model_name,
            embedding_model=embedder.model_name,
            origins=settings.allowed_origins,
        )
        try:
            yield
        finally:
            await pool.close()

    app = FastAPI(
        title="Portfolio AI Assistant",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
        allow_credentials=False,
        max_age=600,
    )

    @app.middleware("http")
    async def limits(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Request size limit (cheap header check; the body model also caps lengths).
        cl = request.headers.get("content-length")
        if request.method == "POST":
            if cl is None and request.headers.get("transfer-encoding"):
                return JSONResponse({"detail": "Chunked request bodies are not accepted."}, status_code=411)
            if cl is not None and (not cl.isdigit() or int(cl) > settings.max_request_bytes):
                return JSONResponse({"detail": "Request too large."}, status_code=413)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    def svc(request: Request) -> Services:
        return request.app.state.services

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready(request: Request) -> JSONResponse:
        try:
            stats = await asyncio.wait_for(svc(request).store.stats(), timeout=3)
        except Exception:  # noqa: BLE001
            return JSONResponse({"status": "unavailable"}, status_code=503)
        status = "ok" if stats["chunks"] > 0 else "empty_knowledge_base"
        return JSONResponse({"status": status, **stats}, status_code=200 if stats["chunks"] > 0 else 503)

    @app.post("/api/chat")
    async def chat(body: ChatRequest, request: Request) -> StreamingResponse:
        s = svc(request)
        allowed, scope, retry_after = s.limiter.check(client_key(request, settings.trust_proxy_headers))
        if not allowed:
            metrics.RATE_LIMITED.labels(scope or "unknown").inc()
            msg = (
                "The assistant has reached its daily usage limit. Please use the contact section instead."
                if scope == "global"
                else "Too many requests — please wait a moment and try again."
            )
            raise HTTPException(status_code=429, detail=msg, headers={"Retry-After": str(retry_after)})

        if len(body.message) > settings.max_message_chars:
            raise HTTPException(
                status_code=413, detail=f"Please keep questions under {settings.max_message_chars} characters."
            )
        message = sanitize_message(body.message, settings.max_message_chars)
        if not message:
            raise HTTPException(status_code=422, detail="Message is empty.")

        async def events() -> AsyncIterator[str]:
            try:
                async with asyncio.timeout(settings.request_timeout_seconds):
                    async for evt in s.chat.chat(message, body.session_id, body.categories):
                        if await request.is_disconnected():
                            return
                        yield _sse(evt.type, evt.data)
            except TimeoutError:
                yield _sse("error", {"message": "The request timed out. Please try again.", "retryable": True})
            except Exception as e:  # noqa: BLE001 — never leak internals to the client
                log(logger, logging.ERROR, "chat_unhandled", error=type(e).__name__)
                yield _sse("error", {"message": "Unexpected server error. Please try again.", "retryable": True})

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/api/chat/reset")
    async def reset(body: ResetRequest, request: Request) -> dict:
        svc(request).sessions.reset(body.session_id)
        return {"status": "ok"}

    if settings.metrics_enabled:

        @app.get("/metrics", include_in_schema=False)
        async def prom(request: Request) -> Response:
            if settings.metrics_token and request.headers.get("authorization") != f"Bearer {settings.metrics_token}":
                return Response(status_code=401)
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


def app_factory() -> FastAPI:
    return create_app()
