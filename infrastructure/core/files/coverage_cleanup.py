"""Coverage file cleanup utilities.

This module provides functions for cleaning coverage database files
that can become corrupted during parallel test execution.
Extracted from file_cleanup.py for file-size health.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)


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
