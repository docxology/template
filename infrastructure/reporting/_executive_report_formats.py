"""Markdown and HTML report formatters for executive summaries.

Transforms an ``ExecutiveSummary`` instance into human-readable Markdown
and styled HTML reports.
"""

from __future__ import annotations

from ._executive_models import ExecutiveSummary
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

def generate_markdown_report(summary: ExecutiveSummary) -> str:
    """Generate Markdown format executive report."""
    lines = [
        "# Executive Summary - All Projects",
        "",
        f"**Generated**: {summary.timestamp}",
        f"**Total Projects**: {summary.total_projects}",
        "",
        "## Executive Overview",
        "",
    ]

    # Generate key insights
    manuscript_words = summary.aggregate_metrics["manuscript"]["total_words"]
    total_projects = summary.total_projects
    avg_project_size = manuscript_words / total_projects if total_projects > 0 else 0

    # Identify best and worst performers
    projects_by_size = sorted(
        summary.project_metrics, key=lambda p: p.manuscript.total_words, reverse=True
    )
    largest_project = projects_by_size[0] if projects_by_size else None
    smallest_project = projects_by_size[-1] if len(projects_by_size) > 1 else None

    projects_by_efficiency = sorted(
        summary.project_metrics,
        key=lambda p: p.outputs.total_outputs / max(p.pipeline.total_duration, 1),
    )
    most_efficient = projects_by_efficiency[-1] if projects_by_efficiency else None

    lines.extend(
        [
            "### Key Findings",
            f"- **Portfolio Size**: {manuscript_words:,} total manuscript words across {total_projects} projects",  # noqa: E501
            f"- **Average Project**: {avg_project_size:,.0f} words per project",
        ]
    )

    if largest_project:
        lines.append(
            f"- **Largest Project**: {largest_project.name} ({largest_project.manuscript.total_words:,} words)"  # noqa: E501
        )

    if smallest_project and smallest_project != largest_project:
        lines.append(
            f"- **Smallest Project**: {smallest_project.name} ({smallest_project.manuscript.total_words:,} words)"  # noqa: E501
        )

    if most_efficient:
        efficiency = most_efficient.outputs.total_outputs / max(
            most_efficient.pipeline.total_duration, 1
        )
        lines.append(
            f"- **Most Efficient**: {most_efficient.name} ({efficiency:.2f} outputs/second)"
        )

    # Health assessment
    failing_projects = [
        p.name
        for p in summary.project_metrics
        if summary.health_scores.get(p.name, {}).get("percentage", 0) < 70
    ]
    if failing_projects:
        lines.extend(
            [
                "",
                "### Critical Issues",
                f"⚠️ **{len(failing_projects)} projects** require immediate attention:",
            ]
        )
        for project in failing_projects:
            health = summary.health_scores.get(project, {})
            grade = health.get("grade", "Unknown")
            lines.append(f"- **{project}**: {grade} health grade")
    else:
        lines.extend(["", "### Health Status", "✅ **All projects** are in good health"])

    lines.extend(
        [
            "",
            "## Aggregate Metrics",
            "",
            "### Manuscript",
            f"- **Total Words**: {summary.aggregate_metrics['manuscript']['total_words']:,}",
            f"- **Total Sections**: {summary.aggregate_metrics['manuscript']['total_sections']}",
            f"- **Total Equations**: {summary.aggregate_metrics['manuscript']['total_equations']}",
            f"- **Total Figures**: {summary.aggregate_metrics['manuscript']['total_figures']}",
            f"- **Total References**: {summary.aggregate_metrics['manuscript']['total_references']}",  # noqa: E501
            "",
            "### Codebase",
            f"- **Source Lines**: {summary.aggregate_metrics['codebase']['total_source_lines']:,}",
            f"- **Methods**: {summary.aggregate_metrics['codebase']['total_methods']}",
            f"- **Classes**: {summary.aggregate_metrics['codebase']['total_classes']}",
            f"- **Scripts**: {summary.aggregate_metrics['codebase']['total_scripts']}",
            "",
            "### Testing",
        ]
    )

    test_metrics = summary.aggregate_metrics["tests"]
    projects_with_data = test_metrics.get("projects_with_test_data", 0)
    total_projects_count = test_metrics.get("total_projects", summary.total_projects)

    if projects_with_data > 0:
        lines.extend(
            [
                f"- **Total Tests**: {test_metrics['total_tests']} ({test_metrics['total_passed']} passed)",  # noqa: E501
                f"- **Average Coverage**: {test_metrics['average_coverage']:.1f}%",
                f"- **Total Execution Time**: {test_metrics['total_execution_time']:.1f}s",
                f"- **Projects with Test Data**: {projects_with_data}/{total_projects_count}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"- **Test Data**: Unavailable for all {total_projects_count} projects",
                "- **Note**: Run test stage first to generate test metrics",
                "",
            ]
        )

    lines.extend(
        [
            "",
            "### Outputs",
            f"- **PDFs**: {summary.aggregate_metrics['outputs']['total_pdfs']} files ({summary.aggregate_metrics['outputs']['total_size_mb']:.1f} MB)",  # noqa: E501
            f"- **Figures**: {summary.aggregate_metrics['outputs']['total_figures']}",
            f"- **Slides**: {summary.aggregate_metrics['outputs']['total_slides']}",
            f"- **Web Pages**: {summary.aggregate_metrics['outputs']['total_web']}",
            "",
            "### Pipeline",
            f"- **Total Duration**: {summary.aggregate_metrics['pipeline']['total_duration']:.0f}s",
            f"- **Average Duration**: {summary.aggregate_metrics['pipeline']['average_duration']:.0f}s",  # noqa: E501
            f"- **Stages Passed**: {summary.aggregate_metrics['pipeline']['total_stages_passed']}",
            "",
            "## Project Comparison",
            "",
            "| Project | Words | Tests | Coverage | Duration | PDF Size |",
            "|---------|-------|-------|----------|----------|----------|",
        ]
    )

    for p in summary.project_metrics:
        lines.append(
            f"| {p.name} | {p.manuscript.total_words:,} | {p.tests.total_tests} | "
            f"{p.tests.coverage_percent:.1f}% | {p.pipeline.total_duration:.0f}s | "
            f"{p.outputs.pdf_size_mb:.1f} MB |"
        )

    # Add totals row
    lines.append(
        f"| **TOTAL** | **{summary.aggregate_metrics['manuscript']['total_words']:,}** | "
        f"**{summary.aggregate_metrics['tests']['total_tests']}** | "
        f"**{summary.aggregate_metrics['tests']['average_coverage']:.1f}%** | "
        f"**{summary.aggregate_metrics['pipeline']['total_duration']:.0f}s** | "
        f"**{summary.aggregate_metrics['outputs']['total_size_mb']:.1f} MB** |"
    )

    # Enhanced recommendations with prioritization
    lines.extend(["", "## Actionable Recommendations", ""])

    # Categorize and prioritize recommendations
    high_priority: list[str] = []
    medium_priority: list[str] = []
    low_priority: list[str] = []

    for rec in summary.recommendations:
        if any(
            keyword in rec.lower() for keyword in ["critical", "immediate", "failing", "broken"]
        ):
            high_priority.append(f"🚨 **HIGH**: {rec}")
        elif any(keyword in rec.lower() for keyword in ["below", "improve", "consider"]):
            medium_priority.append(f"⚠️ **MEDIUM**: {rec}")
        else:
            low_priority.append(f"ℹ️ **LOW**: {rec}")

    if high_priority:
        lines.extend(["### High Priority", ""] + high_priority + [""])

    if medium_priority:
        lines.extend(["### Medium Priority", ""] + medium_priority + [""])

    if low_priority:
        lines.extend(["### Low Priority", ""] + low_priority + [""])

    # Add visual dashboard references
    lines.extend(
        [
            "",
            "## Visual Dashboards",
            "",
            "Comprehensive visual analysis is available in the executive_summary directory:",
            "",
            "### Health & Quality",
            "- `health_scores_radar.png/pdf` - Multi-dimensional health analysis",
            "- `health_scores_comparison.png/pdf` - Health score breakdown by factor",
            "",
            "### Project Details",
            "- `project_dashboard_{name}.png/pdf` - Individual project overviews",
            "- `consolidated_report.html` - Interactive web report",
            "",
            "### Performance Analysis",
            "- `pipeline_efficiency.png/pdf` - Pipeline performance metrics",
            "- `pipeline_bottlenecks.png/pdf` - Bottleneck identification",
            "",
            "### Output Analysis",
            "- `output_distribution.png/pdf` - Output generation analysis",
            "- `output_comparison.png/pdf` - Cross-project output comparison",
            "",
            "### Codebase Analysis",
            "- `codebase_complexity.png/pdf` - Code complexity metrics",
            "- `codebase_comparison.png/pdf` - Codebase structure comparison",
        ]
    )

    return "\n".join(lines)


