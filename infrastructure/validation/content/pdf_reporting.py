"""Human-readable PDF diagnostics for the canonical validation CLI."""

from pathlib import Path
from typing import Any

from infrastructure.core.logging.constants import PIPELINE_STAGE_WIDTH
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


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
