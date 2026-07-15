#!/usr/bin/env python3
"""Literature evaluation harness (thin wrapper around :mod:`literature.evaluation`)."""

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

PROJECT_ROOT = bootstrap_project()

from config import CORPUS_PATH as DEFAULT_CORPUS_PATH
from config import DATA_DIR as DEFAULT_DATA_DIR
from literature.corpus import Corpus
from literature.evaluation import evaluate_corpus
from literature.fixture_honesty import validate_fixture_honesty


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description="Evaluate literature corpus quality and routing coverage.")
    parser.add_argument("--corpus", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_DATA_DIR))
    parser.add_argument(
        "--fixture-honesty",
        action="store_true",
        help="Audit manuscript for undisclosed empirical claims on synthetic fixture corpora",
    )
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
    logger = logging.getLogger("literature_evaluation")

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        logger.error("Corpus file not found: %s", corpus_path)
        sys.exit(1)

    corpus = Corpus.load(corpus_path)
    if args.fixture_honesty:
        manuscript_dir = PROJECT_ROOT / "manuscript"
        violations = validate_fixture_honesty(manuscript_dir, corpus_path)
        if violations:
            for v in violations:
                logger.error("Fixture honesty: %s:%s %s — %s", v.path, v.line, v.reason, v.excerpt)
            sys.exit(1)
        logger.info("Fixture honesty audit passed (%s)", manuscript_dir)
    results = evaluate_corpus(corpus, query=args.query)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "literature_evaluation.json"
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)
    print(f"\nTotal papers: {results['total_papers']}")
    print(str(output_path))


if __name__ == "__main__":
    main()
