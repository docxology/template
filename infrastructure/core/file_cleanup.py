"""File and directory cleanup utilities.

This module provides functions for cleaning output directories and
coverage files. Extracted from file_operations.py for file-size health.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def clean_output_directory(output_dir: Path) -> None:
    """Clean top-level output directory before copying.

    Args:
        output_dir: Path to top-level output directory

    Raises:
        FileOperationError: If the directory cannot be created or cleaned.
    """
    logger.info("Cleaning output directory...")

    if not output_dir.exists():
        logger.info(f"Output directory does not exist, creating: {output_dir}")
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            log_success("Created output directory", logger)
            return
        except OSError as e:
            raise FileOperationError(f"Failed to create output directory {output_dir}: {e}") from e

    # Remove existing contents
    try:
        for item in output_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                logger.debug(f"  Removed directory: {item.name}")
            else:
                item.unlink()
                logger.debug(f"  Removed file: {item.name}")

        log_success("Output directory cleaned", logger)
    except OSError as e:
        raise FileOperationError(f"Failed to clean output directory {output_dir}: {e}") from e


def _clean_dir_preserving(
    dir_path: Path,
    output_dir: Path,
    preserved_relative_paths: set[Path],
    log: Any,
) -> None:
    """Remove all files inside *dir_path* except those in *preserved_relative_paths*.

    Paths in *preserved_relative_paths* are relative to *output_dir*.
    After removing files, any empty directories are cleaned up bottom-up.
    """
    preserved_count = 0
    removed_count = 0

    for file_path in list(dir_path.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(output_dir)
        if rel in preserved_relative_paths:
            log.info(f"  Preserving file for incremental processing: {rel}")
            preserved_count += 1
        else:
            file_path.unlink()
            removed_count += 1

    # Clean up empty directories bottom-up
    for sub in sorted(dir_path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if sub.is_dir() and not any(sub.iterdir()):
            sub.rmdir()

    if preserved_count:
        log.info(
            f"  Selectively cleaned {dir_path.name}/: "
            f"removed {removed_count} files, preserved {preserved_count}"
        )


def clean_output_directories(
    repo_root: Path, project_name: str = "project", subdirs: list[str] | None = None
) -> None:
    """Clean output directories for a fresh pipeline start.

    Removes all contents from both projects/{project_name}/output/ and output/{project_name}/ directories,
    then recreates the expected subdirectory structure.

    Log files are archived to logs/archive/ before cleanup to preserve execution history.

    Also cleans root-level directories from output/ that shouldn't exist.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")
        subdirs: List of subdirectories to recreate. If None, uses default list.
    """
    # Discover valid project names by scanning the projects/ directory directly.
    # Using Path scan instead of infrastructure.project.discovery avoids a
    # circular import: file_operations → project.discovery → core.logging_utils.
    projects_dir = repo_root / "projects"
    project_names: list[str] = (
        [d.name for d in projects_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if projects_dir.exists()
        else []
    )

    # Clean root-level directories from output/ before cleaning project-specific directories
    clean_root_output_directory(repo_root, project_names)

    if subdirs is None:
        subdirs = [
            "pdf",
            "figures",
            "data",
            "reports",
            "simulations",
            "slides",
            "web",
            "logs",
            "llm",
        ]

    output_dirs = [
        repo_root / "projects" / project_name / "output",
        repo_root / "output" / project_name,
    ]

    for output_dir in output_dirs:
        relative_path = output_dir.relative_to(repo_root)

        if output_dir.exists():
            logger.info(f"  Cleaning {relative_path}/...")

            # Archive log files before cleanup
            logs_dir = output_dir / "logs"
            if logs_dir.exists():
                archive_dir = logs_dir / "archive"
                archive_dir.mkdir(parents=True, exist_ok=True)

                # Archive all .log files
                log_files = list(logs_dir.glob("*.log"))
                if log_files:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archived_count = 0
                    for log_file in log_files:
                        try:
                            archive_path = (
                                archive_dir / f"{log_file.stem}_{timestamp}{log_file.suffix}"
                            )
                            shutil.copy2(log_file, archive_path)
                            archived_count += 1
                            logger.debug(
                                f"  Archived log file: {log_file.name} → {archive_path.name}"
                            )
                        except (OSError, shutil.Error) as e:
                            logger.warning(f"  Failed to archive log file {log_file.name}: {e}")

                    if archived_count > 0:
                        logger.info(f"  Archived {archived_count} log file(s) to logs/archive/")

            # Remove all contents except .checkpoints directory and specific
            # persistence files that support incremental processing across runs.
            # Paths are relative to output_dir so files inside subdirectories
            # (e.g. data/nanopublications.jsonl) are correctly preserved.
            preserved_relative_paths = {
                Path("data") / "corpus.jsonl",
                Path("data") / "nanopublications.jsonl",
                Path("data") / "nanopublications.trig",
            }

            for item in output_dir.iterdir():
                if item.is_dir():
                    # Preserve .checkpoints directory to maintain pipeline resume capability
                    if item.name == ".checkpoints":
                        logger.debug(f"  Preserving {item.name}/ directory for checkpoint resume")
                        continue

                    # Check if this subdirectory contains any preserved files
                    has_preserved = any(
                        p.parts[0] == item.name for p in preserved_relative_paths
                    )
                    if has_preserved:
                        # Selectively clean: remove everything except preserved files
                        _clean_dir_preserving(
                            item, output_dir, preserved_relative_paths, logger,
                        )
                    else:
                        shutil.rmtree(item)
                else:
                    # Root-level files: preserve if in the preserve set (incremental pipeline)
                    if Path(item.name) in preserved_relative_paths:
                        logger.debug(f"  Preserving file for incremental processing: {item.name}")
                    else:
                        item.unlink()
        else:
            logger.info(f"  Creating {relative_path}/...")

        # Recreate subdirectory structure
        for subdir in subdirs:
            (output_dir / subdir).mkdir(parents=True, exist_ok=True)

        log_success(f"Cleaned {relative_path}/ (recreated subdirectories)", logger)

    log_success(f"Output directories cleaned for project '{project_name}' - fresh start", logger)


def clean_root_output_directory(repo_root: Path, project_names: list[str]) -> bool:
    """Clean root-level directories from output/ directory.

    Removes root-level directories (data/, figures/, pdf/, etc.) from output/
    that aren't project folders. Only project-specific folders should remain.

    Args:
        repo_root: Repository root directory
        project_names: List of discovered project names

    Returns:
        True if cleanup successful, False otherwise
    """
    output_dir = repo_root / "output"

    if not output_dir.exists():
        logger.debug("Output directory does not exist, nothing to clean")
        return True

    logger.info("Cleaning root-level directories from output/ directory...")

    try:
        # Track what we remove and keep
        removed_items = []
        kept_items = []

        for item in output_dir.iterdir():
            if item.is_dir():
                item_name = item.name

                # Keep project-specific folders
                if item_name in project_names:
                    kept_items.append(item_name)
                    continue

                # Keep special directories that might be needed
                special_dirs = {
                    ".gitkeep",
                    ".gitignore",
                    "multi_project_summary",  # Multi-project summary reports
                    "executive_summary",  # Executive reporting outputs
                }
                if item_name in special_dirs:
                    kept_items.append(item_name)
                    continue

                # Remove root-level directories that shouldn't exist
                # These are directories that should only exist within project folders
                root_level_dirs = {
                    "data",
                    "figures",
                    "pdf",
                    "web",
                    "slides",
                    "reports",
                    "simulations",
                    "llm",
                    "logs",
                    "tex",
                }

                if item_name in root_level_dirs:
                    logger.debug(f"  Removing root-level directory: {item_name}")
                    shutil.rmtree(item)
                    removed_items.append(item_name)
                else:
                    # Unknown directory - keep it but log it
                    logger.warning(f"  Unknown directory in output/: {item_name} (keeping)")
                    kept_items.append(item_name)

            else:
                # Keep non-directory items (files)
                kept_items.append(item.name)

        if removed_items:
            logger.info(f"Removed root-level directories: {', '.join(removed_items)}")
        if kept_items:
            logger.debug(f"Kept items: {', '.join(kept_items)}")

        log_success("Root output directory cleaned", logger)
        return True

    except OSError as e:
        logger.error(f"Failed to clean root output directory: {e}", exc_info=True)
        return False


def clean_coverage_files(repo_root: Path, patterns: list[str] | None = None) -> bool:
    """Clean coverage database files to prevent corruption.

    Removes coverage database files that can become corrupted during parallel
    test execution or when tests are interrupted.

    Args:
        repo_root: Repository root directory
        patterns: List of file patterns to clean (default: coverage-related files)

    Returns:
        True if cleanup successful, False otherwise
    """
    if patterns is None:
        patterns = [
            "**/.coverage",  # Main coverage database (recursive)
            "**/.coverage.*",  # Lock files and temporary coverage files (recursive)
            "**/coverage_*.json",  # JSON coverage reports (recursive)
        ]

    logger.info("Cleaning coverage database files...")

    try:
        removed_files = []
        locked_files = []

        # Clean each pattern
        for pattern in patterns:
            if "*" in pattern:
                # Glob pattern - search for matching files recursively
                glob_pattern = f"**/{pattern}" if not pattern.startswith("**/") else pattern
                for file_path in repo_root.glob(glob_pattern):
                    try:
                        file_path.unlink()
                        removed_files.append(str(file_path.relative_to(repo_root)))
                        logger.debug(f"  Removed: {file_path.relative_to(repo_root)}")
                    except PermissionError:
                        locked_files.append(str(file_path.relative_to(repo_root)))
                        logger.debug(f"  Skipped (locked): {file_path.relative_to(repo_root)}")
                    except OSError as e:
                        logger.debug(f"  Failed to remove {file_path.relative_to(repo_root)}: {e}")
            else:
                # Exact filename
                file_path = repo_root / pattern
                if file_path.exists():
                    try:
                        file_path.unlink()
                        removed_files.append(str(file_path.name))
                        logger.debug(f"  Removed: {file_path.name}")
                    except PermissionError:
                        locked_files.append(str(file_path.name))
                        logger.debug(f"  Skipped (locked): {file_path.name}")
                    except OSError as e:
                        logger.debug(f"  Failed to remove {file_path.name}: {e}")

        # Log results
        if removed_files:
            logger.info(f"Removed coverage files: {', '.join(removed_files)}")
        if locked_files:
            logger.warning(f"Skipped locked coverage files: {', '.join(locked_files)}")
            logger.info("Locked files will be cleaned on next successful test run")

        log_success("Coverage database cleanup completed", logger)
        return True

    except OSError as e:
        logger.error(f"Failed to clean coverage database files: {e}", exc_info=True)
        return False
