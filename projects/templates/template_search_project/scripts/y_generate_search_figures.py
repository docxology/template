#!/usr/bin/env python3
"""Generate figures from a completed search run.

Reads ``output/search/results.json`` (produced by
``run_search_pipeline.py``), generates three PNG figures via the
``src.figures`` module, and prints each output path on stdout for the
infrastructure manifest collector.

This script is a **thin orchestrator**: every plotting decision lives in
``src/figures.py``.

Exit codes:
    0   figures written successfully
    2   no search results available — graceful skip (allow_skip stage trick)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
_repo_root = _project_root.parents[2]
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))
sys.path.insert(0, str(_repo_root))

from infrastructure.core.logging.utils import get_logger

from src.figures import generate_all_figures, load_search_result

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--project-root",
        default=str(_project_root),
        help="Project root for relative output paths (defaults to this script's project).",
    )
    parser.add_argument(
        "--results",
        default=None,
        help=(
            "Override the path to output/search/results.json. Defaults to <project-root>/output/search/results.json."
        ),
    )
    parser.add_argument(
        "--figures-dir",
        default=None,
        help=("Override the directory where the PNG figures are written. Defaults to <project-root>/output/figures."),
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    results_path = Path(args.results).resolve() if args.results else project_root / "output" / "search" / "results.json"
    figures_dir = Path(args.figures_dir).resolve() if args.figures_dir else project_root / "output" / "figures"

    if not results_path.exists():
        logger.warning(
            "No search results at %s; run run_search_pipeline.py first. Skipping.",
            results_path,
        )
        return 2

    try:
        result = load_search_result(results_path)
    except (OSError, ValueError) as exc:
        logger.error("Could not load %s: %s", results_path, exc)
        return 1

    paths = generate_all_figures(result, figures_dir)
    for path in paths:
        print(str(path))
    logger.info("Wrote %d figure(s) to %s", len(paths), figures_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
