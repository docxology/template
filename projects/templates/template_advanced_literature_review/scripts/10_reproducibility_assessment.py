#!/usr/bin/env python3
"""Reproducibility-assessment orchestrator (thin wrapper)."""

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

from config import (
    CORPUS_PATH as DEFAULT_CORPUS_PATH,
)
from config import (
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_URL,
    DEFAULT_REPRO_CHECKPOINT_INTERVAL,
)
from config import (
    OUTPUT_DIR as DEFAULT_OUTPUT_DIR,
)
from reproducibility.runner import run_reproducibility_pipeline


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description="Build reproducibility workflow graphs and score them.")
    parser.add_argument("--corpus", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--fulltext-dir",
        type=str,
        default=None,
        help="Override the fulltext directory (default: config's fulltext.download_dir, "
        "falling back to <output_dir>/fulltext).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--llm-model", type=str, default=DEFAULT_LLM_MODEL)
    parser.add_argument("--llm-url", type=str, default=DEFAULT_LLM_URL)
    parser.add_argument("--checkpoint-interval", type=int, default=DEFAULT_REPRO_CHECKPOINT_INTERVAL)
    parser.add_argument("--clear-workflow-graphs", action="store_true")
    parser.add_argument("--max-papers", type=int, default=None)
    parser.add_argument("--config", type=str, default=None)
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run_reproducibility_pipeline(args, project_root=PROJECT_ROOT)


if __name__ == "__main__":
    main()
