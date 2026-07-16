"""CLI orchestration for the opt-in full-text enrichment stage.

The numbered script delegates here so configuration resolution, corpus
iteration, download accounting, and report persistence remain covered source
behavior rather than script-local business logic.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from config import CORPUS_PATH as DEFAULT_CORPUS_PATH
from config_loader import load_fulltext_config, resolve_fulltext_directory
from literature.corpus import Corpus
from literature.fulltext_download import (
    assess_fulltext_extraction,
    download_and_extract_fulltext,
)

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class FulltextDownloadRun:
    """Summary returned by :func:`run_fulltext_download`."""

    artifact_path: Path
    enabled: bool
    attempted: int = 0
    pdf_count: int = 0
    text_count: int = 0
    skipped_count: int = 0


def run_fulltext_download(
    *,
    project_root: Path,
    corpus_path: Path,
    config_path: Path,
    output_override: str | None = None,
    max_papers: int | None = None,
    logger: logging.Logger | None = None,
) -> FulltextDownloadRun:
    """Run configured full-text enrichment and persist its coverage report."""
    log = logger or logging.getLogger(__name__)
    fulltext_config = load_fulltext_config(config_path) if config_path.exists() else {}
    download_dir, _ = resolve_fulltext_directory(
        project_root=project_root,
        fulltext_config=fulltext_config,
        override=output_override,
    )
    download_dir.mkdir(parents=True, exist_ok=True)

    if not bool(fulltext_config.get("enabled")):
        log.warning(
            "project_config.fulltext.enabled is false in %s — skipping fulltext download. "
            "Enable it and set unpaywall_email to populate %s.",
            config_path,
            download_dir,
        )
        return FulltextDownloadRun(artifact_path=download_dir, enabled=False)

    unpaywall_email = str(fulltext_config.get("unpaywall_email") or "")
    if not unpaywall_email:
        log.warning(
            "fulltext.enabled is true but unpaywall_email is empty — only papers with "
            "an existing pdf_url will be downloaded (Unpaywall resolution is skipped)."
        )

    corpus = Corpus.load(corpus_path)
    papers = corpus.papers
    if max_papers is not None:
        papers = papers[:max_papers]
    log.info("Loaded %d papers for fulltext download", len(papers))

    pdf_count = 0
    text_count = 0
    skipped_count = 0
    for paper in papers:
        result = download_and_extract_fulltext(
            paper,
            download_dir,
            unpaywall_email=unpaywall_email,
        )
        if result["pdf_path"] is None:
            skipped_count += 1
            continue
        pdf_count += 1
        if result["text_path"] is not None:
            text_count += 1
        else:
            log.warning(
                "PDF downloaded for %s but text extraction failed",
                paper.canonical_id[:40],
            )

    log.info(
        "Fulltext download complete: %d PDFs downloaded, %d text files extracted, "
        "%d skipped (no OA URL or download failed)",
        pdf_count,
        text_count,
        skipped_count,
    )
    report_path = download_dir.parent / "data" / "fulltext_extraction.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = assess_fulltext_extraction(corpus, download_dir)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return FulltextDownloadRun(
        artifact_path=report_path,
        enabled=True,
        attempted=len(papers),
        pdf_count=pdf_count,
        text_count=text_count,
        skipped_count=skipped_count,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Download and extract open-access full text for the corpus.")
    parser.add_argument("--corpus", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=(
            "Override the directory for .pdf, .txt, and figures/ files "
            "(default: config's fulltext.download_dir, then output/fulltext)."
        ),
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
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    project_root: Path | None = None,
) -> FulltextDownloadRun:
    """Run the Stage 11 command and print its primary artifact path."""
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root = Path(project_root) if project_root is not None else DEFAULT_PROJECT_ROOT
    config_path = Path(args.config) if args.config else root / "manuscript" / "config.yaml"
    result = run_fulltext_download(
        project_root=root,
        corpus_path=Path(args.corpus),
        config_path=config_path,
        output_override=args.output_dir,
        max_papers=args.max_papers,
        logger=logging.getLogger("fulltext_download"),
    )
    print(str(result.artifact_path))
    return result


__all__ = [
    "FulltextDownloadRun",
    "main",
    "parse_args",
    "run_fulltext_download",
]
