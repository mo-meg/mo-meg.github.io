"""Connection pool and a minimal, dependency-free SQL migration runner."""

from __future__ import annotations

import logging
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector_async
from psycopg_pool import AsyncConnectionPool

from app.logging_setup import log

logger = logging.getLogger(__name__)
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


async def _configure(conn: psycopg.AsyncConnection) -> None:
    await register_vector_async(conn)


async def create_pool(dsn: str, min_size: int = 1, max_size: int = 5) -> AsyncConnectionPool:
    pool = AsyncConnectionPool(
        dsn,
        min_size=min_size,
        max_size=max_size,
        configure=_configure,
        open=False,
        kwargs={"autocommit": True},
        timeout=10,
    )
    await pool.open(wait=True, timeout=30)
    return pool


async def migrate(dsn: str, embedding_dim: int) -> list[str]:
    """Apply pending migrations in filename order. Each migration runs in its own transaction."""
    applied: list[str] = []
    async with await psycopg.AsyncConnection.connect(dsn, autocommit=True) as conn:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                   version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"""
        )
        cur = await conn.execute("SELECT version FROM schema_migrations")
        done = {r[0] for r in await cur.fetchall()}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.stem in done:
                continue
            sql = path.read_text(encoding="utf-8").replace("{embedding_dim}", str(int(embedding_dim)))
            async with conn.transaction():
                await conn.execute(sql)  # type: ignore[arg-type]
                await conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
            applied.append(path.stem)
            log(logger, logging.INFO, "migration_applied", version=path.stem)

        # Guard against a silent mismatch between EMBEDDING_DIM and the existing column.
        cur = await conn.execute(
            """SELECT atttypmod FROM pg_attribute
               WHERE attrelid = 'chunks'::regclass AND attname = 'embedding'"""
        )
        row = await cur.fetchone()
        if row and row[0] != embedding_dim:
            raise RuntimeError(
                f"chunks.embedding has dimension {row[0]} but EMBEDDING_DIM={embedding_dim}. "
                "Re-create the database (or add a migration) and re-index."
            )
    return applied
