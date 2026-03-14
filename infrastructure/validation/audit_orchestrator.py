"""Audit orchestrator that coordinates all validation modules for filepath and reference auditing.

This module provides a unified interface for running audits across all validation modules,
categorizing issues, and generating structured reports.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.validation.check_links import (
    validate_directory_structures,
    validate_file_paths_in_code,
    validate_placeholder_consistency,
    validate_python_imports,
)
from infrastructure.validation.doc_accuracy import check_links, extract_headings
from infrastructure.validation.doc_discovery import categorize_documentation, discover_markdown_files
from infrastructure.validation.doc_models import (
    DocumentationFile,
    LinkIssue,
    QualityIssue,
    ScanResults,
)
from infrastructure.validation.issue_categorizer import (
    generate_issue_summary,
    get_severity_flag,
    prioritize_issues,
)

logger = get_logger(__name__)

def run_comprehensive_audit(
    repo_root: Path,
    verbose: bool = False,
    include_code_validation: bool = True,
    include_directory_validation: bool = True,
    include_import_validation: bool = True,
    include_placeholder_validation: bool = True,
) -> ScanResults:
    """Run audit across all validation modules and return categorized scan results."""
    start_time = time.time()

    logger.info("🔍 Starting filepath and reference audit...")

    # Phase 1: Discovery
    md_files = discover_markdown_files(repo_root)
    logger.info(f"📁 Found {len(md_files)} markdown files to audit")

    # Get project categorization
    doc_categories = categorize_documentation(md_files, repo_root)

    # Phase 2: Collect headings for anchor validation
    all_headings = {}
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(content)
        except (OSError, UnicodeDecodeError) as e:
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

        except (OSError, UnicodeDecodeError, ValueError) as e:
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
        f"📊 Found {len(scan_results.link_issues) + len(scan_results.accuracy_issues) + len(scan_results.quality_issues)} total issues"  # noqa: E501
    )

    return scan_results

def _validate_single_file(
    md_file: Path,
    content: str,
    repo_root: Path,
    all_headings: dict[str, set[str]],
    include_code: bool,
    include_directory: bool,
    include_imports: bool,
    include_placeholders: bool,
) -> dict[str, list[Any]]:
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
    except (OSError, UnicodeDecodeError, ValueError) as e:
        logger.warning(f"Link validation failed for {md_file}: {e}")

    quality_validators = [
        (include_code, validate_file_paths_in_code, "code_block_path", "warning", "Code block path issue"),
        (include_directory, validate_directory_structures, "directory_structure", "info", "Directory structure issue"),
        (include_imports, validate_python_imports, "python_import", "warning", "Python import issue"),
        (include_placeholders, validate_placeholder_consistency, "placeholder_consistency", "info", "Placeholder consistency issue"),
    ]
    for flag, validator_fn, issue_type, severity, default_msg in quality_validators:
        if flag:
            try:
                for issue in validator_fn(content, md_file, repo_root):
                    results["quality_issues"].append(
                        QualityIssue(
                            file=file_key,
                            line=issue.get("line", 0),
                            issue_type=issue_type,
                            issue_message=issue.get("issue", default_msg),
                            severity=severity,
                        )
                    )
            except (OSError, UnicodeDecodeError, ValueError) as e:
                logger.warning(f"{issue_type} validation failed for {md_file}: {e}")

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
    """Generate a formatted audit report with red/yellow/green severity flag classification."""
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
                "green_flags": ([vars(issue) for issue in green_flags] if show_green_flags else []),
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
                "No broken links, missing files, or reference issues were found in the documentation.",  # noqa: E501
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
                f"🔴 **Red Flags (Critical):** {len(red_flags)} - Issues requiring immediate attention",  # noqa: E501
                f"🟡 **Yellow Flags (Warnings):** {len(yellow_flags)} - Issues that should be reviewed",  # noqa: E501
                f"🟢 **Green Flags (Exceptions):** {len(green_flags)} - Known exceptions and false positives",  # noqa: E501
                "",
                (
                    f"**False Positives Filtered:** {summary.get('false_positives', 0)} ({100 * summary.get('false_positives', 0) / total_issues:.1f}%)"  # noqa: E501
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
                report_lines.append(f"- **{category.replace('_', ' ').title()}:** {count} issues")

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
        for issue in prioritized_red[:20]:
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
            ]
        )
        for issue in prioritized_yellow[:15]:
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
                "*These are typically directory references, template patterns, or formatting artifacts.*",  # noqa: E501
                "",
            ]
        )
        # Group green flags by type for summary
        green_by_type: dict[str, int] = {}
        for issue in green_flags:
            issue_type = getattr(issue, "issue_type", "unknown")
            green_by_type[issue_type] = green_by_type.get(issue_type, 0) + 1

        for issue_type, count in sorted(green_by_type.items()):
            report_lines.append(f"- **{issue_type}:** {count} exceptions")
        report_lines.append("")

    return "\n".join(report_lines)
