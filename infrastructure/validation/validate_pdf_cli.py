#!/usr/bin/env python3
"""
PDF output validation script - THIN ORCHESTRATOR

This script validates rendered PDFs for quality issues:
- Unresolved references (??)
- Missing citations
- Warnings and errors
- Document structure verification

All business logic is in src/pdf_validator.py
This script handles only I/O and orchestration.
"""

import sys
from pathlib import Path
from typing import Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Add src to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

try:
    from infrastructure.validation.pdf_validator import (
        PDFValidationError, validate_pdf_rendering)
except ImportError as e:
    logger.error(f"Failed to import from infrastructure/validation/pdf_validator.py")
    logger.error(f"   {e}")
    logger.error(
        f"   Ensure infrastructure/validation/pdf_validator.py exists and is properly formatted"
    )
    sys.exit(1)


def print_validation_report(report: dict, verbose: bool = False) -> None:
    """
    Print validation report to stdout in human-readable format.

    Args:
        report: Validation report from src/pdf_validator
        verbose: If True, print full details
    """
    logger.info("\n" + "=" * 70)
    logger.info("📋 PDF VALIDATION REPORT")
    logger.info("=" * 70)

    pdf_name = Path(report["pdf_path"]).name
    logger.info(f"📄 File: {pdf_name}")
    logger.info("")

    # Issues summary
    issues = report["issues"]
    total = issues["total_issues"]

    if total == 0:
        logger.info("✅ No rendering issues detected!")
    else:
        logger.info(f"⚠️  Found {total} rendering issue(s):")
        if issues["unresolved_references"] > 0:
            logger.info(f"   • Unresolved references (??): {issues['unresolved_references']}")
        if issues["warnings"] > 0:
            logger.info(f"   • Warnings: {issues['warnings']}")
        if issues["errors"] > 0:
            logger.info(f"   • Errors: {issues['errors']}")
        if issues["missing_citations"] > 0:
            logger.info(f"   • Missing citations [?]: {issues['missing_citations']}")

    logger.info("")
    logger.info("-" * 70)
    logger.info(f"📖 First {report['summary']['word_count']} words of document:")
    logger.info("-" * 70)
    logger.info(report["first_words"])
    logger.info("-" * 70)

    if verbose:
        logger.info("\n📊 Full Report Details:")
        logger.info(f"   PDF Path: {report['pdf_path']}")
        logger.info(f"   Has Issues: {report['summary']['has_issues']}")
        logger.info(f"   Word Count: {report['summary']['word_count']}")

    logger.info("=" * 70)
    logger.info("")


def main(
    pdf_path: Optional[Path] = None, n_words: int = 200, verbose: bool = False
) -> int:
    """
    Main validation orchestration.

    Args:
        pdf_path: Path to PDF file (defaults to project_combined.pdf)
        n_words: Number of words to extract for preview
        verbose: Enable verbose output

    Returns:
        Exit code: 0 for success, 1 for issues found, 2 for errors
    """
    # Default to project combined PDF if not specified
    if pdf_path is None:
        pdf_path = repo_root / "output" / "pdf" / "project_combined.pdf"

    # Validate PDF exists
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return 2

    logger.info(f"Validating PDF: {pdf_path.name}")

    try:
        # Use src/pdf_validator methods for all business logic
        report = validate_pdf_rendering(pdf_path, n_words=n_words)

        # Print report (I/O orchestration)
        print_validation_report(report, verbose=verbose)

        # Return appropriate exit code
        if report["summary"]["has_issues"]:
            return 1  # Issues found
        else:
            return 0  # Success

    except PDFValidationError as e:
        logger.error(f"Validation Error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return 2


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate PDF rendering quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate default combined PDF
  python validate_pdf_output.py
  
  # Validate specific PDF
  python validate_pdf_output.py output/pdf/01_abstract.pdf
  
  # Show more words (default: 200)
  python validate_pdf_output.py --words 500
  
  # Verbose output
  python validate_pdf_output.py --verbose
        """,
    )

    parser.add_argument(
        "pdf_path",
        nargs="?",
        type=Path,
        help="Path to PDF file (default: output/pdf/project_combined.pdf)",
    )
    parser.add_argument(
        "-w",
        "--words",
        type=int,
        default=200,
        help="Number of words to extract for preview (default: 200)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    exit_code = main(pdf_path=args.pdf_path, n_words=args.words, verbose=args.verbose)

    sys.exit(exit_code)
