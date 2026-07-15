#!/usr/bin/env python3
"""Open-access full-text download and extraction (thin wrapper).

Bridges the gap between the corpus (Stage 01) and the reproducibility
assessment (Stage 10): resolves OA PDF URLs via Unpaywall, downloads
them, and extracts plaintext + embedded figures via pypdf. The
reproducibility runner reads the .txt files this script produces.

Network-gated and opt-in: when ``project_config.fulltext.enabled`` is
false (the default), this script is a no-op that logs a warning. Enable
it by setting ``fulltext.enabled: true`` and ``fulltext.unpaywall_email``
in ``manuscript/config.yaml``.
"""

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
from config import FULLTEXT_DIR as DEFAULT_FULLTEXT_DIR
from config_loader import load_fulltext_config
from literature.corpus import Corpus
from literature.fulltext_download import (
    assess_fulltext_extraction,
    download_and_extract_fulltext,
)


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(
        description="Download and extract open-access full text for the corpus."
    )
    parser.add_argument("--corpus", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_FULLTEXT_DIR),
        help="Directory to write .pdf, .txt, and figures/ files.",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=None,
        help="Cap the number of papers to attempt (null = no limit).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to manuscript/config.yaml for fulltext settings.",
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
    logger = logging.getLogger("fulltext_download")

    config_path = Path(args.config) if args.config else PROJECT_ROOT / "manuscript" / "config.yaml"
    fulltext_cfg = load_fulltext_config(config_path) if config_path.exists() else {}

    fulltext_enabled = bool(fulltext_cfg.get("enabled"))
    unpaywall_email = fulltext_cfg.get("unpaywall_email") or ""
    download_dir = Path(args.output_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    if not fulltext_enabled:
        logger.warning(
            "project_config.fulltext.enabled is false in %s — skipping fulltext download. "
            "Enable it and set unpaywall_email to populate %s.",
            config_path,
            download_dir,
        )
        print(str(download_dir))
        return

    if not unpaywall_email:
        logger.warning(
            "fulltext.enabled is true but unpaywall_email is empty — only papers with "
            "an existing pdf_url will be downloaded (Unpaywall resolution is skipped)."
        )

    corpus = Corpus.load(Path(args.corpus))
    papers = corpus.papers
    if args.max_papers is not None:
        papers = papers[: args.max_papers]
    logger.info("Loaded %d papers for fulltext download", len(papers))

    success_count = 0
    text_count = 0
    skip_count = 0

    for paper in papers:
        result = download_and_extract_fulltext(
            paper,
            download_dir,
            unpaywall_email=unpaywall_email,
        )
        if result["pdf_path"] is not None:
            success_count += 1
            if result["text_path"] is not None:
                text_count += 1
            else:
                logger.warning(
                    "PDF downloaded for %s but text extraction failed",
                    paper.canonical_id[:40],
                )
        else:
            skip_count += 1

    logger.info(
        "Fulltext download complete: %d PDFs downloaded, %d text files extracted, "
        "%d skipped (no OA URL or download failed)",
        success_count,
        text_count,
        skip_count,
    )

    # Write an extraction-assessment JSON so downstream stages can check coverage
    corpus2 = Corpus.load(Path(args.corpus))
    extraction_report = assess_fulltext_extraction(corpus2, download_dir)
    report_path = download_dir.parent / "data" / "fulltext_extraction.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(extraction_report, handle, indent=2)
    print(str(report_path))


if __name__ == "__main__":
    main()
