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

    def _remove_file(file_path: Path, label: str) -> tuple[str | None, str | None]:
        """Attempt to remove a file; return (removed_label, locked_label)."""
        try:
            file_path.unlink()
            logger.debug(f"  Removed: {label}")
            return label, None
        except PermissionError:
            logger.debug(f"  Skipped (locked): {label}")
            return None, label
        except OSError as e:
            logger.debug(f"  Failed to remove {label}: {e}")
            return None, None

    try:
        removed_files = []
        locked_files = []

        # Clean each pattern
        for pattern in patterns:
            if "*" in pattern:
                # Glob pattern - search for matching files recursively
                glob_pattern = f"**/{pattern}" if not pattern.startswith("**/") else pattern
                for file_path in repo_root.glob(glob_pattern):
                    label = str(file_path.relative_to(repo_root))
                    removed, locked = _remove_file(file_path, label)
                    if removed:
                        removed_files.append(removed)
                    if locked:
                        locked_files.append(locked)
            else:
                # Exact filename
                file_path = repo_root / pattern
                if file_path.exists():
                    removed, locked = _remove_file(file_path, file_path.name)
                    if removed:
                        removed_files.append(removed)
                    if locked:
                        locked_files.append(locked)

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
