"""Pipeline reporter for generating consolidated reports.

Generates comprehensive reports in multiple formats (JSON, HTML, Markdown)
from pipeline execution data.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from infrastructure.core.checkpoint import StageResult
from infrastructure.core.logging_utils import format_duration, get_logger

logger = get_logger(__name__)


@dataclass
class PipelineReport:
    """Complete pipeline execution report."""

    timestamp: str
    total_duration: float
    stages: list[StageResult]
    test_results: Optional[dict[str, Any]] = None
    validation_results: Optional[dict[str, Any]] = None
    performance_metrics: Optional[dict[str, Any]] = None
    error_summary: Optional[dict[str, Any]] = None
    output_statistics: Optional[dict[str, Any]] = None


def generate_pipeline_report(
    stage_results: list[dict[str, Any]],
    total_duration: float,
    repo_root: Path,
    *,
    test_results: Optional[dict[str, Any]] = None,
    validation_results: Optional[dict[str, Any]] = None,
    performance_metrics: Optional[dict[str, Any]] = None,
    error_summary: Optional[dict[str, Any]] = None,
    output_statistics: Optional[dict[str, Any]] = None,
    project_name: Optional[str] = None,
) -> PipelineReport:
    """Generate consolidated pipeline report from stage results and optional extras."""
    stages = []
    for result in stage_results:
        status = "passed" if result.get("exit_code", 1) == 0 else "failed"
        stages.append(
            StageResult(
                name=result.get("name", "unknown"),
                exit_code=result.get("exit_code", 1),
                duration=result.get("duration", 0.0),
                status=status,
            )
        )

    # Enrich a copy of output_statistics with log file info (avoid mutating caller's dict)
    if project_name and output_statistics is not None:
        log_file = repo_root / "projects" / project_name / "output" / "logs" / "pipeline.log"
        output_statistics = {
            **output_statistics,
            "log_file": {
                "exists": log_file.exists(),
                "size": log_file.stat().st_size if log_file.exists() else 0,
                "path": str(log_file),
            },
        }

    return PipelineReport(
        timestamp=datetime.now().isoformat(),
        total_duration=total_duration,
        stages=stages,
        test_results=test_results,
        validation_results=validation_results,
        performance_metrics=performance_metrics,
        error_summary=error_summary,
        output_statistics=output_statistics,
    )


def save_pipeline_report(
    report: PipelineReport, output_dir: Path, formats: Optional[list[str]] = None
) -> dict[str, Path]:
    """Save pipeline report in multiple formats.

    Args:
        report: PipelineReport instance
        output_dir: Output directory path
        formats: List of formats to generate ('json', 'html', 'markdown')

    Returns:
        Dictionary mapping format to file path
    """
    if formats is None:
        formats = ["json", "html", "markdown"]

    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}

    report_dict = {
        "timestamp": report.timestamp,
        "total_duration": report.total_duration,
        "stages": [asdict(stage) for stage in report.stages],
        "test_results": report.test_results,
        "validation_results": report.validation_results,
        "performance_metrics": report.performance_metrics,
        "error_summary": report.error_summary,
        "output_statistics": report.output_statistics,
    }

    if "json" in formats:
        json_path = output_dir / "pipeline_report.json"
        try:
            with open(json_path, "w") as f:
                json.dump(report_dict, f, indent=2)
            saved_files["json"] = json_path
            logger.info(f"Pipeline report (JSON) saved: {json_path}")
        except OSError as e:
            logger.error(f"Failed to write JSON report {json_path}: {e}")
            raise

    if "markdown" in formats:
        md_path = output_dir / "pipeline_report.md"
        try:
            md_content = _generate_pipeline_markdown(report)
            md_path.write_text(md_content)
            saved_files["markdown"] = md_path
            logger.info(f"Pipeline report (Markdown) saved: {md_path}")
        except OSError as e:
            logger.error(f"Failed to write Markdown report {md_path}: {e}")
            raise

    if "html" in formats:
        html_path = output_dir / "pipeline_report.html"
        try:
            html_content = generate_html_report(report)
            html_path.write_text(html_content)
            saved_files["html"] = html_path
            logger.info(f"Pipeline report (HTML) saved: {html_path}")
        except OSError as e:
            logger.error(f"Failed to write HTML report {html_path}: {e}")
            raise

    return saved_files


def _generate_pipeline_markdown(report: PipelineReport) -> str:
    """Generate Markdown format pipeline report.

    Args:
        report: PipelineReport instance

    Returns:
        Markdown formatted report
    """
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


def generate_html_report(report: PipelineReport) -> str:
    """Generate HTML format pipeline report.

    Args:
        report: PipelineReport instance

    Returns:
        HTML formatted report
    """
    # Calculate summary statistics
    passed = sum(1 for s in report.stages if s.status == "passed")
    failed = sum(1 for s in report.stages if s.status == "failed")
    total = len(report.stages)
    success_rate = (passed / total * 100) if total > 0 else 0

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Pipeline Execution Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .status-passed {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-failed {{
            color: #dc3545;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Pipeline Execution Report</h1>
        <p><strong>Generated:</strong> {report.timestamp}</p>
        <p><strong>Total Duration:</strong> {format_duration(report.total_duration)}</p>
    </div>
    
    <div class="summary">
        <div class="summary-card">
            <h3>Stages Executed</h3>
            <div class="value">{total}</div>
        </div>
        <div class="summary-card">
            <h3>Stages Passed</h3>
            <div class="value" style="color: #28a745;">{passed}</div>
        </div>
        <div class="summary-card">
            <h3>Stages Failed</h3>
            <div class="value" style="color: #dc3545;">{failed}</div>
        </div>
        <div class="summary-card">
            <h3>Success Rate</h3>
            <div class="value">{success_rate:.1f}%</div>
        </div>
    </div>
    
    <div class="section">
        <h2>Stage Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Exit Code</th>
                </tr>
            </thead>
            <tbody>
"""

    for stage in report.stages:
        status_class = "status-passed" if stage.status == "passed" else "status-failed"
        status_text = "✅ Passed" if stage.status == "passed" else "❌ Failed"
        html += f"""                <tr>
                    <td>{stage.name}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{format_duration(stage.duration)}</td>
                    <td>{stage.exit_code}</td>
                </tr>
"""

    html += """            </tbody>
        </table>
    </div>
"""

    # Add test results section if available
    if report.test_results:
        summary = report.test_results.get("summary", {})
        html += f"""    <div class="section">
        <h2>Test Results</h2>
        <p><strong>Total Tests:</strong> {summary.get("total_tests", 0)}</p>
        <p><strong>Passed:</strong> {summary.get("total_passed", 0)}</p>
        <p><strong>Failed:</strong> {summary.get("total_failed", 0)}</p>
        <p><strong>Skipped:</strong> {summary.get("total_skipped", 0)}</p>
"""
        if "infrastructure_coverage" in summary:
            html += f"        <p><strong>Infrastructure Coverage:</strong> {summary['infrastructure_coverage']:.2f}%</p>\n"  # noqa: E501
        if "project_coverage" in summary:
            html += f"        <p><strong>Project Coverage:</strong> {summary['project_coverage']:.2f}%</p>\n"  # noqa: E501
        html += "    </div>\n"

    html += """</body>
</html>"""

    return html


