"""Offline Q&A tool.

uv run python -m qa_generator.cli generate [--max-new 10] [--dry-run]
uv run python -m qa_generator.cli status
uv run python -m qa_generator.cli validate
uv run python -m qa_generator.cli approve ID [ID ...] | --all
uv run python -m qa_generator.cli github OWNER/REPO [--force]
uv run python -m qa_generator.cli stamp [--mark-generated]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from qa_generator.knowledge import load_knowledge, section_ids
from qa_generator.paths import Paths
from qa_generator.pipeline import approve, run_generate, stamp, summary
from qa_generator.store import load_eval, load_qa
from qa_generator.validate import Report, validate


def _load_dotenv() -> None:
    env = Path(__file__).resolve().parents[1] / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _print_report(r: Report) -> None:
    for e in r.errors:
        print(f"  ERROR    {e}")
    for w in r.warnings:
        print(f"  warning  {w}")
    print("valid" if r.ok else f"{len(r.errors)} error(s)")


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    p = argparse.ArgumentParser(prog="python -m qa_generator.cli", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="update drafts from knowledge/ using Gemini")
    g.add_argument("--max-new", type=int, default=10, help="maximum number of new items")
    g.add_argument("--negatives", type=int, default=30, help="target number of off-topic test questions")
    g.add_argument("--dry-run", action="store_true")
    sub.add_parser("status", help="counts by status, items needing review")
    sub.add_parser("validate", help="check the Q&A file (exit 1 on errors)")
    a = sub.add_parser("approve", help="mark items as reviewed and publishable")
    a.add_argument("ids", nargs="*")
    a.add_argument("--all", action="store_true", help="approve every draft / needs-review item")
    gh = sub.add_parser("github", help="import a GitHub README into knowledge/projects/")
    gh.add_argument("repo")
    gh.add_argument("--force", action="store_true")
    st = sub.add_parser("stamp", help="fill missing knowledge fingerprints for hand-written items")
    st.add_argument("--mark-generated", action="store_true", help="treat current text as generator output")
    args = p.parse_args(argv)
    paths = Paths.default()

    if args.cmd == "generate":
        from qa_generator.llm import GeminiWriter

        try:
            writer = GeminiWriter()
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        r = run_generate(paths, writer, max_new=args.max_new, negatives_target=args.negatives, dry_run=args.dry_run)
        print(f"created     {len(r.created)}  {r.created}")
        print(f"regenerated {len(r.regenerated)}  {r.regenerated}")
        print(f"needs-review {len(r.flagged)} {r.flagged}")
        print(f"unchanged   {r.unchanged}")
        for k, v in r.skipped.items():
            print(f"  skipped   {k}: {v}")
        print(f"eval cases  +{r.eval_added}")
        if r.validation:
            _print_report(r.validation)
        print("(dry run — nothing written)" if args.dry_run else f"written: {paths.qa_file}")
        return 0

    if args.cmd == "status":
        qa, ev = load_qa(paths.qa_file), load_eval(paths.eval_file)
        print(json.dumps(summary(qa, ev), indent=2))
        for i in qa.items:
            if i.status != "approved":
                print(f"  {i.status:<13} {i.id:<36} {i.i18n['en'].question}")
        return 0

    if args.cmd == "validate":
        qa, ev = load_qa(paths.qa_file), load_eval(paths.eval_file)
        r = validate(qa, section_ids(paths.sections_file), load_knowledge(paths.knowledge), ev)
        _print_report(r)
        return 0 if r.ok else 1

    if args.cmd == "approve":
        if not args.ids and not args.all:
            p.error("give item ids or --all")
        done = approve(paths, args.ids, all_pending=args.all)
        print(f"approved {len(done)}: {done}")
        return 0

    if args.cmd == "github":
        from qa_generator.github import import_readme

        path = import_readme(args.repo, paths.knowledge, token=os.environ.get("GITHUB_TOKEN", ""), force=args.force)
        print(f"wrote {path} — run `generate` to create questions for it")
        return 0

    if args.cmd == "stamp":
        print(f"updated {stamp(paths, mark_generated=args.mark_generated)} field(s)")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
