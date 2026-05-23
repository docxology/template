#!/usr/bin/env python3
"""Thin orchestrator: run all documentation linters via infrastructure.validation.docs.lint_runner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.validation.docs.lint_runner import (  # noqa: E402
    format_docs_lint_report,
    run_docs_lint,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run mermaid + cross-link + consistency linters across the repo.",
    )
    parser.add_argument("--mermaid-only", action="store_true")
    parser.add_argument("--links-only", action="store_true")
    parser.add_argument("--consistency-only", action="store_true")
    parser.add_argument("--doc-pairs-only", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict-mermaid", action="store_true")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    try:
        report = run_docs_lint(
            repo_root,
            mermaid_only=args.mermaid_only,
            links_only=args.links_only,
            consistency_only=args.consistency_only,
            doc_pairs_only=args.doc_pairs_only,
            quiet=args.quiet,
            strict_mermaid=args.strict_mermaid,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    formatted = format_docs_lint_report(
        report,
        repo_root,
        as_json=args.json,
        quiet=args.quiet,
    )
    if formatted is not None:
        sys.stdout.write(formatted)
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
