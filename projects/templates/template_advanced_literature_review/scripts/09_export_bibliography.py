#!/usr/bin/env python3
"""Unified bibliography export harness (thin wrapper around :mod:`literature.bibliography`)."""

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

from config import CORPUS_PATH as DEFAULT_CORPUS_PATH
from config import DATA_DIR as DEFAULT_DATA_DIR
from literature.bibliography import corpus_to_bibtex
from literature.corpus import Corpus


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description="Export the literature corpus to a unified BibTeX file.")
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
    logger = logging.getLogger("export_bibliography")

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        logger.error("Corpus file not found: %s", corpus_path)
        sys.exit(1)

    corpus = Corpus.load(corpus_path)
    bibtex_text = corpus_to_bibtex(corpus)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "bibliography.bib"
    output_path.write_text(bibtex_text, encoding="utf-8")

    print(f"\nTotal papers: {len(corpus)}")
    print(str(output_path))


if __name__ == "__main__":
    main()
