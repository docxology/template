"""File and directory operation utilities.

This module provides functions for cleaning, copying, and managing
output directories and files.
"""
from __future__ import annotations

import shutil
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
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
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
    except Exception as e:
        logger.error(f"Failed to clean output directory: {e}")
        return False


def clean_output_directories(repo_root: Path, subdirs: List[str] | None = None) -> None:
    """Clean output directories for a fresh pipeline start.
    
    Removes all contents from both project/output/ and output/ directories,
    then recreates the expected subdirectory structure.
    
    Args:
        repo_root: Repository root directory
        subdirs: List of subdirectories to recreate. If None, uses default list.
    """
    if subdirs is None:
        subdirs = ["pdf", "figures", "data", "reports", "simulations", "slides", "web", "logs"]
    
    output_dirs = [
        repo_root / "project" / "output",
        repo_root / "output",
    ]
    
    for output_dir in output_dirs:
        relative_path = output_dir.relative_to(repo_root)
        
        if output_dir.exists():
            logger.info(f"  Cleaning {relative_path}/...")
            # Remove all contents
            for item in output_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            logger.info(f"  Creating {relative_path}/...")
        
        # Recreate subdirectory structure
        for subdir in subdirs:
            (output_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        log_success(f"Cleaned {relative_path}/ (recreated subdirectories)", logger)
    
    log_success("Output directories cleaned - fresh start", logger)


def copy_final_deliverables(project_root: Path, output_dir: Path) -> Dict:
    """Copy all project outputs to top-level output directory.
    
    Recursively copies entire project/output/ directory structure, preserving:
    - pdf/ - Complete PDF directory with manuscript and metadata
    - web/ - HTML web outputs
    - slides/ - Beamer slides and metadata
    - figures/ - Generated figures and visualizations
    - data/ - Data files (CSV, NPZ, etc.)
    - reports/ - Generated analysis and simulation reports
    - simulations/ - Simulation outputs and checkpoints
    - llm/ - LLM-generated manuscript reviews
    - logs/ - Pipeline execution logs
    
    Also copies combined PDF to root for convenient access.
    
    Args:
        project_root: Path to repository root
        output_dir: Path to top-level output directory
        
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
    logger.info("Copying all project outputs...")
    
    project_output = project_root / "project" / "output"
    
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
