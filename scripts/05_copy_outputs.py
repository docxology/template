#!/usr/bin/env python3
"""Output copying orchestrator script.

This thin orchestrator coordinates the output copying stage:
1. Cleans the top-level output/ directory
2. Recursively copies entire project/output/ to top-level output/
3. Copies combined PDF to root for convenient access
4. Validates all expected files were copied

Stage 5 of the pipeline orchestration - copies all project outputs to
the top-level output/ directory for easy access.

Complete project outputs copied:
- PDF manuscript (pdf/ directory + root copy of project_combined.pdf)
- Presentation slides (slides/ directory - all formats and metadata)
- Web outputs (web/ directory - all HTML files)
- Generated figures (figures/ directory - all images and PDFs)
- Data files (data/ directory - all CSV, NPZ files)
- Reports (reports/ directory - all markdown/analysis files)
- Simulations (simulations/ directory - all simulation outputs and checkpoints)
- LLM reviews (llm/ directory - LLM-generated manuscript reviews)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header

# Set up logger for this module
logger = get_logger(__name__)


def log_stage(message: str) -> None:
    """Log a stage start message."""
    logger.info(f"\n  {message}")


def clean_output_directory(output_dir: Path) -> bool:
    """Clean top-level output directory before copying.
    
    Args:
        output_dir: Path to top-level output directory
        
    Returns:
        True if cleanup successful, False otherwise
        
    Raises:
        No exceptions - fails gracefully with logging
    """
    log_stage("Cleaning output directory...")
    
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


def copy_final_deliverables(project_root: Path, output_dir: Path) -> dict:
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
    
    Also copies combined PDF to root for convenient access.
    
    Args:
        project_root: Path to repository root
        output_dir: Path to top-level output directory
        
    Returns:
        Dictionary with copy statistics
    """
    log_stage("Copying all project outputs...")
    
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
        "combined_pdf": 0,
        "total_files": 0,
        "errors": [],
    }
    
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
    
    # Count files in each subdirectory and copy combined PDF to root
    subdirs = {
        "pdf": "pdf_files",
        "web": "web_files",
        "slides": "slides_files",
        "figures": "figures_files",
        "data": "data_files",
        "reports": "reports_files",
        "simulations": "simulations_files",
        "llm": "llm_files",
    }
    
    for subdir_name, stats_key in subdirs.items():
        subdir = output_dir / subdir_name
        if subdir.exists():
            files = list(subdir.glob("**/*"))
            file_count = len([f for f in files if f.is_file()])
            stats[stats_key] = file_count
            stats["total_files"] += file_count
            logger.debug(f"  {subdir_name}/: {file_count} file(s)")
    
    # Copy combined PDF to root for convenient access
    combined_pdf_src = output_dir / "pdf" / "project_combined.pdf"
    combined_pdf_dst = output_dir / "project_combined.pdf"
    
    if combined_pdf_src.exists():
        try:
            shutil.copy2(combined_pdf_src, combined_pdf_dst)
            file_size_mb = combined_pdf_src.stat().st_size / (1024 * 1024)
            log_success(f"Copied combined PDF to root ({file_size_mb:.2f} MB)", logger)
            stats["combined_pdf"] = 1
        except Exception as e:
            msg = f"Failed to copy combined PDF to root: {e}"
            logger.warning(msg)
            stats["errors"].append(msg)
    else:
        logger.debug(f"Combined PDF not found at: {combined_pdf_src}")
    
    return stats


def validate_copied_outputs(output_dir: Path) -> bool:
    """Validate all project outputs were copied successfully.

    Checks:
    - Combined PDF exists at root (preferred) or in pdf/ directory (fallback)
    - All expected subdirectories exist (pdf, web, slides, figures, data, reports, simulations, llm)
    - Each directory contains files
    - All files are readable

    Provides clear error messages indicating where to find missing files and potential causes.

    Args:
        output_dir: Path to top-level output directory

    Returns:
        True if validation successful, False if critical files missing
    """
    log_stage("Validating copied outputs...")
    
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
    }
    
    # Directories that are optional or populated later in the pipeline
    optional_dirs = {"llm"}  # LLM stage runs after copy outputs
    
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


