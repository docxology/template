#!/usr/bin/env python3
"""CLI entry point for documentation link and reference audits.

Library functions live in ``link_extract``; this module re-exports them for
backward compatibility and provides ``main()`` / ``run_link_audit()``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.docs.accuracy import extract_headings
from infrastructure.validation.integrity.link_extract import (
    LinkCheckResult,
    _get_actual_project_names,
    _is_real_path_item,
    _resolve_template_path,
    _should_validate_path,
    _validate_import_path,
    check_file_reference,
    extract_code_blocks,
    extract_links,
    validate_directory_structures,
    validate_file_paths_in_code,
    validate_placeholder_consistency,
    validate_python_imports,
)

logger = get_logger(__name__)

__all__ = [
    "LinkCheckResult",
    "_get_actual_project_names",
    "_is_real_path_item",
    "_resolve_template_path",
    "_should_validate_path",
    "_validate_import_path",
    "check_file_reference",
    "extract_code_blocks",
    "extract_headings",
    "extract_links",
    "discover_markdown_files",
    "generate_comprehensive_report",
    "main",
    "run_link_audit",
    "validate_directory_structures",
    "validate_file_paths_in_code",
    "validate_placeholder_consistency",
    "validate_python_imports",
]


def run_link_audit(repo_root: Path) -> int:
    """Run the comprehensive link and reference audit for ``repo_root``."""
    from infrastructure.validation.integrity.link_audit_core import run_link_audit as _run_link_audit

    return _run_link_audit(repo_root)


def main() -> int:
    """Check all documentation links and references comprehensively."""
    repo_root = Path(__file__).resolve().parents[3]
    return run_link_audit(repo_root)


def generate_comprehensive_report(issues: dict[str, list[LinkCheckResult]], total_files: int) -> int:
    """Generate a comprehensive validation report."""
    total_issues = sum(len(issue_list) for issue_list in issues.values())

    logger.info("=" * 80)
    logger.info("COMPREHENSIVE FILEPATH AND REFERENCE AUDIT REPORT")
    logger.info("=" * 80)
    logger.info(f"Files scanned: {total_files}")
    logger.info(f"Total issues found: {total_issues}")

    categories = [
        (
            "broken_anchor_links",
            "Broken Anchor Links",
            "Anchor links that don't resolve to headings",
        ),
        (
            "broken_file_refs",
            "Broken File References",
            "File references that don't exist",
        ),
        (
            "code_block_paths",
            "Invalid Code Block Paths",
            "File paths in code blocks that don't exist",
        ),
        (
            "directory_structures",
            "Directory Structure Issues",
            "Directory trees that don't match filesystem",
        ),
        (
            "python_imports",
            "Invalid Python Imports",
            "Import statements that reference non-existent modules",
        ),
        (
            "placeholder_consistency",
            "Placeholder Inconsistencies",
            "Inconsistent use of {name} vs actual project names",
        ),
    ]

    has_issues = False
    for category_key, title, description in categories:
        issue_list = issues[category_key]
        if issue_list:
            has_issues = True
            logger.warning(f"🚨 {title} ({len(issue_list)} issues)")
            logger.warning(f"   {description}")

            for i, issue in enumerate(issue_list[:5]):
                logger.warning(f"   {i + 1}. {issue['file']}:{issue['line']}")
                logger.warning(f"      Target: {issue['target']}")
                logger.warning(f"      Issue: {issue['issue']}")
                if "text" in issue:
                    logger.warning(f"      Text: {issue['text']}")

            if len(issue_list) > 5:
                logger.warning(f"   ... and {len(issue_list) - 5} more issues in this category")
            logger.info("-" * 60)

    if not has_issues:
        logger.info("✅ ALL VALIDATIONS PASSED!")
        logger.info("No broken links, missing files, or reference issues found.")
        return 0

    logger.info("\n📋 SUMMARY BY CATEGORY:")
    for category_key, title, _ in categories:
        count = len(issues[category_key])
        if count > 0:
            logger.info(f"   • {title}: {count} issues")

    logger.info("\n🔧 Next steps: Run the audit script to generate detailed fix recommendations:")
    logger.info("   python scripts/audit_filepaths.py")

    return 1


if __name__ == "__main__":
    sys.exit(main())
