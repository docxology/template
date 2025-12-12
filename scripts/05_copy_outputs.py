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

import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header
from infrastructure.core.file_operations import (
    clean_output_directory,
    copy_final_deliverables,
)
from infrastructure.validation.output_validator import (
    validate_copied_outputs,
    validate_output_structure,
)
from infrastructure.reporting.output_reporter import (
    generate_output_summary,
)

# Set up logger for this module
logger = get_logger(__name__)


def log_stage(message: str) -> None:
    """Log a stage start message."""
    logger.info(f"\n  {message}")


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
        result = copy_final_deliverables(repo_root, output_dir)
        stats = result.get("stats", {})
        files_list = result.get("files", [])
        
        # Log file details
        if files_list:
            logger.info(f"\nCopied {len(files_list)} file(s) with full paths:")
            for file_info in files_list[:20]:  # Show first 20 files
                file_path = file_info.get("path", "")
                file_size = file_info.get("size", 0)
                category = file_info.get("category", "unknown")
                size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
                logger.info(f"  [{category}] {file_path} ({size_mb:.2f} MB)")
            if len(files_list) > 20:
                logger.info(f"  ... and {len(files_list) - 20} more file(s)")
        
        # Step 3: Validate copied files
        validation_passed = validate_copied_outputs(output_dir)
        
        # Step 3b: Validate directory structure
        structure_validation = validate_output_structure(output_dir)
        
        # Step 4: Generate summary
        generate_output_summary(output_dir, stats, structure_validation)
        
        # Determine success/failure
        if stats.get("total_files", 0) > 0 and validation_passed:
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

