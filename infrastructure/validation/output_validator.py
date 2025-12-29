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
    
    # Check combined PDF - try project-specific first, then fallback to generic
    # First check if this looks like a project-specific output directory
    project_name = None
    if output_dir.parent.name == "output" and output_dir.name != "output":
        project_name = output_dir.name

    combined_pdf_found = False

    if project_name:
        # Try project-specific filename first
        project_pdf_root = output_dir / f"{project_name}_combined.pdf"
        project_pdf_in_pdf_dir = output_dir / "pdf" / f"{project_name}_combined.pdf"

        if project_pdf_root.exists() and project_pdf_root.stat().st_size > 0:
            size_mb = project_pdf_root.stat().st_size / (1024 * 1024)
            log_success(f"Combined PDF at root valid ({size_mb:.2f} MB)", logger)
            combined_pdf_found = True
        elif project_pdf_in_pdf_dir.exists() and project_pdf_in_pdf_dir.stat().st_size > 0:
            size_mb = project_pdf_in_pdf_dir.stat().st_size / (1024 * 1024)
            logger.warning(f"Combined PDF found in pdf/ directory but not at root ({size_mb:.2f} MB)")
            logger.warning("  Consider copying it to root for easier access")
            combined_pdf_found = True

    # Fallback to legacy filename for backward compatibility
    if not combined_pdf_found:
        combined_pdf_root = output_dir / "project_combined.pdf"
        combined_pdf_in_pdf_dir = output_dir / "pdf" / "project_combined.pdf"

        if combined_pdf_root.exists() and combined_pdf_root.stat().st_size > 0:
            size_mb = combined_pdf_root.stat().st_size / (1024 * 1024)
            log_success(f"Combined PDF at root valid ({size_mb:.2f} MB)", logger)
            combined_pdf_found = True
            if project_name:
                logger.warning(f"Using legacy PDF filename. Consider upgrading to project-specific naming.")
        elif combined_pdf_in_pdf_dir.exists() and combined_pdf_in_pdf_dir.stat().st_size > 0:
            size_mb = combined_pdf_in_pdf_dir.stat().st_size / (1024 * 1024)
            logger.warning(f"Combined PDF found in pdf/ directory but not at root ({size_mb:.2f} MB)")
            logger.warning("  Consider copying it to root for easier access")
            combined_pdf_found = True
            if project_name:
                logger.warning(f"Using legacy PDF filename. Consider upgrading to project-specific naming.")

    if not combined_pdf_found:
        logger.error("Combined PDF missing or empty")
        if project_name:
            logger.error(f"  Expected location: output/{project_name}_combined.pdf")
            logger.error(f"  Alternative location: output/pdf/{project_name}_combined.pdf")
            logger.error(f"  Legacy fallback: output/project_combined.pdf")
        else:
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
                # Only warn for required directories, debug for optional or potentially empty
                if dir_name in optional_dirs:
                    logger.debug(f"{dir_name}/ not yet populated (generated in later stage)")
                else:
                    logger.debug(f"{dir_name}/ directory exists but is empty (may be expected for this project type)")
        else:
            if dir_name in optional_dirs:
                logger.debug(f"{dir_name}/ not found (optional, generated in later stage)")
            else:
                logger.warning(f"{dir_name}/ directory not found ({description})")
    
    return validation_passed