def validate_output_structure(output_dir: Path) -> dict:
    """Validate complete output directory structure.
    
    Checks:
    - Output directory exists
    - Combined PDF exists and is > 100KB (should be substantial)
    - All expected subdirectories exist (pdf, web, slides, figures, data, reports, simulations, llm)
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
    expected_dirs = ["pdf", "web", "slides", "figures", "data", "reports", "simulations", "llm"]
    # Directories that are optional or populated later in the pipeline
    optional_dirs = {"llm"}  # LLM stage runs after copy outputs
    
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


def generate_output_summary(output_dir: Path, stats: dict, structure_validation: dict = None) -> None:
    """Generate summary of output copying results.
    
    Args:
        output_dir: Path to output directory
        stats: Dictionary with copy statistics
        structure_validation: Optional validation results dict
    """
    logger.info("\n" + "="*60)
    logger.info("Output Copying Summary")
    logger.info("="*60)
    
    logger.info(f"\nOutput directory: {output_dir}")
    logger.info(f"\nFiles copied by directory:")
    logger.info(f"  • PDF files: {stats['pdf_files']}")
    logger.info(f"  • Web files: {stats['web_files']}")
    logger.info(f"  • Slides files: {stats['slides_files']}")
    logger.info(f"  • Figures: {stats['figures_files']}")
    logger.info(f"  • Data files: {stats['data_files']}")
    logger.info(f"  • Reports: {stats['reports_files']}")
    logger.info(f"  • Simulations: {stats['simulations_files']}")
    logger.info(f"  • LLM reviews: {stats['llm_files']}")
    logger.info(f"  • Combined PDF (root): {stats['combined_pdf']}")
    logger.info(f"\n  Total files copied: {stats['total_files']}")
    
    # Include structure validation if provided
    if structure_validation:
        logger.info(f"\nDirectory structure:")
        for item, info in structure_validation.get("directory_structure", {}).items():
            if info.get("exists"):
                if "size_mb" in info and "files" in info:
                    logger.info(f"  ✓ {item}: {info['files']} files, {info['size_mb']} MB")
                elif "size_mb" in info:
                    logger.info(f"  ✓ {item}: {info['size_mb']} MB")
                elif "files" in info:
                    logger.info(f"  ✓ {item}: {info['files']} files")
            else:
                logger.info(f"  ✗ {item}: Not found")
    
    if stats["errors"]:
        logger.info(f"\nWarnings/Errors ({len(stats['errors'])}):")
        for error in stats["errors"]:
            logger.warning(f"  • {error}")
    
    logger.info("")


def main() -> int:
    """Execute output copying orchestration.
    
    Returns:
        Exit code (0=success, 1=failure)
    """
    log_header("STAGE 05: Copy Outputs")
    
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "output"
    
    try:
        # Step 1: Clean output directory
        if not clean_output_directory(output_dir):
            logger.error("Failed to clean output directory")
            return 1
        
        # Step 2: Copy final deliverables
        stats = copy_final_deliverables(repo_root, output_dir)
        
        # Step 3: Validate copied files
        validation_passed = validate_copied_outputs(output_dir)
        
        # Step 3b: Validate directory structure
        structure_validation = validate_output_structure(output_dir)
        
        # Step 4: Generate summary
        generate_output_summary(output_dir, stats, structure_validation)
        
        # Determine success/failure
        if stats["total_files"] > 0 and validation_passed:
            log_success("\n✅ Output copying complete - all project outputs ready!", logger)
            return 0
        else:
            logger.error("\n❌ Output copying incomplete - check warnings above")
            return 1
    
    except Exception as e:
        logger.error(f"Unexpected error during output copying: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

