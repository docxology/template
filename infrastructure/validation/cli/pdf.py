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
from typing import Any

from infrastructure.core.exceptions import PDFValidationError
from infrastructure.core.logging.constants import PIPELINE_STAGE_WIDTH
from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.content.pdf_validator import validate_pdf_rendering

logger = get_logger(__name__)


def _repo_root_from_cwd() -> Path:
    """Return repository root (directory containing pyproject.toml), else cwd."""
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return Path.cwd()


def discover_combined_pdf(repo_root: Path, project_name: str | None = None) -> Path | None:
    """Locate a combined manuscript PDF under ``output/{project}/pdf/``."""
    if project_name:
        candidate = repo_root / "output" / project_name / "pdf" / f"{project_name}_combined.pdf"
        return candidate if candidate.exists() else None

    candidates = sorted((repo_root / "output").glob("*/pdf/*_combined.pdf"))
    return candidates[0] if candidates else None


def print_validation_report(report: dict[str, Any], verbose: bool = False) -> None:
    """
    Print validation report to stdout in human-readable format.

    Args:
        report: Validation report from src/pdf_validator
        verbose: If True, print full details
    """
    logger.info("\n" + "=" * PIPELINE_STAGE_WIDTH)
    logger.info("📋 PDF VALIDATION REPORT")
    logger.info("=" * PIPELINE_STAGE_WIDTH)

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

    logger.info("=" * PIPELINE_STAGE_WIDTH)
    logger.info("")


def main(
    pdf_path: Path | None = None,
    n_words: int = 200,
    verbose: bool = False,
    project_name: str | None = None,
) -> int:
    """
    Main validation orchestration.

    Args:
        pdf_path: Path to PDF file (defaults to ``output/{project}/pdf/{project}_combined.pdf``)
        n_words: Number of words to extract for preview
        verbose: Enable verbose output
        project_name: Project slug when resolving the default combined PDF path

    Returns:
        Exit code: 0 for success, 1 for issues found, 2 for errors
    """
    if pdf_path is None:
        repo_root = _repo_root_from_cwd()
        pdf_path = discover_combined_pdf(repo_root, project_name=project_name)
        if pdf_path is None:
            hint = (
                f"output/{project_name}/pdf/{project_name}_combined.pdf"
                if project_name
                else "output/{project}/pdf/{project}_combined.pdf"
            )
            logger.error(
                "PDF file not found. Pass a path or use --project to resolve %s",
                hint,
            )
            return 2

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
    except Exception as e:  # noqa: BLE001
        logger.error(f"Unexpected Error: {e}", exc_info=verbose)
        return 2


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate PDF rendering quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate exemplar combined PDF
  python -m infrastructure.validation.cli.pdf \\
    output/template_code_project/pdf/template_code_project_combined.pdf

  # Discover combined PDF for one project
  python -m infrastructure.validation.cli.pdf --project template_code_project

  # Show more words (default: 200)
  python -m infrastructure.validation.cli.pdf --project template_code_project --words 500

  # Verbose output
  python -m infrastructure.validation.cli.pdf --project template_code_project --verbose
        """,
    )

    parser.add_argument(
        "pdf_path",
        nargs="?",
        type=Path,
        help="Path to PDF file (default: output/{project}/pdf/{project}_combined.pdf)",
    )
    parser.add_argument(
        "--project",
        dest="project_name",
        help="Project name when resolving the default combined PDF path",
    )
    parser.add_argument(
        "-w",
        "--words",
        type=int,
        default=200,
        help="Number of words to extract for preview (default: 200)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    exit_code = main(
        pdf_path=args.pdf_path,
        n_words=args.words,
        verbose=args.verbose,
        project_name=args.project_name,
    )

    sys.exit(exit_code)
