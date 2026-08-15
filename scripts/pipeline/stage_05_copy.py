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

from infrastructure.core.logging.utils import get_logger, log_success, log_header
from infrastructure.core.files.cleanup import (
    clean_final_output_directory,
    clean_root_output_directory,
)
from infrastructure.core.files.operations import copy_final_deliverables
from infrastructure.orchestration.discovery import validate_project_slug
from infrastructure.project.discovery import resolve_project_root
from infrastructure.validation.output.validator import (
    validate_copied_outputs,
    validate_output_structure,
)
from infrastructure.validation.output.render_formats import (
    enabled_render_formats,
    load_effective_rendering_config,
    remove_disabled_render_outputs,
    render_config_manuscript_dir,
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


def execute_copy_stage(project_name: str, *, repo_root: Path) -> int:
    """Copy and validate one already-resolved project using real files."""

    project_root = resolve_project_root(repo_root, project_name)
    output_dir = repo_root / "output" / project_name

    try:
        render_config = load_effective_rendering_config(project_root)
    except (OSError, TypeError, ValueError) as exc:
        logger.error("Could not determine enabled render formats: %s", exc)
        return 1
    formats = enabled_render_formats(render_config)
    manuscript_dir = render_config_manuscript_dir(project_root)

    try:
        # Step 1: Clean root-level directories from output/ (keep only project folders)
        from infrastructure.project.discovery import discover_projects

        projects = discover_projects(repo_root)
        project_names = sorted({p.qualified_name for p in projects} | {project_name})
        if not clean_root_output_directory(repo_root, project_names):
            logger.error("Failed to clean root output directory")
            return 1

        # Step 2: Clean project-specific output directory
        clean_final_output_directory(output_dir)

        # Step 2: Copy final deliverables
        stats = copy_final_deliverables(repo_root, output_dir, project_name, project_dir=project_root)

        # Step 3: Filter stale artifacts for formats disabled in this run.
        # The source project tree is preserved; only the freshly cleaned copy
        # is narrowed to the effective publication-format contract.
        remove_disabled_render_outputs(output_dir, project_name, formats)

        # Refresh copy counts after format filtering so the console summary
        # describes the deliverables that actually remain.
        stats["pdf_files"] = sum(1 for path in (output_dir / "pdf").rglob("*") if path.is_file())
        stats["web_files"] = sum(1 for path in (output_dir / "web").rglob("*") if path.is_file())
        stats["slides_files"] = sum(1 for path in (output_dir / "slides").rglob("*") if path.is_file())
        stats["combined_pdf"] = int((output_dir / f"{Path(project_name).name}_combined.pdf").is_file())
        stats["total_files"] = sum(1 for path in output_dir.rglob("*") if path.is_file())

        # Step 4: Validate copied files
        validation_passed = validate_copied_outputs(
            output_dir,
            project_name=project_name,
            enabled_formats=formats,
            manuscript_dir=manuscript_dir,
        )

        # Step 4b: Validate directory structure without inventing a PDF
        # requirement for configurations that explicitly disable it.
        structure_validation = validate_output_structure(output_dir, require_pdf=render_config.enable_pdf)

        # Step 5: Collect comprehensive output statistics
        output_stats = collect_output_statistics(repo_root, project_name, project_dir=project_root)
        detailed_report = generate_detailed_output_report(output_dir, output_stats)

        logger.info(detailed_report)

        report_file, json_file = write_output_statistics_reports(project_root / "output", output_stats)
        logger.info(f"Detailed output statistics saved to: {report_file}")
        logger.info(f"Output statistics JSON saved to: {json_file}")

        # Step 6: Log copy summary for the pipeline console
        log_output_summary(output_dir, dict(stats), structure_validation)

        if stats.get("total_files", 0) > 0 and validation_passed:
            log_success("\n✅ Output copying complete - all project outputs ready!", logger)
            return 0
        logger.error("\n❌ Output copying incomplete - check warnings above")
        return 1

    except Exception as exc:
        logger.error(f"Unexpected error during output copying: {exc}", exc_info=True)
        return 1


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
