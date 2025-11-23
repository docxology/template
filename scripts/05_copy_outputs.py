#!/usr/bin/env python3
"""Output copying orchestrator script.

This thin orchestrator coordinates the output copying stage:
1. Cleans the top-level output/ directory
2. Copies final deliverables from project/output/
3. Validates all expected files were copied

Stage 5 of the pipeline orchestration - copies final deliverables to
the top-level output/ directory for easy access.

Final deliverables copied:
- Combined PDF manuscript
- All presentation slides (PDF format)
- All web outputs (HTML format)
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
    """Copy final deliverables to top-level output directory.
    
    Copies:
    - Combined PDF: project/output/pdf/project_combined.pdf → output/project_combined.pdf
    - Slides: project/output/slides/*.pdf → output/slides/
    - Web: project/output/web/*.html → output/web/
    
    Args:
        project_root: Path to repository root
        output_dir: Path to top-level output directory
        
    Returns:
        Dictionary with copy statistics
    """
    log_stage("Copying final deliverables...")
    
    project_output = project_root / "project" / "output"
    stats = {
        "combined_pdf": 0,
        "slides_copied": 0,
        "web_copied": 0,
        "errors": [],
    }
    
    # 1. Copy combined PDF
    combined_pdf_src = project_output / "pdf" / "project_combined.pdf"
    combined_pdf_dst = output_dir / "project_combined.pdf"
    
    if combined_pdf_src.exists():
        try:
            shutil.copy2(combined_pdf_src, combined_pdf_dst)
            file_size_mb = combined_pdf_src.stat().st_size / (1024 * 1024)
            log_success(f"Copied combined PDF ({file_size_mb:.2f} MB)", logger)
            stats["combined_pdf"] = 1
        except Exception as e:
            msg = f"Failed to copy combined PDF: {e}"
            logger.error(msg)
            stats["errors"].append(msg)
    else:
        msg = f"Combined PDF not found: {combined_pdf_src}"
        logger.warning(msg)
        stats["errors"].append(msg)
    
    # 2. Copy slides
    slides_src = project_output / "slides"
    slides_dst = output_dir / "slides"
    
    if slides_src.exists():
        try:
            slides_dst.mkdir(parents=True, exist_ok=True)
            
            slides = list(slides_src.glob("*.pdf"))
            for slide in slides:
                shutil.copy2(slide, slides_dst / slide.name)
                stats["slides_copied"] += 1
            
            if slides:
                log_success(f"Copied {len(slides)} slide(s)", logger)
            else:
                logger.warning("No slide PDFs found in slides directory")
        except Exception as e:
            msg = f"Failed to copy slides: {e}"
            logger.error(msg)
            stats["errors"].append(msg)
    else:
        logger.warning(f"Slides directory not found: {slides_src}")
    
    # 3. Copy web outputs
    web_src = project_output / "web"
    web_dst = output_dir / "web"
    
    if web_src.exists():
        try:
            web_dst.mkdir(parents=True, exist_ok=True)
            
            html_files = list(web_src.glob("*.html"))
            for html_file in html_files:
                shutil.copy2(html_file, web_dst / html_file.name)
                stats["web_copied"] += 1
            
            # Copy CSS and other assets if present
            for asset in web_src.glob("*.css"):
                shutil.copy2(asset, web_dst / asset.name)
            
            for asset in web_src.glob("*.js"):
                shutil.copy2(asset, web_dst / asset.name)
            
            if html_files:
                log_success(f"Copied {len(html_files)} web page(s)", logger)
            else:
                logger.warning("No HTML files found in web directory")
        except Exception as e:
            msg = f"Failed to copy web outputs: {e}"
            logger.error(msg)
            stats["errors"].append(msg)
    else:
        logger.warning(f"Web directory not found: {web_src}")
    
    return stats


def validate_copied_outputs(output_dir: Path) -> bool:
    """Validate all expected files were copied successfully.
    
    Args:
        output_dir: Path to top-level output directory
        
    Returns:
        True if validation successful, False if critical files missing
    """
    log_stage("Validating copied outputs...")
    
    validation_passed = True
    
    # Check combined PDF
    combined_pdf = output_dir / "project_combined.pdf"
    if combined_pdf.exists() and combined_pdf.stat().st_size > 0:
        size_mb = combined_pdf.stat().st_size / (1024 * 1024)
        log_success(f"Combined PDF valid ({size_mb:.2f} MB)", logger)
    else:
        logger.error("Combined PDF missing or empty")
        validation_passed = False
    
    # Check slides directory
    slides_dir = output_dir / "slides"
    if slides_dir.exists():
        slides = list(slides_dir.glob("*.pdf"))
        if slides:
            total_size_mb = sum(f.stat().st_size for f in slides) / (1024 * 1024)
            log_success(f"Slides directory valid ({len(slides)} PDFs, {total_size_mb:.2f} MB)", logger)
        else:
            logger.warning("Slides directory exists but is empty")
    else:
        logger.warning("Slides directory not created")
    
    # Check web directory
    web_dir = output_dir / "web"
    if web_dir.exists():
        html_files = list(web_dir.glob("*.html"))
        if html_files:
            total_size_kb = sum(f.stat().st_size for f in html_files) / 1024
            log_success(f"Web directory valid ({len(html_files)} HTML files, {total_size_kb:.1f} KB)", logger)
        else:
            logger.warning("Web directory exists but is empty")
    else:
        logger.warning("Web directory not created")
    
    return validation_passed


def validate_output_structure(output_dir: Path) -> dict:
    """Validate complete output directory structure.
    
    Checks:
    - Output directory exists
    - Combined PDF exists and is > 100KB (should be substantial)
    - Slides directory has PDFs (if present)
    - Web directory has HTML files (if present)
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
    
    # Check combined PDF
    combined_pdf = output_dir / "project_combined.pdf"
    if not combined_pdf.exists():
        result["valid"] = False
        result["missing_files"].append("project_combined.pdf")
    else:
        size_bytes = combined_pdf.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        # PDF should typically be > 100KB
        if size_bytes < 100 * 1024:
            result["suspicious_sizes"].append(
                f"Combined PDF is unusually small: {size_mb:.2f} MB"
            )
        
        result["directory_structure"]["combined_pdf"] = {
            "exists": True,
            "size_mb": round(size_mb, 2),
            "readable": combined_pdf.is_file()
        }
    
    # Check subdirectories
    for subdir_name in ["slides", "web"]:
        subdir = output_dir / subdir_name
        
        if subdir.exists():
            files = list(subdir.glob("*"))
            file_count = len([f for f in files if f.is_file()])
            
            result["directory_structure"][subdir_name] = {
                "exists": True,
                "files": file_count,
                "readable": subdir.is_dir()
            }
            
            if file_count == 0:
                result["suspicious_sizes"].append(
                    f"{subdir_name} directory is empty"
                )
        else:
            result["directory_structure"][subdir_name] = {
                "exists": False,
                "files": 0
            }
    
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
    logger.info(f"\nFiles copied:")
    logger.info(f"  • Combined PDF: {stats['combined_pdf']}")
    logger.info(f"  • Slides: {stats['slides_copied']}")
    logger.info(f"  • Web pages: {stats['web_copied']}")
    
    # Include structure validation if provided
    if structure_validation:
        logger.info(f"\nDirectory structure:")
        for item, info in structure_validation.get("directory_structure", {}).items():
            if info.get("exists"):
                if "size_mb" in info:
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
        if stats["combined_pdf"] > 0 and validation_passed:
            log_success("\n✅ Output copying complete - all deliverables ready!", logger)
            return 0
        else:
            logger.error("\n❌ Output copying incomplete - check warnings above")
            return 1
    
    except Exception as e:
        logger.error(f"Unexpected error during output copying: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

