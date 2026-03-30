"""File and directory cleanup utilities.

This module provides functions for cleaning output directories.
Extracted from file_operations.py for file-size health.

Coverage file cleanup is in coverage_cleanup.py.

Sub-modules:
    cleanup_helpers -- selective-clean, log archival, content removal
    cleanup_root    -- root output directory cleanup
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.files.cleanup_helpers import archive_output_logs, clean_output_dir_contents
from infrastructure.core.files.cleanup_root import clean_root_output_directory
from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)

# Re-export so every existing ``from infrastructure.core.files.cleanup import X`` keeps working.
__all__ = [
    "clean_output_directories",
    "clean_output_directory",
    "clean_root_output_directory",
]


def clean_output_directory(output_dir: Path) -> None:
    """Clean top-level output directory before copying.

    Creates *output_dir* if missing; otherwise removes all children so the
    directory exists and is empty. Returns ``None`` on success (callers
    treat a return value as unused; failures raise).

    Args:
        output_dir: Path to top-level output directory

    Raises:
        FileOperationError: If the directory cannot be created or cleaned.
    """
    import shutil

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


def clean_output_directories(
    repo_root: Path, project_name: str = "project", subdirs: list[str] | None = None
) -> None:
    """Clean output directories for a fresh pipeline start.

    Removes all contents from both projects/{project_name}/output/ and output/{project_name}/
    directories, then recreates the expected subdirectory structure.

    Log files are archived to logs/archive/ before cleanup to preserve execution history.
    Also cleans root-level directories from output/ that should not exist.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")
        subdirs: List of subdirectories to recreate. If None, uses default list.
    """
    # Discover valid project names by scanning the projects/ directory directly.
    # Using Path scan instead of infrastructure.project.discovery avoids a
    # circular import: file_operations -> project.discovery -> core.logging_utils.
    projects_dir = repo_root / "projects"
    project_names: list[str] = (
        [d.name for d in projects_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if projects_dir.exists()
        else []
    )

    # Clean root-level directories from output/ before cleaning project-specific directories
    clean_root_output_directory(repo_root, project_names)

    if subdirs is None:
        subdirs = ["pdf", "figures", "data", "reports", "simulations", "slides", "web", "logs", "llm"]

    # Persistence files preserved across runs to support incremental processing.
    # Paths are relative to each output_dir so files inside subdirectories
    # (e.g. data/nanopublications.jsonl) are correctly matched.
    preserved_relative_paths: set[Path] = {
        Path("data") / "corpus.jsonl",
        Path("data") / "nanopublications.jsonl",
        Path("data") / "nanopublications.trig",
    }

    output_dirs = [
        repo_root / "projects" / project_name / "output",
        repo_root / "output" / project_name,
    ]

    for output_dir in output_dirs:
        relative_path = output_dir.relative_to(repo_root)

        if output_dir.exists():
            logger.info(f"  Cleaning {relative_path}/...")
            archive_output_logs(output_dir)
            clean_output_dir_contents(output_dir, preserved_relative_paths)
        else:
            logger.info(f"  Creating {relative_path}/...")

        for subdir in subdirs:
            (output_dir / subdir).mkdir(parents=True, exist_ok=True)

        log_success(f"Cleaned {relative_path}/ (recreated subdirectories)", logger)

    log_success(f"Output directories cleaned for project '{project_name}' - fresh start", logger)
