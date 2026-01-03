"""File and directory operation utilities.

This module provides functions for cleaning, copying, and managing
output directories and files.
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def clean_output_directory(output_dir: Path) -> bool:
    """Clean top-level output directory before copying.
    
    Args:
        output_dir: Path to top-level output directory
        
    Returns:
        True if cleanup successful, False otherwise
    """
    logger.info("Cleaning output directory...")
    
    if not output_dir.exists():
        logger.info(f"Output directory does not exist, creating: {output_dir}")
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            log_success(f"Created output directory", logger)
            return True
        except PermissionError as e:
            logger.error(f"Permission denied creating output directory {output_dir}: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error creating output directory {output_dir}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating output directory {output_dir}: {e}")
            return False
    
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
        return True
    except PermissionError as e:
        logger.error(f"Permission denied cleaning output directory {output_dir}: {e}")
        return False
    except OSError as e:
        logger.error(f"OS error cleaning output directory {output_dir}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error cleaning output directory {output_dir}: {e}")
        return False


def clean_output_directories(
    repo_root: Path,
    project_name: str = "project",
    subdirs: List[str] | None = None
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
    # Import project discovery to get list of valid project names
    from infrastructure.project.discovery import discover_projects

    # Discover all projects to know which folders to keep in output/
    projects = discover_projects(repo_root)
    project_names = [p.name for p in projects]

    # Clean root-level directories from output/ before cleaning project-specific directories
    clean_root_output_directory(repo_root, project_names)

    if subdirs is None:
        subdirs = ["pdf", "figures", "data", "reports", "simulations", "slides", "web", "logs", "llm"]

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
                            archive_path = archive_dir / f"{log_file.stem}_{timestamp}{log_file.suffix}"
                            shutil.copy2(log_file, archive_path)
                            archived_count += 1
                            logger.debug(f"  Archived log file: {log_file.name} → {archive_path.name}")
                        except Exception as e:
                            logger.warning(f"  Failed to archive log file {log_file.name}: {e}")
                    
                    if archived_count > 0:
                        logger.info(f"  Archived {archived_count} log file(s) to logs/archive/")
            
            # Remove all contents except .checkpoints directory (preserve for pipeline resume)
            for item in output_dir.iterdir():
                if item.is_dir():
                    # Preserve .checkpoints directory to maintain pipeline resume capability
                    if item.name != ".checkpoints":
                        shutil.rmtree(item)
                    else:
                        logger.debug(f"  Preserving {item.name}/ directory for checkpoint resume")
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
                    '.gitkeep',
                    '.gitignore',
                    'multi_project_summary',  # Multi-project summary reports
                    'executive_summary',       # Executive reporting outputs
                }
                if item_name in special_dirs:
                    kept_items.append(item_name)
                    continue

                # Remove root-level directories that shouldn't exist
                # These are directories that should only exist within project folders
                root_level_dirs = {
                    'data', 'figures', 'pdf', 'web', 'slides',
                    'reports', 'simulations', 'llm', 'logs', 'tex'
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

    except Exception as e:
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

    except Exception as e:
        logger.error(f"Failed to clean coverage database files: {e}", exc_info=True)
        return False


def copy_final_deliverables(
    project_root: Path,
    output_dir: Path,
    project_name: str = "project"
) -> Dict:
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
        Dictionary with copy statistics:
        {
            "pdf_files": int,
            "web_files": int,
            "slides_files": int,
            "figures_files": int,
            "data_files": int,
            "reports_files": int,
            "simulations_files": int,
            "llm_files": int,
            "logs_files": int,
            "combined_pdf": int,
            "total_files": int,
            "errors": List[str]
        }
    """
    logger.info(f"Copying all outputs for project '{project_name}'...")
    
    project_output = project_root / "projects" / project_name / "output"
    
    stats = {
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
    except Exception as e:
        msg = f"Failed to copy project output directory: {e}"
        logger.error(msg)
        stats["errors"].append(msg)
        return stats
    
    # Collect files in each subdirectory with full paths and sizes
    subdirs = {
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
    
    for subdir_name, stats_key in subdirs.items():
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
                    # Verify log files have content
                    for log_file in log_files:
                        try:
                            size = log_file.stat().st_size
                            if size == 0:
                                logger.warning(f"  Log file is empty: {log_file.name}")
                            else:
                                logger.debug(f"  Found log file: {log_file.name} ({size:,} bytes)")
                        except Exception as e:
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
                except Exception as e:
                    logger.warning(f"  Failed to get size for {file_path}: {e}")
            
            logger.info(f"  {subdir_name}/: {file_count} file(s)")
    
    # Copy combined PDF to root for convenient access
    # First try project-specific name, then fall back to legacy name
    combined_pdf_src = output_dir / "pdf" / f"{project_name}_combined.pdf"
    combined_pdf_dst = output_dir / f"{project_name}_combined.pdf"

    if combined_pdf_src.exists():
        # Use project-specific name
        pass
    else:
        # Fall back to legacy name
        combined_pdf_src = output_dir / "pdf" / "project_combined.pdf"
        combined_pdf_dst = output_dir / "project_combined.pdf"

    if combined_pdf_src.exists():
        try:
            shutil.copy2(combined_pdf_src, combined_pdf_dst)
            file_size = combined_pdf_src.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            log_success(f"Copied combined PDF to root ({file_size_mb:.2f} MB)", logger)
            stats["combined_pdf"] = 1

            # Add to files list
            files_list.append({
                "path": str(combined_pdf_dst.resolve()),
                "size": file_size,
                "category": "pdf",
            })
            logger.info(f"  Root PDF: {combined_pdf_dst} ({file_size:,} bytes)")
        except Exception as e:
            msg = f"Failed to copy combined PDF to root: {e}"
            logger.warning(msg)
            stats["errors"].append(msg)
    else:
        logger.debug(f"Combined PDF not found at: {combined_pdf_src}")
    
    return stats
