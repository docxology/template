#!/usr/bin/env python3
"""Literature search orchestrator (thin wrapper around :mod:`literature.search_runner`)."""

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

from config import OUTPUT_DIR as DEFAULT_OUTPUT_DIR
from literature.search_runner import run_literature_search


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search academic databases for literature (arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv, ChinaRxiv).")
    parser.add_argument(
        "--query",
        default="active inference free energy principle",
        help="Search query string",
    )
    parser.add_argument("--max-results", type=int, default=1000)
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--skip-arxiv", action="store_true")
    parser.add_argument("--skip-s2", action="store_true")
    parser.add_argument("--skip-openalex", action="store_true")
    parser.add_argument("--skip-crossref", action="store_true")
    parser.add_argument("--skip-pubmed", action="store_true")
    parser.add_argument("--skip-sovietrxiv", action="store_true")
    parser.add_argument("--skip-chinarxiv", action="store_true")
    resume_grp = parser.add_mutually_exclusive_group()
    resume_grp.add_argument("--resume", dest="resume", action="store_true")
    resume_grp.add_argument("--no-resume", dest="resume", action="store_false")
    parser.set_defaults(resume=True)
    parser.add_argument("--clear-corpus", action="store_true")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--start-year", type=int, default=None)
    parser.add_argument("--config", type=str, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run_literature_search(args, project_root=PROJECT_ROOT)


if __name__ == "__main__":
    main()
