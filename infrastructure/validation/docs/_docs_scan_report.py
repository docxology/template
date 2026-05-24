"""Markdown report builder for DocumentationScanner results."""

from infrastructure.validation.docs.models import ScanResults


def build_documentation_scan_report(results: ScanResults) -> str:
    """Build the comprehensive documentation scan report body."""
    report_lines = [
        "# Documentation Scan and Improvement Report",
        "",
        f"**Date**: {results.scan_date}",
        "**Scope**: Comprehensive documentation scan across entire repository",
        f"**Files Scanned**: {results.total_files} markdown files",
        "",
        "## Executive Summary",
        "",
        "A comprehensive documentation scan was performed across the entire repository.",
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
        "## Discovery",
        "",
        "### Documentation Structure",
        "",
    ]

    if "discovery" in results.statistics:
        discovery = results.statistics["discovery"]
        report_lines.extend(
            [
                f"- **Markdown Files**: {discovery['markdown_files']}",
                f"- **AGENTS.md/README.md Files**: {discovery['agents_readme_files']}",
                f"- **Configuration Files**: {discovery['config_files']}",
                f"- **Script Files**: {discovery['script_files']}",
                "",
            ]
        )

    report_lines.extend(["## Accuracy", ""])
    if "accuracy" in results.statistics:
        accuracy = results.statistics["accuracy"]
        report_lines.extend(
            [
                f"- **Link Issues**: {accuracy['link_issues']}",
                f"- **Command Issues**: {accuracy['command_issues']}",
                f"- **Path Issues**: {accuracy['path_issues']}",
                f"- **Config Issues**: {accuracy['config_issues']}",
                f"- **Terminology Issues**: {accuracy['terminology_issues']}",
                f"- **Total Issues**: {accuracy['total_issues']}",
                "",
            ]
        )

    if results.link_issues:
        report_lines.extend(["### Link Issues", ""])
        for issue in results.link_issues[:20]:
            report_lines.append(f"- `{issue.file}:{issue.line}` - {issue.target} ({issue.issue_message})")
        if len(results.link_issues) > 20:
            report_lines.append(f"- ... and {len(results.link_issues) - 20} more")
        report_lines.append("")

    report_lines.extend(
        [
            "## Completeness",
            "",
            f"Found {len(results.completeness_gaps)} completeness gaps across various categories.",  # noqa: E501
            "",
            "## Quality",
            "",
            f"Found {len(results.quality_issues)} quality issues requiring attention.",
            "",
            "## Improvements",
            "",
            f"Identified {len(results.improvements_made)} improvements to implement.",
            "",
            "## Verification",
            "",
            "All verification checks completed.",
            "",
            "## Recommendations",
            "",
            "1. Fix all broken links identified in accuracy checks",
            "2. Address completeness gaps identified in completeness analysis",
            "3. Improve quality issues identified in quality assessment",
            "4. Implement improvements identified in the improvements step",
            "",
            "---",
            "",
            f"**Report Generated**: {results.scan_date}",
            "**Next Review Recommended**: Quarterly or after major changes",
        ]
    )

    return "\n".join(report_lines)
