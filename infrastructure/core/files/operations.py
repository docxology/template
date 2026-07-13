"""File copy and inventory operation utilities.

This module provides functions for copying and inventorying
output files. Cleanup functions live in file_cleanup.py.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Literal, TypedDict

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.files.portability import sanitize_machine_local_paths
from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)


class CopyStats(TypedDict):
    """Typed structure for copy_final_deliverables return value."""

    pdf_files: int
    web_files: int
    slides_files: int
    figures_files: int
    data_files: int
    reports_files: int
    simulations_files: int
    llm_files: int
    logs_files: int
    combined_pdf: int
    total_files: int
    errors: list[str]


# Output subdirectory name → stats dict key mapping (module-level constant).
CopyStatsCountKey = Literal[
    "pdf_files",
    "web_files",
    "slides_files",
    "figures_files",
    "data_files",
    "reports_files",
    "simulations_files",
    "llm_files",
    "logs_files",
]

_SUBDIR_STATS_KEYS: dict[str, CopyStatsCountKey] = {
    "pdf": "pdf_files",
    "web": "web_files",
    "slides": "slides_files",
    "figures": "figures_files",
    "data": "data_files",
    "reports": "reports_files",
    "simulations": "simulations_files",
    "llm": "llm_files",
    "logs": "logs_files",
}


def _find_symlinks(root: Path) -> list[Path]:
    if root.is_symlink():
        return [root]
    if not root.exists():
        return []

    links: list[Path] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                if entry.is_symlink():
                    links.append(path)
                elif entry.is_dir(follow_symlinks=False):
                    pending.append(path)
    return sorted(links, key=lambda path: path.as_posix())


def _symlink_error(label: str, root: Path, links: list[Path]) -> str:
    displayed: list[str] = []
    for path in links:
        try:
            displayed.append(path.relative_to(root).as_posix())
        except ValueError:
            displayed.append(path.as_posix())
    return f"Refusing to publish {label} containing symlinks: {', '.join(displayed)}"


def _collect_subdirectory_stats(output_dir: Path, stats: CopyStats, files_list: list[dict[str, Any]]) -> None:
    """Process output subdirectories, verifying contents and updating stats."""
    for subdir_name, stats_key in _SUBDIR_STATS_KEYS.items():
        subdir = output_dir / subdir_name
        if subdir.exists():
            all_items = list(subdir.glob("**/*"))
            file_items = [f for f in all_items if f.is_file()]
            file_count = len(file_items)
            stats[stats_key] = file_count
            stats["total_files"] += file_count

            # Special validation for logs directory
            if subdir_name == "logs":
                log_files = [f for f in file_items if f.suffix == ".log"]
                if not log_files:
                    logger.warning(
                        f"  No log files found in {subdir_name}/ directory. "
                        "Log files should be created during pipeline execution."
                    )
                else:
                    for log_file in log_files:
                        try:
                            size = log_file.stat().st_size
                            if size == 0:
                                logger.warning(f"  Log file is empty: {log_file.name}")
                            else:
                                logger.debug(f"  Found log file: {log_file.name} ({size:,} bytes)")
                        except OSError as e:
                            logger.warning(f"  Failed to verify log file {log_file.name}: {e}")
                    logger.info(f"  Found {len(log_files)} log file(s) in {subdir_name}/")

            # Log each file with full path and size
            for file_path in file_items:
                try:
                    file_size = file_path.stat().st_size
                    files_list.append(
                        {
                            "path": str(file_path.resolve()),
                            "size": file_size,
                            "category": subdir_name,
                        }
                    )
                    logger.debug(f"  Copied: {file_path.name} ({file_size:,} bytes)")
                except OSError as e:
                    logger.warning(f"  Failed to get size for {file_path}: {e}")

            logger.info(f"  {subdir_name}/: {file_count} file(s)")


def _copy_combined_pdf(
    output_dir: Path, project_basename: str, stats: CopyStats, files_list: list[dict[str, Any]]
) -> None:
    """Copy combined PDF to root of output directory for convenient access."""
    combined_pdf_src = output_dir / "pdf" / f"{project_basename}_combined.pdf"
    combined_pdf_dst = output_dir / f"{project_basename}_combined.pdf"

    if not combined_pdf_src.exists():
        logger.debug(f"Combined PDF not found at: {combined_pdf_src}")
        return

    try:
        shutil.copy2(combined_pdf_src, combined_pdf_dst)
        file_size = combined_pdf_src.stat().st_size
        log_success(f"Copied combined PDF to root ({file_size / (1024 * 1024):.2f} MB)", logger)
        stats["combined_pdf"] = 1
        files_list.append(
            {
                "path": str(combined_pdf_dst.resolve()),
                "size": file_size,
                "category": "pdf",
            }
        )
        logger.info(f"  Root PDF: {combined_pdf_dst} ({file_size:,} bytes)")
    except (OSError, shutil.Error) as e:
        msg = f"Failed to copy combined PDF to root: {e}"
        logger.warning(msg)
        stats["errors"].append(msg)


def copy_final_deliverables(
    project_root: Path,
    output_dir: Path,
    project_name: str = "project",
    project_dir: Path | None = None,
) -> CopyStats:
    """Copy all project outputs to top-level output directory.

    Recursively copies entire projects/{project_name}/output/ directory structure, preserving:
    - pdf/ - Complete PDF directory with manuscript and metadata
    - web/ - HTML web outputs
    - slides/ - Beamer slides and metadata
    - figures/ - Generated figures and visualizations
    - data/ - Data files (CSV, NPZ, etc.)
    - reports/ - Generated analysis and simulation reports
    - simulations/ - Simulation outputs and checkpoints
    - llm/ - LLM-generated manuscript reviews
    - logs/ - Pipeline execution logs

    Also copies combined PDF to root of project output directory for convenient access.

    Args:
        project_root: Path to repository root
        output_dir: Path to top-level output directory (should be output/{project_name}/)
        project_name: Name of project in projects/ directory (default: "project")
        project_dir: Resolved project directory. When provided, this overrides
            ``project_root / "projects" / project_name`` so WIP projects under
            ``projects/working/`` can be copied without creating an
            output-only shadow under ``projects/``.

    Returns:
        Dictionary with copy statistics including counts and any errors.
    """
    logger.info(f"Copying all outputs for project '{project_name}'...")

    if project_dir is None:
        from infrastructure.core.project_paths import resolve_project_root

        project_dir = resolve_project_root(project_root, project_name)
    project_output = project_dir / "output"

    stats: CopyStats = {
        "pdf_files": 0,
        "web_files": 0,
        "slides_files": 0,
        "figures_files": 0,
        "data_files": 0,
        "reports_files": 0,
        "simulations_files": 0,
        "llm_files": 0,
        "logs_files": 0,
        "combined_pdf": 0,
        "total_files": 0,
        "errors": [],
    }

    files_list: list[dict[str, Any]] = []

    if not project_output.exists():
        msg = f"Project output directory not found: {project_output}"
        logger.warning(msg)
        stats["errors"].append(msg)
        return stats

    try:
        source_links = _find_symlinks(project_output)
        destination_links = _find_symlinks(output_dir)
    except OSError as exc:
        msg = f"Failed to verify publication output paths: {exc}"
        logger.error(msg)
        stats["errors"].append(msg)
        return stats
    if source_links:
        msg = _symlink_error("source", project_output, source_links)
        logger.error(msg)
        stats["errors"].append(msg)
        return stats
    if destination_links:
        msg = _symlink_error("destination", output_dir, destination_links)
        logger.error(msg)
        stats["errors"].append(msg)
        return stats

    sanitize_machine_local_paths(project_output)

    # Recursively copy entire project/output/ directory
    try:
        logger.debug(f"Recursively copying: {project_output} → {output_dir}")
        shutil.copytree(project_output, output_dir, dirs_exist_ok=True, symlinks=True)
        log_success("Recursively copied project/output/ directory", logger)
    except (OSError, shutil.Error) as e:
        msg = f"Failed to copy project output directory: {e}"
        logger.error(msg)
        stats["errors"].append(msg)
        return stats

    try:
        copied_links = _find_symlinks(output_dir)
    except OSError as exc:
        msg = f"Failed to verify copied publication outputs: {exc}"
        logger.error(msg)
        stats["errors"].append(msg)
        return stats
    if copied_links:
        for path in copied_links:
            try:
                path.unlink()
            except OSError as exc:
                logger.error(f"Failed to remove unsafe copied symlink {path}: {exc}")
        msg = _symlink_error("destination", output_dir, copied_links)
        logger.error(msg)
        stats["errors"].append(msg)
        return stats

    # Process subdirectories for verifying contents and updating stats
    _collect_subdirectory_stats(output_dir, stats, files_list)

    # Copy combined PDF to root for convenient access
    _copy_combined_pdf(output_dir, Path(project_name).name, stats, files_list)

    return stats


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str | None:
    """Calculate hash of a file for integrity verification.

    Args:
        file_path: Path to file to hash
        algorithm: Hash algorithm to use

    Returns:
        Hash string, or None if file does not exist or cannot be read

    Raises:
        FileOperationError: If the algorithm is unsupported
    """
    if not file_path.exists():
        return None

    try:
        hash_func = hashlib.new(algorithm)
    except ValueError as e:
        raise FileOperationError(f"Unsupported hash algorithm '{algorithm}': {e}") from e

    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except OSError as e:
        logger.debug(f"Could not hash {file_path}: {e}")
        return None
