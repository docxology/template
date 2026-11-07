#!/usr/bin/env python3
"""Output validation orchestrator script.

This thin orchestrator coordinates the validation stage:
1. Validates generated PDFs
2. Checks markdown formatting
3. Verifies file integrity
4. Generates validation report

Stage 04 of the pipeline orchestration.

Exit codes:
    0: All critical validations passed (PDFs present, markdown well-formed)
    1: At least one critical validation failed
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.logging.utils import get_logger, log_header
from infrastructure.core.project_paths import resolve_project_root
from infrastructure.validation.output.pipeline import execute_validation_pipeline
from infrastructure.validation.publication.rendered_provenance import (
    RenderedProvenanceError,
    write_rendered_provenance_receipt,
)

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute validation orchestration."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate output")
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    args = parser.parse_args()

    log_header(f"STAGE 04: Validate Output (Project: {args.project})", logger)

    repo_root = Path(__file__).resolve().parents[2]
    try:
        project_root = resolve_project_root(repo_root, args.project)
        with project_output_lock(project_root):
            if resolve_project_root(repo_root, args.project) != project_root:
                logger.error("Validation project moved before acquiring its output lock")
                return 1
            return _validate_and_seal(args.project, repo_root)
    except (OSError, ValueError) as exc:
        logger.error("Validation project failed: %s", exc)
        return 1


def _validate_and_seal(project_name: str, repo_root: Path) -> int:
    result = execute_validation_pipeline(project_name, repo_root=repo_root)
    if result != 0:
        return result
    try:
        receipt = write_rendered_provenance_receipt(repo_root, project_name)
    except RenderedProvenanceError as exc:
        logger.error("Rendered provenance receipt failed [%s]: %s", exc.code, exc)
        return 1
    logger.info(
        "Rendered provenance receipt: %d source, %d config, %d output files",
        receipt.source.file_count,
        receipt.config.file_count,
        receipt.output.file_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
