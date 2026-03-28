"""Markdown report generation for pipeline execution results.

Generates Markdown-formatted reports from PipelineReport data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from infrastructure.core.logging.helpers import format_duration

if TYPE_CHECKING:
    from .pipeline_report_model import PipelineReport


def _generate_pipeline_markdown(report: PipelineReport) -> str:
    """Generate Markdown format pipeline report."""
    lines = [
        "# Pipeline Execution Report",
        "",
        f"**Generated:** {report.timestamp}",
        f"**Total Duration:** {format_duration(report.total_duration)}",
        "",
        "## Summary",
        "",
    ]

    # Calculate summary statistics
    passed = sum(1 for s in report.stages if s.status == "passed")
    failed = sum(1 for s in report.stages if s.status == "failed")
    total = len(report.stages)

    lines.append(f"- **Stages Executed:** {total}")
    lines.append(f"- **Stages Passed:** {passed}")
    lines.append(f"- **Stages Failed:** {failed}")
    lines.append(f"- **Success Rate:** {(passed / total * 100) if total > 0 else 0:.1f}%")
    lines.append("")

    # Stage details
    lines.append("## Stage Results")
    lines.append("")
    lines.append("| Stage | Status | Duration | Exit Code |")
    lines.append("|-------|--------|----------|-----------|")

    for stage in report.stages:
        status_emoji = "✅" if stage.status == "passed" else "❌"
        duration_str = format_duration(stage.duration)
        lines.append(
            f"| {stage.name} | {status_emoji} {stage.status} | {duration_str} | {stage.exit_code} |"
        )

    lines.append("")

    # Test results section
    if report.test_results:
        lines.append("## Test Results")
        lines.append("")
        summary = report.test_results.get("summary", {})
        lines.append(f"- **Total Tests:** {summary.get('total_tests', 0)}")
        lines.append(f"- **Passed:** {summary.get('total_passed', 0)}")
        lines.append(f"- **Failed:** {summary.get('total_failed', 0)}")
        lines.append(f"- **Skipped:** {summary.get('total_skipped', 0)}")
        if "infrastructure_coverage" in summary:
            lines.append(
                f"- **Infrastructure Coverage:** {summary['infrastructure_coverage']:.2f}%"
            )
        if "project_coverage" in summary:
            lines.append(f"- **Project Coverage:** {summary['project_coverage']:.2f}%")
        lines.append("")

    # Validation results section
    if report.validation_results:
        lines.append("## Validation Results")
        lines.append("")
        for key, value in report.validation_results.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    # Performance metrics section
    if report.performance_metrics:
        lines.append("## Performance Metrics")
        lines.append("")
        for key, value in report.performance_metrics.items():
            if isinstance(value, float):
                lines.append(f"- **{key}:** {value:.2f}")
            else:
                lines.append(f"- **{key}:** {value}")
        lines.append("")

    # Error summary section
    if report.error_summary and report.error_summary.get("total_errors", 0) > 0:
        lines.append("## Error Summary")
        lines.append("")
        lines.append(f"**Total Errors:** {report.error_summary.get('total_errors', 0)}")
        lines.append("")
        errors = report.error_summary.get("errors", [])
        if errors:
            for err in errors[:5]:
                lines.append(f"- {err}")
            if len(errors) > 5:
                lines.append(f"- ... and {len(errors) - 5} more")
            lines.append("")

    # Output statistics section
    if report.output_statistics:
        lines.append("## Output Statistics")
        lines.append("")
        stats = report.output_statistics
        lines.append(f"- **PDF Files:** {stats.get('pdf_files', 0)}")
        lines.append(f"- **Figures:** {stats.get('figures', 0)}")
        lines.append(f"- **Data Files:** {stats.get('data_files', 0)}")
        lines.append("")

    return "\n".join(lines)
