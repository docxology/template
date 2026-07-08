#!/usr/bin/env python3
"""Multi-keyword deep search orchestrator.

Reads ``deep_search`` block from ``manuscript/config.yaml``, runs one
search per keyword (each capped at ``max_results_per_keyword``), fully
enriches every paper, optionally generates a per-paper LLM deep
summary, and writes a per-keyword reading report plus an aggregate
report and a unified BibTeX file.

Usage:

    uv run python projects/templates/template_search_project/scripts/run_deep_search.py
    uv run python projects/templates/template_search_project/scripts/run_deep_search.py --no-llm
    uv run python projects/templates/template_search_project/scripts/run_deep_search.py --keyword "convex optimization"

All config-override resolution, the LLM callable build, the deep-search
call, artifact printing, and the run-summary write live in
``src.deep_search_cli.run_deep_search_cli`` — this script only wires up
argparse and the config load per the thin-orchestrator pattern.
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

from src.config import load_project_config
from src.deep_search_cli import run_deep_search_cli
from src.dotenv import load_dotenv

# Load project-local .env early so PAPERCLIP_API_KEY (and any other
# secrets) are available when the deep_search module instantiates
# PaperclipBackend. The shell environment always wins (override=False).
load_dotenv(_project_root / ".env")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        default=str(_project_root / "manuscript" / "config.yaml"),
        help="Path to manuscript/config.yaml",
    )
    parser.add_argument(
        "--project-root",
        default=str(_project_root),
        help="Project root for relative output paths",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip the per-paper LLM stage even when config.yaml enables it.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass SearchCache reads (writes still happen).",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=None,
        help="Override keyword list (may be passed multiple times).",
    )
    parser.add_argument(
        "--corpus",
        default=None,
        help="Override path to local corpus (when sources includes 'local').",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Force-enable deep search regardless of config.yaml setting.",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config = load_project_config(args.config)
    return run_deep_search_cli(args, project_root, config)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
