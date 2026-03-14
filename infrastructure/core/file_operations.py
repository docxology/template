"""File copy and inventory operation utilities.

This module provides functions for copying and inventorying
output files. Cleanup functions live in file_cleanup.py.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)

# Output subdirectory name → stats dict key mapping (module-level constant).
_SUBDIR_STATS_KEYS: dict[str, str] = {
    "pdf": "pdf_files", "web": "web_files", "slides": "slides_files",
    "figures": "figures_files", "data": "data_files", "reports": "reports_files",
    "simulations": "simulations_files", "llm": "llm_files", "logs": "logs_files",
}


def _process_subdirectories(output_dir: Path, stats: dict[str, Any], files_list: list[dict[str, Any]]) -> None:
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
                    files_list.append({
                        "path": str(file_path.resolve()),
                        "size": file_size,
                        "category": subdir_name,
                    })
                    logger.debug(f"  Copied: {file_path.name} ({file_size:,} bytes)")
                except OSError as e:
                    logger.warning(f"  Failed to get size for {file_path}: {e}")

            logger.info(f"  {subdir_name}/: {file_count} file(s)")

def _copy_combined_pdf(output_dir: Path, project_basename: str, stats: dict[str, Any], files_list: list[dict[str, Any]]) -> None:
    """Copy combined PDF to root of output directory for convenient access."""
    combined_pdf_src = output_dir / "pdf" / f"{project_basename}_combined.pdf"
    combined_pdf_dst = output_dir / f"{project_basename}_combined.pdf"

    if not combined_pdf_src.exists():
        combined_pdf_src = output_dir / "pdf" / "project_combined.pdf"
        combined_pdf_dst = output_dir / "project_combined.pdf"

    if combined_pdf_src.exists():
        try:
            shutil.copy2(combined_pdf_src, combined_pdf_dst)
            file_size = combined_pdf_src.stat().st_size
            log_success(f"Copied combined PDF to root ({file_size / (1024 * 1024):.2f} MB)", logger)
            stats["combined_pdf"] = 1
            files_list.append({
                "path": str(combined_pdf_dst.resolve()),
                "size": file_size,
                "category": "pdf",
            })
            logger.info(f"  Root PDF: {combined_pdf_dst} ({file_size:,} bytes)")
        except (OSError, shutil.Error) as e:
            msg = f"Failed to copy combined PDF to root: {e}"
            logger.warning(msg)
            stats["errors"].append(msg)
    else:
        logger.debug(f"Combined PDF not found at: {combined_pdf_src}")


def copy_final_deliverables(
    project_root: Path, output_dir: Path, project_name: str = "project"
) -> dict[str, Any]:
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

    Returns:
        Dictionary with copy statistics including counts and any errors.
    """
    logger.info(f"Copying all outputs for project '{project_name}'...")

    project_output = project_root / "projects" / project_name / "output"

    stats: dict[str, Any] = {
        "pdf_files": 0, "web_files": 0, "slides_files": 0, "figures_files": 0,
        "data_files": 0, "reports_files": 0, "simulations_files": 0, "llm_files": 0,
        "logs_files": 0, "combined_pdf": 0, "total_files": 0, "errors": [],
    }

    files_list = []

    if not project_output.exists():
        msg = f"Project output directory not found: {project_output}"
        logger.warning(msg)
        stats["errors"].append(msg)
        return stats

    # Recursively copy entire project/output/ directory
    try:
        logger.debug(f"Recursively copying: {project_output} → {output_dir}")
        shutil.copytree(project_output, output_dir, dirs_exist_ok=True)
        log_success("Recursively copied project/output/ directory", logger)
    except (OSError, shutil.Error) as e:
        msg = f"Failed to copy project output directory: {e}"
        logger.error(msg)
        stats["errors"].append(msg)
        return stats

    # Process subdirectories for verifying contents and updating stats
    _process_subdirectories(output_dir, stats, files_list)

    # Copy combined PDF to root for convenient access
    _copy_combined_pdf(output_dir, Path(project_name).name, stats, files_list)

    return stats


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str | None:
    """Calculate hash of a file for integrity verification.

    Args:
        file_path: Path to file to hash
        algorithm: Hash algorithm to use

    Returns:
        Hash string or None if file is missing or calculation fails
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
