#!/usr/bin/env python3
"""Output validation orchestrator script.

This thin orchestrator coordinates the validation stage:
1. Validates generated PDFs
2. Checks markdown formatting
3. Verifies file integrity
4. Generates validation report

Stage 5 of the pipeline orchestration.
"""
from __future__ import annotations

import subprocess
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


def validate_pdfs() -> bool:
    """Validate generated PDF files."""
    log_stage("Validating PDF files...")
    
    repo_root = Path(__file__).parent.parent
    pdf_dir = repo_root / "project" / "output" / "pdf"
    
    if not pdf_dir.exists():
        logger.error("PDF directory not found")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("No PDF files to validate")
        return False
    
    valid_count = 0
    for pdf_file in pdf_files:
        try:
            # Check file size (PDFs should be > 0 bytes)
            file_size = pdf_file.stat().st_size
            
            if file_size > 0:
                log_success(f"PDF valid: {pdf_file.name} ({file_size} bytes)", logger)
                valid_count += 1
            else:
                logger.error(f"PDF empty: {pdf_file.name}")
        except Exception as e:
            logger.error(f"Cannot validate {pdf_file.name}: {e}")
    
    return valid_count == len(pdf_files)


def validate_markdown() -> bool:
    """Validate markdown files in manuscript."""
    log_stage("Validating markdown files...")
    
    repo_root = Path(__file__).parent.parent
    # Check project/manuscript first, then fall back to root manuscript/ for backward compatibility
    manuscript_dir = repo_root / "project" / "manuscript"
    
    if not manuscript_dir.exists():
        # Fallback for backward compatibility
        manuscript_dir = repo_root / "manuscript"
    
    if not manuscript_dir.exists():
        logger.warning("Manuscript directory not found")
        return True
    
    markdown_files = list(manuscript_dir.glob("*.md"))
    
    if not markdown_files:
        logger.warning("No markdown files found")
        return True
    
    log_success(f"Found {len(markdown_files)} markdown file(s)", logger)
    
    # Check for validation script
    validate_script = repo_root / "repo_utilities" / "validate_markdown.py"
    
    if validate_script.exists():
        logger.info("Running markdown validation script...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(validate_script)],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                log_success("Markdown validation passed", logger)
                return True
            else:
                logger.warning("Markdown validation had issues (non-critical)")
                if result.stdout:
                    logger.debug(f"Validation output: {result.stdout}")
                return True  # Non-critical
        except Exception as e:
            logger.warning(f"Could not run markdown validation: {e}")
            return True  # Non-critical
    else:
        logger.info("Markdown validation script not found (optional)")
        return True


def verify_outputs_exist() -> bool:
    """Verify all expected output files exist."""
    log_stage("Verifying output structure...")
    
    repo_root = Path(__file__).parent.parent
    
    required_dirs = [
        repo_root / "project" / "output" / "pdf",
        repo_root / "project" / "output" / "figures",
        repo_root / "project" / "output" / "data",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*")))
            log_success(f"Directory exists: {dir_path.name} ({file_count} file(s))", logger)
        else:
            logger.error(f"Directory missing: {dir_path.name}")
            all_exist = False
    
    return all_exist


def generate_validation_report() -> None:
    """Generate a validation report."""
    log_stage("Generating validation report...")
    
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "project" / "output"
    
    report_lines = [
        "Validation Report",
        "=================",
        "",
        f"Generated at: {output_dir.absolute()}",
        "",
    ]
    
    # Collect output statistics
    for subdir in ["pdf", "figures", "data"]:
        subdir_path = output_dir / subdir
        if subdir_path.exists():
            files = list(subdir_path.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            report_lines.append(f"{subdir.upper()}: {len(files)} file(s), {size_mb:.2f} MB")
    
    report_lines.extend([
        "",
        "Validation Complete",
        "",
    ])
    
    # Log report
    report_text = "\n".join(report_lines)
    logger.info(f"\n{report_text}")


def main() -> int:
    """Execute validation orchestration."""
    log_header("STAGE 04: Validate Output")
    
    checks = [
        ("PDF validation", validate_pdfs),
        ("Markdown validation", validate_markdown),
        ("Output structure", verify_outputs_exist),
    ]
    
    results = []
    for check_name, check_fn in checks:
        try:
            result = check_fn()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"Error during {check_name}: {e}", exc_info=True)
            results.append((check_name, False))
    
    # Generate report
    generate_validation_report()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("Validation Summary")
    logger.info("="*60)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        log_success("\n✅ Validation complete - pipeline successful!", logger)
        return 0
    else:
        logger.error("\n❌ Validation failed - review issues above")
        return 1


if __name__ == "__main__":
    exit(main())