def generate_html_report(summary: ExecutiveSummary) -> str:
    """Generate HTML format executive report."""
    from infrastructure.reporting.html_templates import (
        get_base_html_template,
        render_summary_cards,
        render_table,
    )

    # Generate header content
    header_html = f"""        <h1>Executive Summary - All Projects</h1>
        <p><strong>Generated:</strong> {summary.timestamp}</p>
        <p><strong>Total Projects:</strong> {summary.total_projects}</p>"""

    # Generate summary cards
    test_metrics = summary.aggregate_metrics["tests"]
    projects_with_data = test_metrics.get("projects_with_test_data", 0)

    cards: list[dict[str, str]] = [
        {"title": "Total Projects", "value": str(summary.total_projects)},
        {
            "title": "Total Manuscript Words",
            "value": f"{summary.aggregate_metrics['manuscript']['total_words']:,}",
        },
    ]

    if projects_with_data > 0:
        cards.extend(
            [
                {"title": "Total Tests", "value": f"{test_metrics['total_tests']}"},
                {
                    "title": "Average Coverage",
                    "value": f"{test_metrics['average_coverage']:.1f}%",
                },
            ]
        )
    else:
        cards.extend(
            [
                {"title": "Test Data", "value": "Unavailable"},
                {"title": "Coverage", "value": "N/A"},
            ]
        )
    summary_cards_html = render_summary_cards(cards)

    # Generate comparative table
    headers = ["Project", "Words", "Tests", "Coverage", "Duration", "PDF Size"]
    rows = []
    for project in summary.project_metrics:
        rows.append(
            [
                project.name,
                f"{project.manuscript.total_words:,}",
                str(project.tests.total_tests),
                f"{project.tests.coverage_percent:.1f}%",
                f"{project.pipeline.total_duration:.0f}s",
                f"{project.outputs.pdf_size_mb:.2f} MB",
            ]
        )

    comparison_table_html = render_table(headers, rows)

    # Generate executive overview
    manuscript_words = summary.aggregate_metrics["manuscript"]["total_words"]
    avg_project_size = (
        manuscript_words / summary.total_projects if summary.total_projects > 0 else 0
    )

    # Find best/worst performers
    projects_by_size = sorted(
        summary.project_metrics, key=lambda p: p.manuscript.total_words, reverse=True
    )
    largest_project = projects_by_size[0] if projects_by_size else None

    overview_html = f"""
        <div class="section">
            <h2>Executive Overview</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Total Portfolio</h3>
                    <div class="value">{manuscript_words:,} words</div>
                </div>
                <div class="summary-card">
                    <h3>Average Project</h3>
                    <div class="value">{avg_project_size:,.0f} words</div>
                </div>
                <div class="summary-card">
                    <h3>Projects Analyzed</h3>
                    <div class="value">{summary.total_projects}</div>
                </div>
    """

    if largest_project:
        overview_html += f"""
                <div class="summary-card">
                    <h3>Largest Project</h3>
                    <div class="value">{largest_project.name}</div>
                </div>
        """

    overview_html += "        </div>\n        </div>"

    # Enhanced recommendations with prioritization
    high_priority: list[str] = []
    medium_priority: list[str] = []
    low_priority: list[str] = []

    for rec in summary.recommendations:
        if any(
            keyword in rec.lower() for keyword in ["critical", "immediate", "failing", "broken"]
        ):
            high_priority.append(f'<li class="status-failed">{rec}</li>')
        elif any(keyword in rec.lower() for keyword in ["below", "improve", "consider"]):
            medium_priority.append(f'<li class="status-warning">{rec}</li>')
        else:
            low_priority.append(f'<li class="status-passed">{rec}</li>')

    recommendations_html = '<div class="section"><h2>Actionable Recommendations</h2>'

    if high_priority:
        recommendations_html += "<h3>🚨 High Priority</h3><ul>" + "".join(high_priority) + "</ul>"

    if medium_priority:
        recommendations_html += (
            "<h3>⚠️ Medium Priority</h3><ul>" + "".join(medium_priority) + "</ul>"
        )

    if low_priority:
        recommendations_html += "<h3>ℹ️ Low Priority</h3><ul>" + "".join(low_priority) + "</ul>"

    recommendations_html += "</div>"

    # Add visual dashboard section
    dashboard_html = """
        <div class="section">
            <h2>Visual Dashboards</h2>
            <p>Comprehensive visual analysis is available:</p>
            <ul>
                <li><strong>Health & Quality:</strong> health_scores_radar.png/pdf, health_scores_comparison.png/pdf</li>
                <li><strong>Project Details:</strong> project_dashboard_{name}.png/pdf, consolidated_report.html</li>
                <li><strong>Performance:</strong> pipeline_efficiency.png/pdf, pipeline_bottlenecks.png/pdf</li>
                <li><strong>Outputs:</strong> output_distribution.png/pdf, output_comparison.png/pdf</li>
                <li><strong>Codebase:</strong> codebase_complexity.png/pdf, codebase_comparison.png/pdf</li>
            </ul>
        </div>
    """

    # Generate main content
    content_html = f"""
        {overview_html}

        <div class="section">
            <h2>Key Metrics</h2>
            {summary_cards_html}
        </div>

        <div class="section">
            <h2>Project Comparison</h2>
            {comparison_table_html}
        </div>

        {recommendations_html}

        {dashboard_html}
    """

    # Generate footer content
    footer_html = f"""        <p>Generated by Research Template Executive Reporter</p>
        <p>Timestamp: {summary.timestamp}</p>"""

    # Get base template and fill placeholders
    html = get_base_html_template()
    html = html.replace("{title}", "Executive Summary - All Projects")
    html = html.replace("{header}", header_html)
    html = html.replace("{content}", content_html)
    html = html.replace("{footer}", footer_html)

    return html
