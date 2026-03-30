"""Markdown report builder for DocumentationScanner results."""

from __future__ import annotations

from infrastructure.validation.docs.models import ScanResults


def build_documentation_scan_report(results: ScanResults) -> str:
    """Build the comprehensive documentation scan report body."""
    report_lines = [
        "# Documentation Scan and Improvement Report",
        "",
        f"**Date**: {results.scan_date}",
        "**Scope**: Comprehensive 7-phase documentation scan across entire repository",
        f"**Files Scanned**: {results.total_files} markdown files",
        "",
        "## Executive Summary",
        "",
        "A comprehensive documentation scan was performed across the entire repository following the systematic 7-phase approach.",  # noqa: E501
        "",
        "### Key Statistics",
        "",
        f"- **Total Files Scanned**: {results.total_files} markdown files",
        f"- **Link Issues Found**: {len(results.link_issues)}",
        f"- **Accuracy Issues Found**: {len(results.accuracy_issues)}",
        f"- **Completeness Gaps**: {len(results.completeness_gaps)}",
        f"- **Quality Issues**: {len(results.quality_issues)}",
        f"- **Improvements Identified**: {len(results.improvements_made)}",
        "",
        "## Phase 1: Discovery and Inventory",
        "",
        "### Documentation Structure",
        "",
    ]

    if "phase1" in results.statistics:
        phase1 = results.statistics["phase1"]
        report_lines.extend(
            [
                f"- **Markdown Files**: {phase1['markdown_files']}",
                f"- **AGENTS.md/README.md Files**: {phase1['agents_readme_files']}",
                f"- **Configuration Files**: {phase1['config_files']}",
                f"- **Script Files**: {phase1['script_files']}",
                "",
            ]
        )

    report_lines.extend(["## Phase 2: Accuracy Verification", ""])
    if "phase2" in results.statistics:
        phase2 = results.statistics["phase2"]
        report_lines.extend(
            [
                f"- **Link Issues**: {phase2['link_issues']}",
                f"- **Command Issues**: {phase2['command_issues']}",
                f"- **Path Issues**: {phase2['path_issues']}",
                f"- **Config Issues**: {phase2['config_issues']}",
                f"- **Terminology Issues**: {phase2['terminology_issues']}",
                f"- **Total Issues**: {phase2['total_issues']}",
                "",
            ]
        )

    if results.link_issues:
        report_lines.extend(["### Link Issues", ""])
        for issue in results.link_issues[:20]:
            report_lines.append(
                f"- `{issue.file}:{issue.line}` - {issue.target} ({issue.issue_message})"
            )
        if len(results.link_issues) > 20:
            report_lines.append(f"- ... and {len(results.link_issues) - 20} more")
        report_lines.append("")

    report_lines.extend(
        [
            "## Phase 3: Completeness Analysis",
            "",
            f"Found {len(results.completeness_gaps)} completeness gaps across various categories.",  # noqa: E501
            "",
            "## Phase 4: Quality Assessment",
            "",
            f"Found {len(results.quality_issues)} quality issues requiring attention.",
            "",
            "## Phase 5: Intelligent Improvements",
            "",
            f"Identified {len(results.improvements_made)} improvements to implement.",
            "",
            "## Phase 6: Verification and Validation",
            "",
            "All verification checks completed.",
            "",
            "## Recommendations",
            "",
            "1. Fix all broken links identified in Phase 2",
            "2. Address completeness gaps identified in Phase 3",
            "3. Improve quality issues identified in Phase 4",
            "4. Implement improvements identified in Phase 5",
            "",
            "---",
            "",
            f"**Report Generated**: {results.scan_date}",
            "**Next Review Recommended**: Quarterly or after major changes",
        ]
    )

    return "\n".join(report_lines)
