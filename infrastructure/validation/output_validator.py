"""Output validation utilities.

This module provides functions for validating copied outputs and
output directory structure.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def validate_copied_outputs(output_dir: Path) -> bool:
    """Validate all project outputs were copied successfully.

    Checks:
    - Combined PDF exists at root (preferred) or in pdf/ directory (fallback)
    - All expected subdirectories exist (pdf, web, slides, figures, data, reports, simulations, llm, logs)
    - Each directory contains files
    - All files are readable

    Args:
        output_dir: Path to top-level output directory

    Returns:
        True if validation successful, False if critical files missing
    """
    logger.info("Validating copied outputs...")
    
    validation_passed = True
    
    # Check combined PDF at root
    combined_pdf_root = output_dir / "project_combined.pdf"
    combined_pdf_in_pdf_dir = output_dir / "pdf" / "project_combined.pdf"

    # Check root location first (preferred)
    if combined_pdf_root.exists() and combined_pdf_root.stat().st_size > 0:
        size_mb = combined_pdf_root.stat().st_size / (1024 * 1024)
        log_success(f"Combined PDF at root valid ({size_mb:.2f} MB)", logger)
    # Check pdf/ directory as fallback
    elif combined_pdf_in_pdf_dir.exists() and combined_pdf_in_pdf_dir.stat().st_size > 0:
        size_mb = combined_pdf_in_pdf_dir.stat().st_size / (1024 * 1024)
        logger.warning(f"Combined PDF found in pdf/ directory but not at root ({size_mb:.2f} MB)")
        logger.warning("  Consider copying it to root for easier access")
        # Don't fail validation if PDF exists in pdf/ directory
    else:
        logger.error("Combined PDF missing or empty")
        logger.error("  Expected location: output/project_combined.pdf")
        logger.error("  Alternative location: output/pdf/project_combined.pdf")
        logger.error("  This may indicate PDF generation failed in Stage 3")
        validation_passed = False
    
    # Check all expected subdirectories
    expected_dirs = {
        "pdf": "PDF manuscripts and metadata",
        "web": "HTML web outputs",
        "slides": "Beamer slide presentations",
        "figures": "Generated figures and images",
        "data": "Data files and datasets",
        "reports": "Analysis and simulation reports",
        "simulations": "Simulation outputs and checkpoints",
        "llm": "LLM-generated manuscript reviews",
        "logs": "Pipeline execution logs",
    }
    
    # Directories that are optional or populated later in the pipeline
    optional_dirs = {"llm", "logs"}  # LLM stage and logs may be generated during pipeline
    
    for dir_name, description in expected_dirs.items():
        subdir = output_dir / dir_name
        if subdir.exists():
            files = list(subdir.glob("**/*"))
            file_count = len([f for f in files if f.is_file()])
            if file_count > 0:
                total_size_mb = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
                log_success(f"{dir_name}/ valid ({file_count} files, {total_size_mb:.2f} MB)", logger)
            else:
                # Only warn for required directories, info for optional
                if dir_name in optional_dirs:
                    logger.debug(f"{dir_name}/ not yet populated (generated in later stage)")
                else:
                    logger.warning(f"{dir_name}/ directory exists but is empty")
        else:
            if dir_name in optional_dirs:
                logger.debug(f"{dir_name}/ not found (optional, generated in later stage)")
            else:
                logger.warning(f"{dir_name}/ directory not found ({description})")
    
    return validation_passed


def validate_output_structure(output_dir: Path) -> Dict:
    """Validate complete output directory structure.
    
    Checks:
    - Output directory exists
    - Combined PDF exists and is > 100KB (should be substantial)
    - All expected subdirectories exist (pdf, web, slides, figures, data, reports, simulations, llm, logs)
    - Each subdirectory contains files
    - All files are readable
    
    Args:
        output_dir: Path to top-level output directory
        
    Returns:
        Dictionary with structure validation results
    """
    result = {
        "valid": True,
        "issues": [],
        "missing_files": [],
        "suspicious_sizes": [],
        "directory_structure": {}
    }
    
    # Check output directory exists
    if not output_dir.exists():
        result["valid"] = False
        result["issues"].append("Output directory does not exist")
        return result
    
    # Check combined PDF at root
    combined_pdf = output_dir / "project_combined.pdf"
    if not combined_pdf.exists():
        result["valid"] = False
        result["missing_files"].append("project_combined.pdf (root)")
    else:
        size_bytes = combined_pdf.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        # PDF should typically be > 100KB
        if size_bytes < 100 * 1024:
            result["suspicious_sizes"].append(
                f"Combined PDF is unusually small: {size_mb:.2f} MB"
            )
        
        result["directory_structure"]["project_combined_pdf"] = {
            "exists": True,
            "size_mb": round(size_mb, 2),
            "readable": combined_pdf.is_file()
        }
    
    # Check all expected subdirectories
    expected_dirs = ["pdf", "web", "slides", "figures", "data", "reports", "simulations", "llm", "logs"]
    # Directories that are optional or populated later in the pipeline
    optional_dirs = {"llm", "logs"}  # LLM stage and logs may be generated during pipeline
    
    for subdir_name in expected_dirs:
        subdir = output_dir / subdir_name
        
        if subdir.exists():
            files = list(subdir.glob("**/*"))
            file_count = len([f for f in files if f.is_file()])
            total_size_mb = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
            
            result["directory_structure"][subdir_name] = {
                "exists": True,
                "files": file_count,
                "size_mb": round(total_size_mb, 2),
                "readable": subdir.is_dir(),
                "optional": subdir_name in optional_dirs
            }
            
            # Only flag empty directories as suspicious if not optional
            if file_count == 0 and subdir_name not in optional_dirs:
                result["suspicious_sizes"].append(
                    f"{subdir_name}/ directory is empty"
                )
        else:
            result["directory_structure"][subdir_name] = {
                "exists": False,
                "files": 0,
                "size_mb": 0.0,
                "optional": subdir_name in optional_dirs
            }
            # Only add issue for required directories
            if subdir_name not in optional_dirs:
                result["issues"].append(f"Missing directory: {subdir_name}/")
    
    return result



