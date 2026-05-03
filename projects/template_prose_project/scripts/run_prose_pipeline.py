#!/usr/bin/env python3
"""Thin orchestrator: read manuscript → analyse prose → check → review report.

All logic lives in :mod:`template_prose_project.pipeline`,
:mod:`template_prose_project.figures`, and
:mod:`template_prose_project.report`. This script's job is to wire those
functions to the filesystem.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))

from infrastructure.core.logging.utils import get_logger

from src.config import load_project_config
from src.pipeline import run_prose_pipeline
from src.report import write_review_report

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
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
        "--strict",
        action="store_true",
        help="Exit non-zero when any configured check fails.",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config = load_project_config(args.config)

    logger.info("Running prose pipeline for: %s", config.title)
    artifacts = run_prose_pipeline(config, project_root=project_root)

    logger.info(
        "Prose run complete: %d files, %d words, all_passed=%s",
        len(artifacts.manuscript_report.files),
        artifacts.total_words,
        artifacts.all_passed,
    )
    if artifacts.report_path is not None:
        print(str(artifacts.report_path))

    review_path = (project_root / config.report.output_path).resolve()
    write_review_report(
        review_path,
        title=config.title,
        manuscript_report=artifacts.manuscript_report,
        checks=artifacts.checks,
        include_per_file_table=config.report.include_per_file_table,
        include_outline=config.report.include_outline,
        include_quality_flags=config.report.include_quality_flags,
    )
    print(str(review_path))

    summary_path = (project_root / "output" / "run_summary.json").resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "title": config.title,
        "files": len(artifacts.manuscript_report.files),
        "total_words": artifacts.total_words,
        "all_passed": artifacts.all_passed,
        "checks": [c.to_dict() for c in artifacts.checks],
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(str(summary_path))

    if args.strict and not artifacts.all_passed:
        logger.warning("Strict mode: exiting 1 because checks failed")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
