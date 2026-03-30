"""Markdown report builder for repository scan results."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from infrastructure.validation.repo.models import RepoScanResults


def build_repo_scan_report(results: RepoScanResults) -> str:
    """Build the repository accuracy and completeness scan report body."""
    lines = [
        "# Repository Accuracy and Completeness Scan Report",
        "",
        f"**Scan Date**: {datetime.now().isoformat()}",
        "",
        "## Executive Summary",
        "",
        f"- **Accuracy Issues**: {len(results.accuracy_issues)}",
        f"- **Completeness Gaps**: {len(results.completeness_gaps)}",
        "",
        "## Accuracy Issues",
        "",
    ]

    by_category: dict[str, list] = defaultdict(list)
    for issue in results.accuracy_issues:
        by_category[issue.category].append(issue)

    for category, cat_issues in sorted(by_category.items()):
        lines.append(f"### {category.title()} Issues ({len(cat_issues)})")
        lines.append("")
        for issue in cat_issues[:20]:
            lines.append(f"- **{issue.severity.upper()}**: `{issue.file}`")
            if issue.line:
                lines.append(f"  - Line {issue.line}: {issue.message}")
            else:
                lines.append(f"  - {issue.message}")
            if issue.details:
                lines.append(f"  - Details: {issue.details}")
        if len(cat_issues) > 20:
            lines.append(f"- ... and {len(cat_issues) - 20} more")
        lines.append("")

    lines.extend(["## Completeness Gaps", ""])

    by_gap_cat: dict[str, list] = defaultdict(list)
    for gap in results.completeness_gaps:
        by_gap_cat[gap.category].append(gap)

    for category, gaps in sorted(by_gap_cat.items()):
        lines.append(f"### {category.title()} Gaps ({len(gaps)})")
        lines.append("")
        for gap in gaps:
            lines.append(f"- **{gap.severity.upper()}**: {gap.item}")
            lines.append(f"  - {gap.description}")
        lines.append("")

    lines.extend(
        [
            "## Recommendations",
            "",
            "1. Address all ERROR-level accuracy issues",
            "2. Review WARNING-level issues for potential problems",
            "3. Fill completeness gaps where appropriate",
            "4. Ensure all src/ modules are tested and documented",
            "",
        ]
    )

    return "\n".join(lines)
