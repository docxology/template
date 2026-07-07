#!/usr/bin/env python3
"""LLM Manuscript Review orchestrator script.

This thin orchestrator coordinates the LLM review stage:
1. Checks Ollama availability and selects best model
2. Extracts text from combined manuscript PDF (full content, no truncation by default)
3. Generates configured review types (default: executive_summary only)
4. Generates translations to configured languages (if enabled)
5. Validates review quality and retries if needed
6. Saves all reviews to output/llm/ with detailed metrics

Stage 06 of the pipeline orchestration (reviews and translations) - uses
local Ollama LLM for manuscript analysis and review generation.

CLI Usage:
- python3 scripts/pipeline/stage_06_llm_review.py                # Run both reviews and translations
- python3 scripts/pipeline/stage_06_llm_review.py --reviews-only # Run only English scientific reviews
- python3 scripts/pipeline/stage_06_llm_review.py --translations-only # Run only translations

Exit codes:
    0: LLM review/translation completed successfully
    1: LLM pipeline failed hard (configuration error, unrecoverable runtime error)
    2: LLM stage skipped gracefully (Ollama unavailable, no model installed) — callers
       should treat this as a non-fatal soft-skip rather than a failure

These map to ``scripts.exit_codes.ExitCode`` (SUCCESS=0 / FAILURE=1 / SKIP=2).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add root to path for infrastructure imports
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.core.pipeline import stage_label
from infrastructure.llm.review.pipeline_runner import ReviewMode, run_llm_review_pipeline

# Set up logger for this module
logger = get_logger(__name__)

# Repo root used to resolve pipeline.yaml candidates for stage labelling.
_REPO_ROOT = Path(__file__).resolve().parents[2]


def main(mode: str = ReviewMode.ALL, project_name: str = "project") -> int:
    """Execute LLM manuscript review orchestration.

    Args:
        mode: Execution mode - ALL (both), REVIEWS_ONLY, or TRANSLATIONS_ONLY
        project_name: Name of project in projects/ directory

    Returns:
        Exit code (0=success, 1=failure, 2=skipped)
    """
    if mode == ReviewMode.REVIEWS_ONLY:
        label = stage_label("LLM Scientific Review", project_name, repo_root=_REPO_ROOT)
        log_header(f"{label} (English)", logger)
    elif mode == ReviewMode.TRANSLATIONS_ONLY:
        log_header(stage_label("LLM Translations", project_name, repo_root=_REPO_ROOT), logger)
    else:
        # ALL mode runs both reviews and translations; use the review stage as
        # the lead banner since it executes first.
        label = stage_label("LLM Scientific Review", project_name, repo_root=_REPO_ROOT)
        log_header(f"{label.split(':')[0]}: LLM Manuscript Review", logger)

    repo_root = _REPO_ROOT
    exit_code = run_llm_review_pipeline(mode=mode, project_name=project_name, repo_root=repo_root)
    if exit_code == 0:
        log_success("LLM review stage completed successfully", logger)
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Manuscript Review Orchestrator")
    parser.add_argument(
        "--project",
        type=str,
        default="project",
        help="Project name in projects/ directory (default: project)",
    )

    # Mutually exclusive group for execution mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--reviews-only",
        action="store_true",
        help="Run only English scientific reviews (no translations)",
    )
    mode_group.add_argument(
        "--translations-only",
        action="store_true",
        help="Run only translations (no scientific reviews)",
    )

    args = parser.parse_args()

    try:
        if args.reviews_only:
            exec_mode = ReviewMode.REVIEWS_ONLY
        elif args.translations_only:
            exec_mode = ReviewMode.TRANSLATIONS_ONLY
        else:
            exec_mode = ReviewMode.ALL

        sys.exit(main(mode=exec_mode, project_name=args.project))
    except KeyboardInterrupt:
        logger.info("\nLLM Review cancelled by user.")
        sys.exit(130)
