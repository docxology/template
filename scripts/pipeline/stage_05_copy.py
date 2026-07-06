#!/usr/bin/env python3
"""Output copying orchestrator script.

This thin orchestrator coordinates the output copying stage:
1. Cleans the top-level output/ directory
2. Recursively copies entire project/output/ to top-level output/
3. Copies combined PDF to root for convenient access
4. Validates all expected files were copied

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

from infrastructure.core.logging.utils import get_logger, log_success, log_header
from infrastructure.core.files.cleanup import (
    clean_output_directory,
    clean_root_output_directory,
)
from infrastructure.core.files.operations import copy_final_deliverables
from infrastructure.project.discovery import resolve_project_root
from infrastructure.validation.output.validator import (
    validate_copied_outputs,
    validate_output_structure,
)
from infrastructure.reporting.output_statistics import (
    collect_output_statistics,
    generate_detailed_output_report,
    log_output_summary,
    write_output_statistics_reports,
)

# Set up logger for this module
logger = get_logger(__name__)


def log_stage(message: str) -> None:
    """Log a stage start message."""
    logger.info(f"\n  {message}")


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
    project_root = resolve_project_root(repo_root, args.project)
    output_dir = repo_root / "output" / args.project

    try:
        # Step 1: Clean root-level directories from output/ (keep only project folders)
        from infrastructure.project.discovery import discover_projects

        projects = discover_projects(repo_root)
        project_names = sorted({p.qualified_name for p in projects} | {args.project})
        if not clean_root_output_directory(repo_root, project_names):
            logger.error("Failed to clean root output directory")
            return 1

        # Step 2: Clean project-specific output directory
        clean_output_directory(output_dir)

        # Step 2: Copy final deliverables
        stats = copy_final_deliverables(repo_root, output_dir, args.project, project_dir=project_root)

        # Step 3: Validate copied files
        validation_passed = validate_copied_outputs(output_dir)

        # Step 3b: Validate directory structure
        structure_validation = validate_output_structure(output_dir)

        # Step 4: Collect comprehensive output statistics
        output_stats = collect_output_statistics(repo_root, args.project, project_dir=project_root)
        detailed_report = generate_detailed_output_report(output_dir, output_stats)

        # Log detailed report
        logger.info(detailed_report)

        report_file, json_file = write_output_statistics_reports(project_root / "output", output_stats)
        logger.info(f"Detailed output statistics saved to: {report_file}")
        logger.info(f"Output statistics JSON saved to: {json_file}")

        # Step 5: Log copy summary for the pipeline console
        log_output_summary(output_dir, dict(stats), structure_validation)

        # Determine success/failure
        if stats.get("total_files", 0) > 0 and validation_passed:
            log_success("\n✅ Output copying complete - all project outputs ready!", logger)
            return 0
        else:
            logger.error("\n❌ Output copying incomplete - check warnings above")
            return 1

    except Exception as e:
        logger.error(f"Unexpected error during output copying: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
