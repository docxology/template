#!/usr/bin/env python3
"""Executive outputs reorganization script.

This script reorganizes existing executive summary and multi-project summary
outputs by moving files into type-specific subdirectories using the OutputOrganizer.

Usage:
    python3 scripts/organize_executive_outputs.py
    python3 scripts/organize_executive_outputs.py --dry-run
    python3 scripts/organize_executive_outputs.py --executive-only
    python3 scripts/organize_executive_outputs.py --multi-project-only

The script will:
1. Organize files in output/executive_summary/ by type (png/, pdf/, csv/, html/, json/, md/)
2. Organize files in output/multi_project_summary/ by type (json/, md/)
3. Copy combined PDFs from all projects to output/executive_summary/combined_pdfs/
4. Provide detailed logging of all operations

This is a safe, idempotent operation that can be run multiple times.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_header, log_success, log_substep
from infrastructure.reporting.output_organizer import OutputOrganizer


def organize_executive_summary(repo_root: Path, dry_run: bool = False) -> int:
    """
    Organize files in the executive summary directory.

    Args:
        repo_root: Repository root directory
        dry_run: If True, only show what would be done without making changes

    Returns:
        Number of files moved
    """
    executive_dir = repo_root / "output" / "executive_summary"

    if not executive_dir.exists():
        logger.warning(f"Executive summary directory not found: {executive_dir}")
        return 0

    logger.info(f"Organizing executive summary outputs in: {executive_dir}")

    organizer = OutputOrganizer()

    if dry_run:
        logger.info("DRY RUN MODE - No files will be moved")
        summary = organizer.get_organized_structure_summary(executive_dir)
        logger.info("Current organization:")
        for subdir, files in summary.items():
            logger.info(f"  {subdir}/: {len(files)} files")
            for file in sorted(files)[:5]:  # Show first 5 files
                logger.info(f"    - {file}")
            if len(files) > 5:
                logger.info(f"    ... and {len(files) - 5} more")
        return 0

    # Organize existing files
    log_substep("Moving existing files to type-specific subdirectories...", logger)
    result = organizer.organize_existing_files(executive_dir)

    logger.info("Organization complete:")
    logger.info(f"  - Moved: {result.moved_files} files")
    logger.info(f"  - Skipped: {result.skipped_files} files (already organized)")
    logger.info(f"  - Errors: {result.error_files} files")
    logger.info(f"  - Created: {result.created_dirs} subdirectories")

    # Copy combined PDFs
    log_substep("Copying combined PDFs from all projects...", logger)
    copied_count = organizer.copy_combined_pdfs(repo_root, executive_dir)
    logger.info(f"  - Copied: {copied_count} combined PDF files")

    # Show final organization
    log_substep("Final organization:", logger)
    summary = organizer.get_organized_structure_summary(executive_dir)
    for subdir, files in sorted(summary.items()):
        logger.info(f"  {subdir}/: {len(files)} files")

    total_files = sum(len(files) for files in summary.values())
    logger.info(f"Total organized files: {total_files}")

    return result.moved_files + copied_count


def organize_multi_project_summary(repo_root: Path, dry_run: bool = False) -> int:
    """
    Organize files in the multi-project summary directory.

    Args:
        repo_root: Repository root directory
        dry_run: If True, only show what would be done without making changes

    Returns:
        Number of files moved
    """
    multi_project_dir = repo_root / "output" / "multi_project_summary"

    if not multi_project_dir.exists():
        logger.warning(f"Multi-project summary directory not found: {multi_project_dir}")
        return 0

    logger.info(f"Organizing multi-project summary outputs in: {multi_project_dir}")

    organizer = OutputOrganizer()

    if dry_run:
        logger.info("DRY RUN MODE - No files will be moved")
        summary = organizer.get_organized_structure_summary(multi_project_dir)
        logger.info("Current organization:")
        for subdir, files in summary.items():
            logger.info(f"  {subdir}/: {len(files)} files")
            for file in sorted(files):
                logger.info(f"    - {file}")
        return 0

    # Organize existing files
    log_substep("Moving existing files to type-specific subdirectories...", logger)
    result = organizer.organize_existing_files(multi_project_dir)

    logger.info("Organization complete:")
    logger.info(f"  - Moved: {result.moved_files} files")
    logger.info(f"  - Skipped: {result.skipped_files} files (already organized)")
    logger.info(f"  - Errors: {result.error_files} files")
    logger.info(f"  - Created: {result.created_dirs} subdirectories")

    # Show final organization
    log_substep("Final organization:", logger)
    summary = organizer.get_organized_structure_summary(multi_project_dir)
    for subdir, files in sorted(summary.items()):
        logger.info(f"  {subdir}/: {len(files)} files")

    total_files = sum(len(files) for files in summary.values())
    logger.info(f"Total organized files: {total_files}")

    return result.moved_files


def main() -> int:
    """Main entry point for the reorganization script."""
    parser = argparse.ArgumentParser(
        description="Reorganize executive summary and multi-project summary outputs by file type",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/organize_executive_outputs.py
  python3 scripts/organize_executive_outputs.py --dry-run
  python3 scripts/organize_executive_outputs.py --executive-only
  python3 scripts/organize_executive_outputs.py --multi-project-only
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    parser.add_argument(
        "--executive-only",
        action="store_true",
        help="Only organize executive summary outputs"
    )

    parser.add_argument(
        "--multi-project-only",
        action="store_true",
        help="Only organize multi-project summary outputs"
    )

    args = parser.parse_args()

    # Set up logging
    global logger
    logger = get_logger(__name__)

    # Determine repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    log_header("EXECUTIVE OUTPUTS REORGANIZATION", logger)
    logger.info(f"Repository root: {repo_root}")
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    total_moved = 0

    try:
        # Organize executive summary
        if not args.multi_project_only:
            logger.info("")
            log_header("EXECUTIVE SUMMARY ORGANIZATION", logger)
            moved = organize_executive_summary(repo_root, args.dry_run)
            total_moved += moved

        # Organize multi-project summary
        if not args.executive_only:
            logger.info("")
            log_header("MULTI-PROJECT SUMMARY ORGANIZATION", logger)
            moved = organize_multi_project_summary(repo_root, args.dry_run)
            total_moved += moved

        # Final summary
        logger.info("")
        log_success("REORGANIZATION COMPLETE", logger)
        if args.dry_run:
            logger.info("This was a dry run - no files were moved")
        else:
            logger.info(f"Total files processed: {total_moved}")

        return 0

    except Exception as e:
        logger.error(f"Reorganization failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())