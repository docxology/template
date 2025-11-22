#!/usr/bin/env python3
"""PDF rendering orchestrator script.

This thin orchestrator coordinates the PDF rendering stage:
1. Calls repo_utilities/render_pdf.sh
2. Monitors rendering process
3. Validates PDF generation
4. Reports rendering results

Stage 4 of the pipeline orchestration.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Add infrastructure to path for logging
sys.path.insert(0, str(Path(__file__).parent.parent / "infrastructure"))

from logging_utils import get_logger, log_success, log_error, log_header

# Set up logger for this module
logger = get_logger(__name__)


def find_render_script() -> Path | None:
    """Find the render_pdf.sh script."""
    repo_root = Path(__file__).parent.parent
    render_script = repo_root / "repo_utilities" / "render_pdf.sh"
    
    if render_script.exists():
        log_success(f"Found render script: {render_script.name}", logger)
        return render_script
    else:
        logger.error(f"Render script not found: {render_script}")
        return None


def run_render_pipeline(render_script: Path) -> int:
    """Execute the PDF rendering pipeline."""
    logger.info("Executing PDF rendering pipeline...")
    
    repo_root = Path(__file__).parent.parent
    
    logger.info(f"Running: {render_script.name}")
    
    try:
        result = subprocess.run(
            [str(render_script)],
            cwd=str(repo_root),
            check=False
        )
        
        if result.returncode == 0:
            log_success("PDF rendering completed successfully", logger)
        else:
            logger.error(f"PDF rendering failed (exit code: {result.returncode})")
        
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to execute render pipeline: {e}", exc_info=True)
        return 1


def verify_pdf_outputs() -> bool:
    """Verify that PDFs were generated."""
    logger.info("Verifying PDF outputs...")
    
    repo_root = Path(__file__).parent.parent
    pdf_dir = repo_root / "project" / "output" / "pdf"
    
    if not pdf_dir.exists():
        logger.error("PDF output directory not found")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if pdf_files:
        log_success(f"Generated {len(pdf_files)} PDF file(s)", logger)
        for pdf_file in pdf_files:
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            logger.info(f"  • {pdf_file.name} ({size_mb:.2f} MB)")
        return True
    else:
        logger.error("No PDF files found in output directory")
        return False


def main() -> int:
    """Execute PDF rendering orchestration."""
    log_header("STAGE 03: Render PDF", logger)
    
    # Find render script
    render_script = find_render_script()
    if not render_script:
        logger.error("Cannot proceed - render script not found")
        return 1
    
    # Run rendering pipeline
    exit_code = run_render_pipeline(render_script)
    
    if exit_code == 0:
        # Verify outputs
        outputs_valid = verify_pdf_outputs()
        
        if outputs_valid:
            log_success("PDF rendering complete - ready for validation", logger)
        else:
            logger.warning("PDF rendering completed but output verification failed")
    else:
        logger.error("PDF rendering failed - check logs for details")
    
    return exit_code


if __name__ == "__main__":
    exit(main())

