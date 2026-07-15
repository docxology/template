#!/usr/bin/env python3
"""Meta-analysis pipeline orchestrator (thin wrapper)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

PROJECT_ROOT = bootstrap_project()

from analysis.pipeline_runner import run_meta_analysis_pipeline
from config import (
    CORPUS_PATH as DEFAULT_CORPUS_PATH,
)
from config import (
    DEFAULT_MAX_FEATURES,
    DEFAULT_MIN_YEAR,
    DEFAULT_N_TOPICS,
    DEFAULT_SEED,
)
from config import (
    OUTPUT_DIR as DEFAULT_OUTPUT_DIR,
)


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description="Run meta-analysis pipeline on Active Inference corpus.")
    parser.add_argument("--corpus", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--n-topics", type=int, default=DEFAULT_N_TOPICS)
    parser.add_argument("--max-features", type=int, default=DEFAULT_MAX_FEATURES)
    parser.add_argument("--min-year", type=int, default=DEFAULT_MIN_YEAR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run_meta_analysis_pipeline(args, project_root=PROJECT_ROOT)


if __name__ == "__main__":
    main()