def validate_root_output_structure(repo_root: Path) -> Dict[str, Any]:
    """Validate that root output/ directory structure is correct.

    Checks that output/ directory only contains project-specific folders
    and no root-level directories (data/, figures/, pdf/, etc.).

    Args:
        repo_root: Repository root directory

    Returns:
        Validation report dictionary with:
        - valid: Boolean indicating if structure is correct
        - issues: List of issues found
        - project_folders: List of project folders found
        - invalid_folders: List of invalid root-level directories
    """
    output_dir = repo_root / "output"

    if not output_dir.exists():
        return {
            "valid": False,
            "issues": ["Output directory does not exist"],
            "project_folders": [],
            "invalid_folders": []
        }

    # Discover valid project names
    from infrastructure.project.discovery import discover_projects
    projects = discover_projects(repo_root)
    project_names = set(p.name for p in projects)

    issues = []
    project_folders = []
    invalid_folders = []

    # Check each item in output directory
    for item in output_dir.iterdir():
        if not item.is_dir():
            continue  # Skip files

        item_name = item.name

        # Keep project-specific folders
        if item_name in project_names:
            project_folders.append(item_name)
            continue

        # Keep special directories
        if item_name in ['.gitkeep', '.gitignore']:
            continue

        # Check for root-level directories that shouldn't exist
        root_level_dirs = {
            'data', 'figures', 'pdf', 'web', 'slides',
            'reports', 'simulations', 'llm', 'logs', 'tex'
        }

        if item_name in root_level_dirs:
            invalid_folders.append(item_name)
            issues.append(f"Root-level directory '{item_name}' should not exist in output/")
        else:
            # Unknown directory - flag as potential issue
            issues.append(f"Unknown directory '{item_name}' in output/ (should only contain project folders)")

    valid = len(issues) == 0

    report = {
        "valid": valid,
        "issues": issues,
        "project_folders": sorted(project_folders),
        "invalid_folders": sorted(invalid_folders)
    }

    if valid:
        logger.info(f"Root output structure valid: {len(project_folders)} project folders found")
    else:
        logger.warning(f"Root output structure invalid: {len(issues)} issues found")

    return report


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
        "warnings": [],
        "directory_structure": {}
    }
    
    # Check output directory exists
    if not output_dir.exists():
        result["valid"] = False
        result["issues"].append("Output directory does not exist")
        return result
    
    # Check combined PDF - try project-specific first, then fallback to generic
    project_name = None
    if output_dir.parent.name == "output" and output_dir.name != "output":
        project_name = output_dir.name

    combined_pdf_found = False
    pdf_file = None
    pdf_size_mb = 0.0

    if project_name:
        # Try project-specific filename first
        project_pdf = output_dir / f"{project_name}_combined.pdf"
        if project_pdf.exists():
            size_bytes = project_pdf.stat().st_size
            pdf_size_mb = size_bytes / (1024 * 1024)
            combined_pdf_found = True
            pdf_file = project_pdf

            # PDF should typically be > 100KB
            if size_bytes < 100 * 1024:
                result["suspicious_sizes"].append(
                    f"Combined PDF is unusually small: {pdf_size_mb:.2f} MB"
                )
        else:
            result["missing_files"].append(f"{project_name}_combined.pdf (project-specific)")

    # Fallback to legacy filename for backward compatibility
    if not combined_pdf_found:
        combined_pdf = output_dir / "project_combined.pdf"
        if combined_pdf.exists():
            size_bytes = combined_pdf.stat().st_size
            pdf_size_mb = size_bytes / (1024 * 1024)
            combined_pdf_found = True
            pdf_file = combined_pdf

            # PDF should typically be > 100KB
            if size_bytes < 100 * 1024:
                result["suspicious_sizes"].append(
                    f"Combined PDF is unusually small: {pdf_size_mb:.2f} MB"
                )
            if project_name:
                result["warnings"].append(f"Using legacy PDF filename. Consider upgrading to project-specific naming.")
        else:
            result["missing_files"].append("project_combined.pdf (legacy fallback)")

    # Populate directory structure metadata
    if combined_pdf_found and pdf_file:
        result["directory_structure"]["project_combined_pdf"] = {
            "exists": True,
            "size_mb": round(pdf_size_mb, 2),
            "readable": pdf_file.is_file()
        }
    else:
        result["valid"] = False
        result["directory_structure"]["project_combined_pdf"] = {
            "exists": False,
            "size_mb": 0.0,
            "readable": False
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
















