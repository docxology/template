#!/usr/bin/env python3
"""Knowledge graph construction orchestrator (thin wrapper)."""

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
    DEFAULT_CHECKPOINT_INTERVAL,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_URL,
    OUTPUT_DIR as DEFAULT_OUTPUT_DIR,
)
from knowledge_graph.kg_runner import run_knowledge_graph_pipeline


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description="Build knowledge graph and score hypotheses.")
    parser.add_argument("--corpus", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--llm-model", type=str, default=DEFAULT_LLM_MODEL)
    parser.add_argument("--llm-url", type=str, default=DEFAULT_LLM_URL)
    parser.add_argument("--checkpoint-interval", type=int, default=DEFAULT_CHECKPOINT_INTERVAL)
    parser.add_argument("--clear-assertions", action="store_true")
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
    run_knowledge_graph_pipeline(args, project_root=PROJECT_ROOT)


if __name__ == "__main__":
    main()
