#!/usr/bin/env python3
"""Write ``docs/_generated/coverage_history.md`` from CI coverage artefacts.

Thin orchestrator — all logic lives in
:mod:`infrastructure.reporting.coverage_history`.

Two collection modes:

* ``--from-dir=PATH`` — read every ``coverage-*.xml`` under ``PATH``.
  Used by CI when the workflow has already downloaded the artefacts
  locally, and by anyone running offline.
* ``--from-gh`` — call ``gh run list`` + ``gh run download`` for the
  past ``--days`` of successful runs of the named workflow.

Run from repository root::

    uv run python scripts/docgen/coverage_history.py --from-dir=./_artefacts
    uv run python scripts/docgen/coverage_history.py --from-gh --days=30
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bootstrap: add repo root so ``infrastructure`` and ``scripts`` are importable
# when this file is run directly (``python scripts/docgen/coverage_history.py``).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.reporting.coverage_history import (  # noqa: E402
    CoveragePoint,
    build_history_markdown,
    collect_history_from_dir,
    collect_history_via_gh,
)

logger = get_logger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-dir", type=Path, help="Directory holding coverage-*.xml files.")
    src.add_argument("--from-gh", action="store_true", help="Use `gh run download` against ci.yml.")
    parser.add_argument("--workflow", default="ci.yml", help="GitHub Actions workflow filename.")
    parser.add_argument("--days", type=int, default=30, help="Rolling window in days.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output Markdown path (default: docs/_generated/coverage_history.md).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    log_header("Generate Coverage History Dashboard", logger)
    args = _parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    out_path = args.output or repo_root / "docs" / "_generated" / "coverage_history.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    points: list[CoveragePoint]
    if args.from_dir is not None:
        points = collect_history_from_dir(args.from_dir)
    else:
        points = collect_history_via_gh(workflow=args.workflow, days=args.days, repo_root=repo_root)

    markdown = build_history_markdown(points, days=args.days)
    out_path.write_text(markdown, encoding="utf-8")
    log_success(f"Wrote {out_path} ({len(points)} coverage point(s))", logger)
    return 0


if __name__ == "__main__":
    sys.exit(main())
