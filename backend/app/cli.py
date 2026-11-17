"""Knowledge-base administration CLI.

python -m app.cli migrate
python -m app.cli sync [DIR] [--prune] [--force]      # Markdown + PDF under the knowledge dir
python -m app.cli add FILE [FILE...] [--category C] [--title T] [--label L] [--url U] [--force]
python -m app.cli github OWNER/REPO [--category projects] [--title T] [--label L]
python -m app.cli remove SOURCE_ID
python -m app.cli reindex                              # re-embed everything (e.g. after a model change)
python -m app.cli list
python -m app.cli search "question" [--k 6] [--category C]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from app.config import KNOWN_CATEGORIES, Settings, get_settings
from app.db import create_pool, migrate
from app.ingestion.loaders import LoaderError, discover, load_file, load_github_readme
from app.ingestion.pipeline import Ingestor, IngestReport
from app.logging_setup import setup_logging
from app.retrieval import Retriever
from app.services import build_ai
from app.vectorstore import PgVectorStore


def _print_report(r: IngestReport) -> None:
    for sid, outcome in sorted(r.results.items()):
        print(f"  {outcome:<10} {sid}")
    for sid in r.removed:
        print(f"  {'removed':<10} {sid}")
    for sid, err in r.errors.items():
        print(f"  {'ERROR':<10} {sid}: {err}", file=sys.stderr)
    print("summary:", r.summary())


async def _run(args: argparse.Namespace, settings: Settings) -> int:
    if args.cmd == "migrate":
        applied = await migrate(settings.database_url, settings.embedding_dim)
        print("applied:", applied or "nothing (up to date)")
        return 0

    await migrate(settings.database_url, settings.embedding_dim)
    pool = await create_pool(settings.database_url)
    try:
        store = PgVectorStore(pool)
        embedder, _ = build_ai(settings)
        ingestor = Ingestor(store, embedder, settings.chunk_size, settings.chunk_overlap)
        root = Path(getattr(args, "dir", None) or settings.knowledge_dir).resolve()

        if args.cmd in ("sync", "reindex"):
            if not root.is_dir():
                print(f"knowledge directory not found: {root}", file=sys.stderr)
                return 2
            force = args.cmd == "reindex" or args.force
            docs, report = [], IngestReport()
            for p in discover(root):
                try:
                    docs.append(load_file(p, root))
                except LoaderError as e:
                    report.errors[str(p)] = str(e)
            r = await ingestor.ingest_many(docs, force=force)
            report.results, report.errors = r.results, {**report.errors, **r.errors}
            if args.cmd == "reindex":
                for rec in await store.list_documents():
                    if rec.source_id.startswith("github:"):
                        repo = rec.metadata.get("repo") or rec.source_id.split(":", 1)[1]
                        try:
                            d = await load_github_readme(
                                repo,
                                category=rec.category,
                                title=rec.title,
                                source_label=rec.source_label,
                                token=settings.github_token,
                            )
                            report.results[d.source_id] = await ingestor.ingest(d, force=True)
                        except Exception as e:  # noqa: BLE001
                            report.errors[rec.source_id] = str(e)
            if getattr(args, "prune", False):
                report.removed = await ingestor.prune({d.source_id for d in docs}, prefix="file:")
            _print_report(report)
            return 1 if report.errors else 0

        if args.cmd == "add":
            overrides = {
                k: v
                for k, v in {
                    "category": args.category,
                    "title": args.title,
                    "source_label": args.label,
                    "url": args.url,
                }.items()
                if v
            }
            docs = []
            for f in args.files:
                p = Path(f)
                docs.append(load_file(p, root if p.resolve().is_relative_to(root) else None, **overrides))
            _print_report(await ingestor.ingest_many(docs, force=args.force))
            return 0

        if args.cmd == "github":
            d = await load_github_readme(
                args.repo,
                category=args.category,
                title=args.title,
                source_label=args.label,
                token=settings.github_token,
            )
            print(f"  {await ingestor.ingest(d, force=args.force):<10} {d.source_id}")
            return 0

        if args.cmd == "remove":
            ok = await store.delete_document(args.source_id)
            print("removed" if ok else "not found", args.source_id)
            return 0 if ok else 1

        if args.cmd == "list":
            docs = await store.list_documents()
            for d in docs:
                print(f"{d.category:<13} {d.chunk_count:>3} chunks  {d.source_id:<55} {d.source_label}")
            print(f"{len(docs)} documents")
            return 0

        if args.cmd == "search":
            retriever = Retriever(
                store,
                embedder,
                top_k=args.k,
                candidates=settings.retrieval_candidates,
                min_score=settings.retrieval_min_score,
            )
            cats = [args.category] if args.category else None
            for c in await retriever.retrieve(args.query, categories=cats):
                print(f"{c.similarity:.3f}  rrf={c.score:.4f}  {c.source_label} › {c.heading}")
                print("       " + " ".join(c.text.split())[:160])
            return 0
    finally:
        await pool.close()
    return 2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.cli", description="Manage the portfolio knowledge base")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="apply database migrations")

    s = sub.add_parser("sync", help="ingest new/changed Markdown & PDF files (incremental)")
    s.add_argument("dir", nargs="?")
    s.add_argument("--prune", action="store_true", help="remove indexed files that no longer exist")
    s.add_argument("--force", action="store_true", help="re-embed even if unchanged")

    r = sub.add_parser("reindex", help="re-embed all documents (files + GitHub READMEs)")
    r.add_argument("dir", nargs="?")

    a = sub.add_parser("add", help="add or update specific files")
    a.add_argument("files", nargs="+")
    a.add_argument("--category", choices=KNOWN_CATEGORIES)
    a.add_argument("--title")
    a.add_argument("--label", help="citation label shown to visitors")
    a.add_argument("--url")
    a.add_argument("--force", action="store_true")

    g = sub.add_parser("github", help="ingest a GitHub repository README")
    g.add_argument("repo", help="owner/name")
    g.add_argument("--category", default="projects", choices=KNOWN_CATEGORIES)
    g.add_argument("--title")
    g.add_argument("--label")
    g.add_argument("--force", action="store_true")

    rm = sub.add_parser("remove", help="remove a document by source id")
    rm.add_argument("source_id")

    sub.add_parser("list", help="list indexed documents")

    q = sub.add_parser("search", help="debug retrieval for a query")
    q.add_argument("query")
    q.add_argument("--k", type=int, default=6)
    q.add_argument("--category", choices=KNOWN_CATEGORIES)

    args = p.parse_args(argv)
    settings = get_settings()
    setup_logging("WARNING")
    try:
        return asyncio.run(_run(args, settings))
    except LoaderError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
