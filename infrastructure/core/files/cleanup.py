"""File and directory cleanup utilities.

This module provides functions for cleaning output directories.
Extracted from file_operations.py for file-size health.

Coverage file cleanup is in coverage_cleanup.py.

Sub-modules:
    cleanup_helpers -- selective-clean, log archival, content removal
    cleanup_root    -- root output directory cleanup
"""

import json
from pathlib import Path

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.files.cleanup_helpers import (
    clean_output_dir_contents,
    remove_output_entry,
)
from infrastructure.core.files.cleanup_root import clean_root_output_directory
from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.core.project_paths import validate_project_name

logger = get_logger(__name__)

# Re-export so every existing ``from infrastructure.core.files.cleanup import X`` keeps working.
__all__ = [
    "clean_final_output_directory",
    "clean_output_directories",
    "clean_output_directory",
    "clean_root_output_directory",
]

_PUBLICATION_SIDECAR_NAMES = frozenset({"release_bundle", "swh_repo_url.txt", "upload_receipts.json"})


def _reject_symlink_directory(path: Path) -> None:
    """Refuse cleanup when the directory itself redirects outside its root."""
    if path.is_symlink():
        raise FileOperationError(f"Refusing to clean symlinked output directory: {path}")


def clean_output_directory(output_dir: Path, *, preserve_names: frozenset[str] = frozenset()) -> None:
    """Clean top-level output directory before copying.

    Creates *output_dir* if missing; otherwise removes all children so the
    directory exists and is empty. Returns ``None`` on success (callers
    treat a return value as unused; failures raise).

    Args:
        output_dir: Path to top-level output directory.
        preserve_names: Existing top-level entries to retain.

    Raises:
        FileOperationError: If the directory cannot be created or cleaned.
    """
    logger.info("Cleaning output directory...")
    _reject_symlink_directory(output_dir)

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
            if item.name in preserve_names:
                logger.debug(f"  Preserved entry: {item.name}")
                continue
            remove_output_entry(item)
            logger.debug(f"  Removed entry: {item.name}")

        log_success("Output directory cleaned", logger)
    except OSError as e:
        raise FileOperationError(f"Failed to clean output directory {output_dir}: {e}") from e


def clean_final_output_directory(output_dir: Path) -> None:
    """Clean copied outputs while retaining independently published sidecars."""
    clean_output_directory(output_dir, preserve_names=_PUBLICATION_SIDECAR_NAMES)


_OUTPUT_PRESERVE_MANIFEST_NAME = ".pipeline_preserve_output_dirs"


def _load_output_preserve_manifest(project_dir: Path) -> frozenset[str]:
    """Return top-level output/ subdirectory names a project wants preserved across cleans.

    Reads an opt-in, project-local manifest file (one directory name per
    line, ``#``-comments and blank lines ignored). Absent by default — a
    project must explicitly declare that part of its output/ is a committed
    golden-fixture snapshot consumed by its own test suite rather than
    disposable, regenerable pipeline output.
    """
    manifest_path = project_dir / _OUTPUT_PRESERVE_MANIFEST_NAME
    if not manifest_path.is_file():
        return frozenset()
    names = {
        line.strip()
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    return frozenset(names)


def clean_output_directories(
    repo_root: Path,
    project_name: str = "project",
    subdirs: list[str] | None = None,
) -> list[Path]:
    """Clean output directories for a fresh pipeline start.

    Removes all contents from both projects/{project_name}/output/ and output/{project_name}/
    directories, then recreates the expected subdirectory structure. Git-tracked
    files under either directory are never destroyed; each skipped path is
    recorded in ``output/reports/cleanup_report.json`` and returned.

    Also cleans root-level directories from output/ that should not exist.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")
        subdirs: List of subdirectories to recreate. If None, uses default list.

    Returns:
        Repo-relative paths of every git-tracked file skipped by the clean.

    Raises:
        FileOperationError: If git cannot be consulted inside a repository
            (fail-closed: nothing is deleted).
    """
    project_name = validate_project_name(project_name)

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

    project_dir = repo_root / "projects" / project_name
    preserved_subtree_names = _load_output_preserve_manifest(project_dir)

    output_dirs = [
        project_dir / "output",
        repo_root / "output" / project_name,
    ]
    skipped: list[Path] = []
    for output_dir in output_dirs:
        _reject_symlink_directory(output_dir)
        relative_path = output_dir.relative_to(repo_root)

        if output_dir.exists():
            logger.info(f"  Cleaning {relative_path}/...")
            skipped.extend(
                output_dir / rel
                for rel in clean_output_dir_contents(output_dir, preserved_relative_paths, preserved_subtree_names)
            )
        else:
            logger.info(f"  Creating {relative_path}/...")

        for subdir in subdirs:
            (output_dir / subdir).mkdir(parents=True, exist_ok=True)

        log_success(f"Cleaned {relative_path}/ (recreated subdirectories)", logger)
    _write_cleanup_report(repo_root, project_dir, skipped)
    log_success(f"Output directories cleaned for project '{project_name}' - fresh start", logger)
    return skipped


def _write_cleanup_report(repo_root: Path, project_dir: Path, skipped: list[Path]) -> None:
    """Persist the skipped-tracked-files report consumed by snapshots and CI.

    ``skipped`` holds absolute paths; the report records them repo-relative.
    """
    repo_relative = sorted(
        p.relative_to(repo_root).as_posix() if p.is_relative_to(repo_root) else p.as_posix() for p in skipped
    )
    report_dir = project_dir / "output" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "skipped_tracked_count": len(repo_relative),
        "skipped_tracked": repo_relative,
    }
    report_path = report_dir / "cleanup_report.json"
    try:
        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise FileOperationError(f"Failed to write cleanup report {report_path}: {exc}") from exc
