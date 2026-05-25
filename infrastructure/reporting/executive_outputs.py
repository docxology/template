"""Executive output organization helpers used by root scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_header, log_success, log_substep
from infrastructure.reporting.output_organizer import OrganizationResult, OutputOrganizer

logger = get_logger(__name__)


@dataclass(frozen=True)
class ExecutiveOutputOptions:
    """Options for executive output organization."""

    dry_run: bool = False
    executive_only: bool = False
    multi_project_only: bool = False


def organize_executive_summary(repo_root: Path, dry_run: bool = False) -> int:
    """Organize files in ``output/executive_summary`` by type."""
    executive_dir = repo_root / "output" / "executive_summary"
    if not executive_dir.exists():
        logger.warning(f"Executive summary directory not found: {executive_dir}")
        return 0

    logger.info(f"Organizing executive summary outputs in: {executive_dir}")
    organizer = OutputOrganizer()
    if dry_run:
        _log_dry_run_summary(organizer, executive_dir, limit=5)
        return 0

    log_substep("Moving existing files to type-specific subdirectories...", logger)
    result = organizer.organize_existing_files(executive_dir)
    _log_organization_result(result)

    log_substep("Copying combined PDFs from all projects...", logger)
    copied_count = organizer.copy_combined_pdfs(repo_root, executive_dir)
    logger.info(f"  - Copied: {copied_count} combined PDF files")
    _log_final_summary(organizer, executive_dir)
    return result.moved_files + copied_count


def organize_multi_project_summary(repo_root: Path, dry_run: bool = False) -> int:
    """Organize files in ``output/multi_project_summary`` by type."""
    multi_project_dir = repo_root / "output" / "multi_project_summary"
    if not multi_project_dir.exists():
        logger.warning(f"Multi-project summary directory not found: {multi_project_dir}")
        return 0

    logger.info(f"Organizing multi-project summary outputs in: {multi_project_dir}")
    organizer = OutputOrganizer()
    if dry_run:
        _log_dry_run_summary(organizer, multi_project_dir, limit=None)
        return 0

    log_substep("Moving existing files to type-specific subdirectories...", logger)
    result = organizer.organize_existing_files(multi_project_dir)
    _log_organization_result(result)
    _log_final_summary(organizer, multi_project_dir)
    return result.moved_files


def run_executive_output_organization(repo_root: Path, options: ExecutiveOutputOptions) -> int:
    """Run executive and multi-project output organization."""
    log_header("EXECUTIVE OUTPUTS REORGANIZATION", logger)
    logger.info(f"Repository root: {repo_root}")
    if options.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    total_moved = 0
    if not options.multi_project_only:
        logger.info("")
        log_header("EXECUTIVE SUMMARY ORGANIZATION", logger)
        total_moved += organize_executive_summary(repo_root, options.dry_run)
    if not options.executive_only:
        logger.info("")
        log_header("MULTI-PROJECT SUMMARY ORGANIZATION", logger)
        total_moved += organize_multi_project_summary(repo_root, options.dry_run)

    logger.info("")
    log_success("REORGANIZATION COMPLETE", logger)
    if options.dry_run:
        logger.info("This was a dry run - no files were moved")
    else:
        logger.info(f"Total files processed: {total_moved}")
    return total_moved


def _log_dry_run_summary(organizer: OutputOrganizer, directory: Path, *, limit: int | None) -> None:
    logger.info("DRY RUN MODE - No files will be moved")
    summary = organizer.get_organized_structure_summary(directory)
    logger.info("Current organization:")
    for subdir, files in summary.items():
        logger.info(f"  {subdir}/: {len(files)} files")
        display_files = sorted(files) if limit is None else sorted(files)[:limit]
        for file in display_files:
            logger.info(f"    - {file}")
        if limit is not None and len(files) > limit:
            logger.info(f"    ... and {len(files) - limit} more")


def _log_organization_result(result: OrganizationResult) -> None:
    logger.info("Organization complete:")
    logger.info(f"  - Moved: {result.moved_files} files")
    logger.info(f"  - Skipped: {result.skipped_files} files (already organized)")
    logger.info(f"  - Errors: {result.error_files} files")
    logger.info(f"  - Created: {result.created_dirs} subdirectories")


def _log_final_summary(organizer: OutputOrganizer, directory: Path) -> None:
    log_substep("Final organization:", logger)
    summary = organizer.get_organized_structure_summary(directory)
    for subdir, files in sorted(summary.items()):
        logger.info(f"  {subdir}/: {len(files)} files")
    total_files = sum(len(files) for files in summary.values())
    logger.info(f"Total organized files: {total_files}")
