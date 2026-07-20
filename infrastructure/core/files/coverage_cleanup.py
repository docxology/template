"""Coverage file cleanup utilities.

This module provides functions for cleaning coverage database files
that can become corrupted during parallel test execution.
Extracted from file_cleanup.py for file-size health.
"""

import os
from pathlib import Path

from infrastructure.core.files.serialization import relative_or_self
from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)

_TRACKED_COVERAGE_PROVENANCE = Path("docs/_generated/coverage_snapshot.json")


def clean_coverage_files(repo_root: Path, patterns: list[str] | None = None, scope_dir: Path | None = None) -> bool:
    """Clean coverage database files to prevent corruption.

    Removes coverage database files that can become corrupted during parallel
    test execution or when tests are interrupted.

    Args:
        repo_root: Repository root directory. Used to compute the relative
            labels reported to the caller, and as the search root when
            *scope_dir* is not given.
        patterns: List of file patterns to clean (default: coverage-related files)
        scope_dir: Restrict the search to this directory (and its
            descendants) instead of the whole repository — pass the specific
            project's root whenever the caller is about to run one project's
            tests. Without this, the default recursive repo-wide glob deletes
            OTHER concurrently-running projects' live coverage databases
            (observed in practice: a project's own passing test run reported
            "Total coverage: 0.00%" because a sibling project's pipeline
            invocation had just unlinked its mid-write ``.coverage.project``).
            The active ``COVERAGE_FILE`` and its parallel-worker shards are
            always preserved, even when they match a cleanup pattern.

    Returns:
        True if cleanup successful, False otherwise
    """
    if patterns is None:
        patterns = [
            "**/.coverage",  # Main coverage database (recursive)
            "**/.coverage.*",  # Lock files and temporary coverage files (recursive)
            "**/coverage_*.json",  # JSON coverage reports (recursive)
        ]

    search_root = scope_dir if scope_dir is not None else repo_root
    active_coverage = _active_coverage_file()
    protected_paths = {(repo_root / _TRACKED_COVERAGE_PROVENANCE).resolve()}

    logger.info("Cleaning coverage database files...")

    def _remove_file(file_path: Path, label: str) -> tuple[str | None, str | None]:
        """Attempt to remove a file; return (removed_label, locked_label)."""
        if active_coverage is not None and _belongs_to_coverage_family(file_path, active_coverage):
            logger.debug(f"  Preserved active coverage data: {label}")
            return None, None
        if file_path.resolve() in protected_paths:
            logger.debug("  Preserved tracked coverage provenance: %s", label)
            return None, None
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
                for file_path in search_root.glob(glob_pattern):
                    label = relative_or_self(file_path, repo_root)
                    removed, locked = _remove_file(file_path, label)
                    if removed:
                        removed_files.append(removed)
                    if locked:
                        locked_files.append(locked)
            else:
                # Exact filename
                file_path = search_root / pattern
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


def _active_coverage_file() -> Path | None:
    """Resolve the enclosing coverage database selected by coverage.py."""

    value = os.environ.get("COVERAGE_FILE")
    if not value:
        return None
    path = Path(value).expanduser()
    return (path if path.is_absolute() else Path.cwd() / path).resolve()


def _belongs_to_coverage_family(candidate: Path, active: Path) -> bool:
    """Return whether *candidate* is the active database or an xdist shard."""

    resolved = candidate.resolve()
    return resolved.parent == active.parent and (
        resolved.name == active.name or resolved.name.startswith(f"{active.name}.")
    )
