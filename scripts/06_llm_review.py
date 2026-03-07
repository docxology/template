#!/usr/bin/env python3
"""LLM Manuscript Review orchestrator script.

This thin orchestrator coordinates the LLM review stage:
1. Checks Ollama availability and selects best model
2. Extracts text from combined manuscript PDF (full content, no truncation by default)
3. Generates configured review types (default: executive_summary only)
4. Generates translations to configured languages (if enabled)
5. Validates review quality and retries if needed
6. Saves all reviews to output/llm/ with detailed metrics

Stage 8/9 of the pipeline orchestration - uses local Ollama LLM for
manuscript analysis and review generation.

CLI Usage:
- python3 scripts/06_llm_review.py                # Run both reviews and translations
- python3 scripts/06_llm_review.py --reviews-only # Run only English scientific reviews
- python3 scripts/06_llm_review.py --translations-only # Run only translations
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.llm.review.pipeline_runner import ReviewMode, run_llm_review_pipeline

# Set up logger for this module
logger = get_logger(__name__)


def main(mode: str = ReviewMode.ALL, project_name: str = "project") -> int:
    """Execute LLM manuscript review orchestration.

    Args:
        mode: Execution mode - ALL (both), REVIEWS_ONLY, or TRANSLATIONS_ONLY
        project_name: Name of project in projects/ directory

    Returns:
        Exit code (0=success, 1=failure, 2=skipped)
    """
    if mode == ReviewMode.REVIEWS_ONLY:
        log_header("Stage 8/9: LLM Scientific Review (English)", logger)
    elif mode == ReviewMode.TRANSLATIONS_ONLY:
        log_header("Stage 9/9: LLM Translations", logger)
    else:
        log_header("Stage 8/9: LLM Manuscript Review", logger)

    repo_root = Path(__file__).parent.parent
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
