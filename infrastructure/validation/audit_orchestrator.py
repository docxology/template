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
from infrastructure.validation.doc_discovery import find_markdown_files, categorize_documentation
from infrastructure.validation.doc_accuracy import check_links
from infrastructure.validation.check_links import (
    extract_headings,
    validate_file_paths_in_code,
    validate_directory_structures,
    validate_python_imports,
    validate_placeholder_consistency
)
from infrastructure.validation.doc_models import (
    ScanResults,
    LinkIssue,
    AccuracyIssue,
    CompletenessGap,
    QualityIssue,
    DocumentationFile
)

logger = get_logger(__name__)


def run_comprehensive_audit(
    repo_root: Path,
    verbose: bool = False,
    include_code_validation: bool = True,
    include_directory_validation: bool = True,
    include_import_validation: bool = True,
    include_placeholder_validation: bool = True
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
            content = md_file.read_text(encoding='utf-8')
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(content)
        except Exception as e:
            if verbose:
                logger.warning(f"Error reading {md_file}: {e}")

    # Phase 3: Run all validations
    scan_results = ScanResults(scan_date=time.strftime('%Y-%m-%d %H:%M:%S'))

    # Process each file
    for i, md_file in enumerate(md_files):
        if verbose and (i + 1) % 10 == 0:
            logger.info(f"🔄 Processed {i + 1}/{len(md_files)} files...")

        try:
            content = md_file.read_text(encoding='utf-8')
            file_results = _validate_single_file(
                md_file, content, repo_root, all_headings,
                include_code_validation, include_directory_validation,
                include_import_validation, include_placeholder_validation
            )

            # Add to scan results
            scan_results.link_issues.extend(file_results['link_issues'])
            scan_results.accuracy_issues.extend(file_results['accuracy_issues'])
            scan_results.quality_issues.extend(file_results['quality_issues'])

            # Create documentation file entry
            doc_file = DocumentationFile(
                path=str(md_file.relative_to(repo_root)),
                relative_path=str(md_file.relative_to(repo_root)),
                directory=str(md_file.parent.relative_to(repo_root)),
                name=md_file.name,
                category=doc_categories.get(str(md_file.relative_to(repo_root)), ""),
                word_count=len(content.split()),
                line_count=len(content.splitlines()),
                has_links='[' in content and ']' in content,
                has_code_blocks='```' in content
            )
            scan_results.documentation_files.append(doc_file)

        except Exception as e:
            logger.error(f"Error processing {md_file}: {e}")
            scan_results.quality_issues.append(QualityIssue(
                file=str(md_file.relative_to(repo_root)),
                line=0,
                issue_type='processing_error',
                issue_message=f"Failed to process file: {e}",
                severity='error'
            ))

    # Phase 4: Calculate statistics
    scan_results.scan_duration = time.time() - start_time
    _calculate_statistics(scan_results)

    logger.info(f"✅ Audit completed in {scan_results.scan_duration:.2f}s")
    logger.info(f"📊 Found {len(scan_results.link_issues) + len(scan_results.accuracy_issues) + len(scan_results.quality_issues)} total issues")

    return scan_results


def _validate_single_file(
    md_file: Path,
    content: str,
    repo_root: Path,
    all_headings: Dict[str, set],
    include_code: bool,
    include_directory: bool,
    include_imports: bool,
    include_placeholders: bool
) -> Dict[str, List]:
    """Validate a single markdown file using all available validation modules."""

    file_key = str(md_file.relative_to(repo_root))
    results = {
        'link_issues': [],
        'accuracy_issues': [],
        'quality_issues': []
    }

    # Link validation using doc_accuracy
    try:
        link_issues = check_links(md_file, repo_root, all_headings)
        for issue in link_issues:
            results['link_issues'].append(LinkIssue(
                source_file=file_key,
                target=issue.get('target', ''),
                line=issue.get('line', 0),
                link_text=issue.get('text', ''),
                issue_type=issue.get('issue_type', 'link_issue'),
                issue_message=issue.get('issue', 'Link validation failed'),
                severity='error'
            ))
    except Exception as e:
        logger.warning(f"Link validation failed for {md_file}: {e}")

    # Code block path validation
    if include_code:
        try:
            code_issues = validate_file_paths_in_code(content, md_file, repo_root)
            for issue in code_issues:
                results['quality_issues'].append(QualityIssue(
                    file=file_key,
                    line=issue.get('line', 0),
                    issue_type='code_block_path',
                    issue_message=issue.get('issue', 'Code block path issue'),
                    severity='warning'
                ))
        except Exception as e:
            logger.warning(f"Code validation failed for {md_file}: {e}")

    # Directory structure validation
    if include_directory:
        try:
            dir_issues = validate_directory_structures(content, md_file, repo_root)
            for issue in dir_issues:
                results['quality_issues'].append(QualityIssue(
                    file=file_key,
                    line=issue.get('line', 0),
                    issue_type='directory_structure',
                    issue_message=issue.get('issue', 'Directory structure issue'),
                    severity='info'
                ))
        except Exception as e:
            logger.warning(f"Directory validation failed for {md_file}: {e}")

    # Python import validation
    if include_imports:
        try:
            import_issues = validate_python_imports(content, md_file, repo_root)
            for issue in import_issues:
                results['quality_issues'].append(QualityIssue(
                    file=file_key,
                    line=issue.get('line', 0),
                    issue_type='python_import',
                    issue_message=issue.get('issue', 'Python import issue'),
                    severity='warning'
                ))
        except Exception as e:
            logger.warning(f"Import validation failed for {md_file}: {e}")

    # Placeholder consistency validation
    if include_placeholders:
        try:
            placeholder_issues = validate_placeholder_consistency(content, md_file, repo_root)
            for issue in placeholder_issues:
                results['quality_issues'].append(QualityIssue(
                    file=file_key,
                    line=issue.get('line', 0),
                    issue_type='placeholder_consistency',
                    issue_message=issue.get('issue', 'Placeholder consistency issue'),
                    severity='info'
                ))
        except Exception as e:
            logger.warning(f"Placeholder validation failed for {md_file}: {e}")

    return results


def _calculate_statistics(scan_results: ScanResults) -> None:
    """Calculate statistics for the scan results."""
    scan_results.scanned_files = len(scan_results.documentation_files)

    # Calculate statistics by issue type
    stats = {
        'link_issues': len(scan_results.link_issues),
        'accuracy_issues': len(scan_results.accuracy_issues),
        'completeness_gaps': len(scan_results.completeness_gaps),
        'quality_issues': len(scan_results.quality_issues)
    }

    scan_results.statistics = stats


def generate_audit_report(scan_results: ScanResults, output_format: str = 'markdown') -> str:
    """Generate a formatted audit report.

    Args:
        scan_results: Complete scan results
        output_format: Output format ('markdown' or 'json')

    Returns:
        Formatted report string
    """
    if output_format == 'json':
        import json
        return json.dumps({
            'scan_date': scan_results.scan_date,
            'total_files': scan_results.total_files,
            'scan_duration': 0.0,
            'statistics': scan_results.statistics,
            'link_issues': [vars(issue) for issue in scan_results.link_issues],
            'accuracy_issues': [vars(issue) for issue in scan_results.accuracy_issues],
            'completeness_gaps': [vars(issue) for issue in scan_results.completeness_gaps],
            'quality_issues': [vars(issue) for issue in scan_results.quality_issues]
        }, indent=2, default=str)

    # Default markdown format
    report_lines = [
        "# 📊 Comprehensive Filepath and Reference Audit Report",
        "",
        f"**Generated:** {scan_results.scan_date}",
        f"**Files Scanned:** {scan_results.total_files}",
        f"**Scan Duration:** 0.00 seconds",
        "",
        "## 📈 Executive Summary",
        ""
    ]

    total_issues = sum(scan_results.statistics.values())
    if total_issues == 0:
        report_lines.extend([
            "✅ **ALL VALIDATIONS PASSED!**",
            "",
            "No broken links, missing files, or reference issues were found in the documentation.",
            ""
        ])
    else:
        report_lines.extend([
            f"🚨 **{total_issues} issues** found across {len([k for k, v in scan_results.statistics.items() if v > 0])} categories.",
            "",
            "### Issues by Category",
            ""
        ])

        for category, count in scan_results.statistics.items():
            if count > 0:
                report_lines.append(f"- **{category.replace('_', ' ').title()}:** {count} issues")

        report_lines.append("")

    # Detailed issues sections
    if scan_results.link_issues:
        report_lines.extend([
            "## 🔗 Link Issues",
            "",
            f"Found {len(scan_results.link_issues)} link validation issues:",
            ""
        ])
        for issue in scan_results.link_issues[:10]:  # Show first 10
            report_lines.extend([
                f"**{issue.source_file}:{issue.line}**",
                f"- **Target:** `{issue.target}`",
                f"- **Issue:** {issue.issue_message}",
                ""
            ])

    if scan_results.accuracy_issues:
        report_lines.extend([
            "## 🎯 Accuracy Issues",
            "",
            f"Found {len(scan_results.accuracy_issues)} accuracy validation issues:",
            ""
        ])
        for issue in scan_results.accuracy_issues[:10]:
            report_lines.extend([
                f"**{issue.file}:{issue.line}**",
                f"- **Issue:** {issue.issue_message}",
                ""
            ])

    if scan_results.quality_issues:
        report_lines.extend([
            "## ⭐ Quality Issues",
            "",
            f"Found {len(scan_results.quality_issues)} quality validation issues:",
            ""
        ])
        for issue in scan_results.quality_issues[:10]:
            report_lines.extend([
                f"**{issue.file}:{issue.line}**",
                f"- **Type:** {issue.issue_type}",
                f"- **Issue:** {issue.issue_message}",
                ""
            ])

    return "\n".join(report_lines)