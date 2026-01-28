#!/usr/bin/env python3
"""Audit orchestrator that coordinates all validation modules for filepath and reference auditing.

This module provides a unified interface for running audits across all validation modules,
categorizing issues, and generating structured reports.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.validation.check_links import (
    extract_headings, validate_directory_structures,
    validate_file_paths_in_code, validate_placeholder_consistency,
    validate_python_imports)
from infrastructure.validation.doc_accuracy import check_links
from infrastructure.validation.doc_discovery import (categorize_documentation,
                                                     find_markdown_files)
from infrastructure.validation.doc_models import (AccuracyIssue,
                                                  CompletenessGap,
                                                  DocumentationFile, LinkIssue,
                                                  QualityIssue, ScanResults)
from infrastructure.validation.issue_categorizer import (
    filter_false_positives, generate_issue_summary, get_severity_flag,
    is_false_positive, prioritize_issues)

logger = get_logger(__name__)


def run_comprehensive_audit(
    repo_root: Path,
    verbose: bool = False,
    include_code_validation: bool = True,
    include_directory_validation: bool = True,
    include_import_validation: bool = True,
    include_placeholder_validation: bool = True,
) -> ScanResults:
    """Run audit across all validation modules.

    Args:
        repo_root: Repository root directory
        verbose: Enable verbose logging
        include_code_validation: Include code block path validation
        include_directory_validation: Include directory structure validation
        include_import_validation: Include Python import validation
        include_placeholder_validation: Include placeholder consistency validation

    Returns:
        Complete scan results with all issues categorized
    """
    start_time = time.time()

    logger.info("🔍 Starting filepath and reference audit...")

    # Phase 1: Discovery
    md_files = find_markdown_files(repo_root)
    logger.info(f"📁 Found {len(md_files)} markdown files to audit")

    # Get project categorization
    doc_categories = categorize_documentation(md_files, repo_root)

    # Phase 2: Collect headings for anchor validation
    all_headings = {}
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(
                content
            )
        except Exception as e:
            if verbose:
                logger.warning(f"Error reading {md_file}: {e}")

    # Phase 3: Run all validations
    scan_results = ScanResults(scan_date=time.strftime("%Y-%m-%d %H:%M:%S"))

    # Process each file
    for i, md_file in enumerate(md_files):
        if verbose and (i + 1) % 10 == 0:
            logger.info(f"🔄 Processed {i + 1}/{len(md_files)} files...")

        try:
            content = md_file.read_text(encoding="utf-8")
            file_results = _validate_single_file(
                md_file,
                content,
                repo_root,
                all_headings,
                include_code_validation,
                include_directory_validation,
                include_import_validation,
                include_placeholder_validation,
            )

            # Add to scan results
            scan_results.link_issues.extend(file_results["link_issues"])
            scan_results.accuracy_issues.extend(file_results["accuracy_issues"])
            scan_results.quality_issues.extend(file_results["quality_issues"])

            # Create documentation file entry
            doc_file = DocumentationFile(
                path=str(md_file.relative_to(repo_root)),
                relative_path=str(md_file.relative_to(repo_root)),
                directory=str(md_file.parent.relative_to(repo_root)),
                name=md_file.name,
                category=doc_categories.get(str(md_file.relative_to(repo_root)), ""),
                word_count=len(content.split()),
                line_count=len(content.splitlines()),
                has_links="[" in content and "]" in content,
                has_code_blocks="```" in content,
            )
            scan_results.documentation_files.append(doc_file)

        except Exception as e:
            logger.error(f"Error processing {md_file}: {e}")
            scan_results.quality_issues.append(
                QualityIssue(
                    file=str(md_file.relative_to(repo_root)),
                    line=0,
                    issue_type="processing_error",
                    issue_message=f"Failed to process file: {e}",
                    severity="error",
                )
            )

    # Phase 4: Calculate statistics
    scan_results.scan_duration = time.time() - start_time
    _calculate_statistics(scan_results)

    logger.info(f"✅ Audit completed in {scan_results.scan_duration:.2f}s")
    logger.info(
        f"📊 Found {len(scan_results.link_issues) + len(scan_results.accuracy_issues) + len(scan_results.quality_issues)} total issues"
    )

    return scan_results


def _validate_single_file(
    md_file: Path,
    content: str,
    repo_root: Path,
    all_headings: Dict[str, set],
    include_code: bool,
    include_directory: bool,
    include_imports: bool,
    include_placeholders: bool,
) -> Dict[str, List]:
    """Validate a single markdown file using all available validation modules."""

    file_key = str(md_file.relative_to(repo_root))
    results = {"link_issues": [], "accuracy_issues": [], "quality_issues": []}

    # Link validation using doc_accuracy
    try:
        link_issues = check_links([md_file], repo_root, all_headings)
        for issue in link_issues:
            results["link_issues"].append(
                LinkIssue(
                    file=file_key,
                    target=issue.target,
                    line=issue.line,
                    link_text=issue.link_text,
                    issue_type=issue.issue_type,
                    issue_message=issue.issue_message,
                    severity=issue.severity,
                )
            )
    except Exception as e:
        logger.warning(f"Link validation failed for {md_file}: {e}")

    # Code block path validation
    if include_code:
        try:
            code_issues = validate_file_paths_in_code(content, md_file, repo_root)
            for issue in code_issues:
                results["quality_issues"].append(
                    QualityIssue(
                        file=file_key,
                        line=issue.get("line", 0),
                        issue_type="code_block_path",
                        issue_message=issue.get("issue", "Code block path issue"),
                        severity="warning",
                    )
                )
        except Exception as e:
            logger.warning(f"Code validation failed for {md_file}: {e}")

    # Directory structure validation
    if include_directory:
        try:
            dir_issues = validate_directory_structures(content, md_file, repo_root)
            for issue in dir_issues:
                results["quality_issues"].append(
                    QualityIssue(
                        file=file_key,
                        line=issue.get("line", 0),
                        issue_type="directory_structure",
                        issue_message=issue.get("issue", "Directory structure issue"),
                        severity="info",
                    )
                )
        except Exception as e:
            logger.warning(f"Directory validation failed for {md_file}: {e}")

    # Python import validation
    if include_imports:
        try:
            import_issues = validate_python_imports(content, md_file, repo_root)
            for issue in import_issues:
                results["quality_issues"].append(
                    QualityIssue(
                        file=file_key,
                        line=issue.get("line", 0),
                        issue_type="python_import",
                        issue_message=issue.get("issue", "Python import issue"),
                        severity="warning",
                    )
                )
        except Exception as e:
            logger.warning(f"Import validation failed for {md_file}: {e}")

    # Placeholder consistency validation
    if include_placeholders:
        try:
            placeholder_issues = validate_placeholder_consistency(
                content, md_file, repo_root
            )
            for issue in placeholder_issues:
                results["quality_issues"].append(
                    QualityIssue(
                        file=file_key,
                        line=issue.get("line", 0),
                        issue_type="placeholder_consistency",
                        issue_message=issue.get(
                            "issue", "Placeholder consistency issue"
                        ),
                        severity="info",
                    )
                )
        except Exception as e:
            logger.warning(f"Placeholder validation failed for {md_file}: {e}")

    return results


def _calculate_statistics(scan_results: ScanResults) -> None:
    """Calculate statistics for the scan results."""
    scan_results.scanned_files = len(scan_results.documentation_files)

    # Calculate statistics by issue type
    stats = {
        "link_issues": len(scan_results.link_issues),
        "accuracy_issues": len(scan_results.accuracy_issues),
        "completeness_gaps": len(scan_results.completeness_gaps),
        "quality_issues": len(scan_results.quality_issues),
    }

    scan_results.statistics = stats


def generate_audit_report(
    scan_results: ScanResults,
    output_format: str = "markdown",
    show_green_flags: bool = False,
) -> str:
    """Generate a formatted audit report with severity flag classification.

    Args:
        scan_results: Complete scan results
        output_format: Output format ('markdown' or 'json')
        show_green_flags: Whether to show green flags (known exceptions) in report

    Returns:
        Formatted report string
    """
    # Collect all issues
    all_issues = []
    all_issues.extend(scan_results.link_issues)
    all_issues.extend(scan_results.accuracy_issues)
    all_issues.extend(scan_results.quality_issues)
    all_issues.extend(scan_results.completeness_gaps)

    # Filter false positives and categorize by severity flag
    red_flags = []
    yellow_flags = []
    green_flags = []

    for issue in all_issues:
        flag = get_severity_flag(issue)
        if flag == "red":
            red_flags.append(issue)
        elif flag == "yellow":
            yellow_flags.append(issue)
        else:
            green_flags.append(issue)

    # Generate summary statistics
    summary = generate_issue_summary(all_issues)

    if output_format == "json":
        import json

        return json.dumps(
            {
                "scan_date": scan_results.scan_date,
                "total_files": scan_results.scanned_files,
                "scan_duration": scan_results.scan_duration,
                "statistics": scan_results.statistics,
                "severity_flags": {
                    "red": len(red_flags),
                    "yellow": len(yellow_flags),
                    "green": len(green_flags),
                },
                "summary": summary,
                "red_flags": [vars(issue) for issue in red_flags],
                "yellow_flags": [vars(issue) for issue in yellow_flags],
                "green_flags": (
                    [vars(issue) for issue in green_flags] if show_green_flags else []
                ),
            },
            indent=2,
            default=str,
        )

    # Default markdown format with severity flag organization
    report_lines = [
        "# 📊 Comprehensive Filepath and Reference Audit Report",
        "",
        f"**Generated:** {scan_results.scan_date}",
        f"**Files Scanned:** {scan_results.scanned_files}",
        f"**Scan Duration:** {scan_results.scan_duration:.2f} seconds",
        "",
        "## 📈 Executive Summary",
        "",
    ]

    total_issues = len(all_issues)
    if total_issues == 0:
        report_lines.extend(
            [
                "✅ **ALL VALIDATIONS PASSED!**",
                "",
                "No broken links, missing files, or reference issues were found in the documentation.",
                "",
            ]
        )
    else:
        # Show severity flag summary
        report_lines.extend(
            [
                f"**Total Issues Found:** {total_issues}",
                "",
                "### 🚩 Severity Flag Summary",
                "",
                f"🔴 **Red Flags (Critical):** {len(red_flags)} - Issues requiring immediate attention",
                f"🟡 **Yellow Flags (Warnings):** {len(yellow_flags)} - Issues that should be reviewed",
                f"🟢 **Green Flags (Exceptions):** {len(green_flags)} - Known exceptions and false positives",
                "",
                (
                    f"**False Positives Filtered:** {summary.get('false_positives', 0)} ({100 * summary.get('false_positives', 0) / total_issues:.1f}%)"
                    if total_issues > 0
                    else ""
                ),
                "",
            ]
        )

        if total_issues > 0:
            report_lines.append("")

        # Show category breakdown
        report_lines.extend(["### Issues by Category", ""])

        for category, count in scan_results.statistics.items():
            if count > 0:
                report_lines.append(
                    f"- **{category.replace('_', ' ').title()}:** {count} issues"
                )

        report_lines.append("")

    # Show red flags first (critical issues)
    if red_flags:
        prioritized_red = prioritize_issues(red_flags)
        report_lines.extend(
            [
                "## 🔴 Red Flags (Critical Issues)",
                "",
                f"**{len(red_flags)} critical issues** requiring immediate attention:",
                "",
            ]
        )
        for issue in prioritized_red[:20]:  # Show first 20 red flags
            issue_type = getattr(issue, "issue_type", "unknown")
            target = getattr(issue, "target", "N/A")
            report_lines.extend(
                [
                    f"**{issue.file}:{issue.line}**",
                    f"- **Type:** {issue_type}",
                    f"- **Target:** `{target}`" if target != "N/A" else "",
                    f"- **Issue:** {issue.issue_message}",
                    "",
                ]
            )
        if len(red_flags) > 20:
            report_lines.append(f"*... and {len(red_flags) - 20} more red flags*")
            report_lines.append("")

    # Show yellow flags second (warnings)
    if yellow_flags:
        prioritized_yellow = prioritize_issues(yellow_flags)
        report_lines.extend(
            [
                "## 🟡 Yellow Flags (Warnings)",
                "",
                f"**{len(yellow_flags)} warnings** that should be reviewed:",
                "",
            ]
        )
        for issue in prioritized_yellow[:15]:  # Show first 15 yellow flags
            issue_type = getattr(issue, "issue_type", "unknown")
            target = getattr(issue, "target", "N/A")
            report_lines.extend(
                [
                    f"**{issue.file}:{issue.line}**",
                    f"- **Type:** {issue_type}",
                    f"- **Target:** `{target}`" if target != "N/A" else "",
                    f"- **Issue:** {issue.issue_message}",
                    "",
                ]
            )
        if len(yellow_flags) > 15:
            report_lines.append(f"*... and {len(yellow_flags) - 15} more yellow flags*")
            report_lines.append("")

    # Show green flags last (exceptions) - only if requested
    if show_green_flags and green_flags:
        report_lines.extend(
            [
                "## 🟢 Green Flags (Known Exceptions)",
                "",
                f"**{len(green_flags)} known exceptions** (false positives filtered):",
                "",
                "*These are typically directory references, template patterns, or formatting artifacts.*",
                "",
            ]
        )
        # Group green flags by type for summary
        green_by_type = {}
        for issue in green_flags:
            issue_type = getattr(issue, "issue_type", "unknown")
            green_by_type[issue_type] = green_by_type.get(issue_type, 0) + 1

        for issue_type, count in sorted(green_by_type.items()):
            report_lines.append(f"- **{issue_type}:** {count} exceptions")
        report_lines.append("")

    return "\n".join(report_lines)
