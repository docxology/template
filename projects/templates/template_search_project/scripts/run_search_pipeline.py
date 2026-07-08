#!/usr/bin/env python3
"""Thin orchestrator: search → enrich → BibTeX → LLM → reading report.

All logic lives in :mod:`template_search_project.pipeline`,
:mod:`template_search_project.synthesis`, :mod:`template_search_project.report`,
and :mod:`template_search_project.search_pipeline_cli` (under ``src/``). This
script's job is purely to wire those functions to the filesystem, the optional
local Ollama server, and the command-line argument set.

Usage:

    uv run python projects/templates/template_search_project/scripts/run_search_pipeline.py
    uv run python projects/templates/template_search_project/scripts/run_search_pipeline.py \
        --config projects/templates/template_search_project/manuscript/config.yaml \
        --no-llm

Environment:
    PAPERCLIP_API_KEY  optional; required iff config.search.sources contains 'paperclip'
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project src/ + repo root to path so we can import the package and infrastructure.
_project_root = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
_repo_root = _project_root.parents[2]
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))
sys.path.insert(0, str(_repo_root))

from src.config import load_project_config
from src.dotenv import load_dotenv
from src.search_pipeline_cli import run_search_pipeline_cli

# Load project-local .env early so PAPERCLIP_API_KEY (and any other
# secrets) are available before the pipeline module builds backends.
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
        "--no-cache",
        action="store_true",
        help="Bypass search-cache reads (cache writes still happen).",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip the LLM synthesis stage even if the config enables it.",
    )
    parser.add_argument(
        "--corpus",
        default=None,
        help="Path to a JSON corpus, required iff 'local' is in config.search.sources.",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config = load_project_config(args.config)
    return run_search_pipeline_cli(args, project_root, config)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
