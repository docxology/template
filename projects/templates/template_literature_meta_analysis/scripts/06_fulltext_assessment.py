#!/usr/bin/env python3
"""Full-text availability assessment (thin wrapper)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

bootstrap_project()

from config import CORPUS_PATH as DEFAULT_CORPUS_PATH, DATA_DIR as DEFAULT_DATA_DIR
from literature.corpus import Corpus
from literature.fulltext_assessment import assess_corpus


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description="Assess full-text availability across the literature corpus.")
    parser.add_argument("--corpus", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_DATA_DIR))
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
    logger = logging.getLogger("fulltext_assessment")

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        logger.error("Corpus file not found: %s", corpus_path)
        sys.exit(1)

    corpus = Corpus.load(corpus_path)
    results = assess_corpus(corpus)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "fulltext_assessment.json"
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)
    print(f"\nTotal papers: {results['total_papers']}")
    print(str(output_path))


if __name__ == "__main__":
    main()
