#!/usr/bin/env python3
"""Output copying orchestrator script.

This thin orchestrator coordinates the output copying stage:
1. Cleans generated content from the top-level project output while preserving
   independently produced release bundles and publication receipts
2. Recursively copies entire project/output/ to top-level output/
3. Removes copied artifacts for formats disabled by the effective configuration
4. Validates every enabled canonical deliverable

Stage 05 of the pipeline orchestration - copies all project outputs to
the top-level output/ directory for easy access.

Complete project outputs copied:
- PDF manuscript (pdf/ directory + root copy of `{project}_combined.pdf`)
- Presentation slides (slides/ directory - all formats and metadata)
- Web outputs (web/ directory - all HTML files)
- Generated figures (figures/ directory - all images and PDFs)
- Data files (data/ directory - all CSV, NPZ files)
- Reports (reports/ directory - all markdown/analysis files)
- Simulations (simulations/ directory - all simulation outputs and checkpoints)
- LLM reviews (llm/ directory - LLM-generated manuscript reviews)

Exit codes:
    0: Copy completed and post-copy validation passed
    1: Copy failed or post-copy validation found missing critical files
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header
from infrastructure.orchestration.discovery import validate_project_slug
from infrastructure.orchestration.stage_policy import execute_copy_stage

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute output copying orchestration.

    Returns:
        Exit code (0=success, 1=failure)
    """
    import argparse

    parser = argparse.ArgumentParser(description="Copy outputs")
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    args = parser.parse_args()

    log_header(f"STAGE 05: Copy Outputs (Project: {args.project})", logger)

    repo_root = Path(__file__).resolve().parents[2]
    try:
        project_name = validate_project_slug(args.project, repo_root)
    except ValueError as exc:
        logger.error("Invalid project: %s", exc)
        return 1
    return execute_copy_stage(project_name, repo_root=repo_root)


if __name__ == "__main__":
    exit(main())