def save_test_results(test_results: dict[str, Any], output_dir: Path) -> Path:
    """Write test_results dict to test_results.json and return the path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "test_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, default=str)
    return report_path


def generate_validation_report(
    validation_results: dict[str, Any], output_dir: Path
) -> dict[str, Path]:
    """Generate validation report as JSON and Markdown; returns paths by format key."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}

    json_path = output_dir / "validation_report.json"
    with open(json_path, "w") as f:
        json.dump(validation_results, f, indent=2)
    saved_files["json"] = json_path

    md_path = output_dir / "validation_report.md"
    md_content = generate_validation_markdown(validation_results)
    md_path.write_text(md_content)
    saved_files["markdown"] = md_path

    return saved_files


def generate_validation_markdown(results: dict[str, Any]) -> str:
    """Return Markdown-formatted validation report for the given results dict."""
    lines = [
        "# Validation Report",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
    ]

    # Add validation details
    if "checks" in results:
        lines.append("## Validation Checks")
        lines.append("")
        for check_name, check_result in results["checks"].items():
            status = "✅ PASS" if check_result else "❌ FAIL"
            lines.append(f"- {status}: {check_name}")
        lines.append("")

    return "\n".join(lines)


def generate_performance_report(performance_metrics: dict[str, Any], output_dir: Path) -> Path:
    """Write performance_metrics dict to performance_report.json and return the path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "performance_report.json"
    with open(json_path, "w") as f:
        json.dump(performance_metrics, f, indent=2)

    return json_path


def save_error_summary(errors: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    """Aggregate errors, write JSON and Markdown reports, and return the summary dict."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Categorize errors
    by_type: dict[str, list[dict[str, Any]]] = {}
    for error in errors:
        error_type = error.get("type", "unknown")
        if error_type not in by_type:
            by_type[error_type] = []
        by_type[error_type].append(error)

    summary = {
        "total_errors": len(errors),
        "errors_by_type": {k: len(v) for k, v in by_type.items()},
        "errors": errors,
    }

    # Save JSON report
    json_path = output_dir / "error_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    md_path = output_dir / "error_summary.md"
    md_content = generate_error_markdown(summary)
    md_path.write_text(md_content)

    return summary


def generate_error_markdown(summary: dict[str, Any]) -> str:
    """Generate Markdown error summary.

    Args:
        summary: Error summary dictionary

    Returns:
        Markdown formatted report
    """
    lines = [
        "# Error Summary",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        f"**Total Errors:** {summary.get('total_errors', 0)}",
        "",
    ]

    if summary.get("errors_by_type"):
        lines.append("## Errors by Type")
        lines.append("")
        for error_type, count in summary["errors_by_type"].items():
            lines.append(f"- **{error_type}:** {count}")
        lines.append("")

    if summary.get("errors"):
        lines.append("## Error Details")
        lines.append("")
        for i, error in enumerate(summary["errors"][:10], 1):  # Limit to first 10
            lines.append(f"### Error {i}")
            lines.append(f"- **Type:** {error.get('type', 'unknown')}")
            lines.append(f"- **Message:** {error.get('message', 'N/A')}")
            if error.get("file"):
                lines.append(f"- **File:** {error.get('file')}")
            if error.get("suggestions"):
                lines.append("- **Suggestions:**")
                for suggestion in error.get("suggestions", []):
                    lines.append(f"  - {suggestion}")
            lines.append("")

        if len(summary["errors"]) > 10:
            lines.append(f"*... and {len(summary['errors']) - 10} more errors*")

    return "\n".join(lines)
