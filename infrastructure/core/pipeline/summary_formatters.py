"""Pipeline summary formatting — text, JSON, and HTML output.

Extracted from summary.py to keep each module under 300 LOC.
These formatters are used by PipelineSummaryGenerator and should not
be imported directly by callers — use summary.py as the entry point.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.files.inventory import FileInventoryManager
from infrastructure.core.logging.helpers import format_duration
from infrastructure.core.pipeline.summary_helpers import (
    extract_project_name_from_path,
    find_base_output_dir,
    format_stage_result,
    get_final_log_path,
    stage_result_to_dict,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.core.pipeline.summary import PipelineSummary


def format_text_summary(
    summary: PipelineSummary,
    file_inventory_manager: FileInventoryManager,
) -> str:
    """Format summary as text output.

    Args:
        summary: Pipeline summary
        file_inventory_manager: Manager for file inventory reports

    Returns:
        Text formatted summary
    """
    lines = []

    # Header
    lines.append("")
    lines.append("PIPELINE SUMMARY")
    lines.append("")
    if summary.failed_stages:
        failed_names = ", ".join(r.stage_name for r in summary.failed_stages)
        lines.append(f"Pipeline completed with failures: {failed_names}")
    else:
        lines.append("All stages completed successfully!")

    # Log file info
    log_file_final = summary.log_file
    log_path_changed = False
    if summary.log_file:
        log_file_final = get_final_log_path(summary.log_file)
        log_path_changed = str(summary.log_file) != str(log_file_final)
        lines.append(f"Full pipeline log: {summary.log_file}")
        if log_path_changed:
            lines.append(f"  (Will be available at: {log_file_final} after copy stage)")

    lines.append("")
    lines.append("Stage Results:")

    # Stage results
    executed_stages = summary.executed_stages

    for result in summary.stage_results:
        stage_display = format_stage_result(
            result, summary.total_duration, summary.skip_infra
        )
        lines.append(f"  {stage_display}")

    lines.append("")
    lines.append("Performance Metrics:")
    lines.append(f"  Total Execution Time: {summary.total_duration:.1f}s")

    if executed_stages:
        avg_time = sum(r.duration for r in executed_stages) / len(executed_stages)
        lines.append(f"  Average Stage Time: {avg_time:.1f}s")

    if summary.slowest_stage:
        slowest_pct = (summary.slowest_stage.duration * 100) / summary.total_duration
        lines.append(
            f"  Slowest Stage: Stage {summary.slowest_stage.stage_num} - {summary.slowest_stage.stage_name} "  # noqa: E501
            f"({format_duration(summary.slowest_stage.duration)}, {slowest_pct:.0f}%)"
        )

    if summary.fastest_stage:
        lines.append(
            f"  Fastest Stage: Stage {summary.fastest_stage.stage_num} - {summary.fastest_stage.stage_name} "  # noqa: E501
            f"({format_duration(summary.fastest_stage.duration)})"
        )

    lines.append("")

    # File inventory
    if summary.inventory:
        base_dir = find_base_output_dir(summary.inventory)
        inventory_report = file_inventory_manager.generate_inventory_report(
            summary.inventory, "text", base_dir
        )
        lines.append(inventory_report)

        # Add notes about file locations
        if base_dir and "output" in str(base_dir):
            project_name = extract_project_name_from_path(base_dir)
            if project_name:
                lines.append(
                    f"Note: Files are also available in projects/{project_name}/output/ during development"  # noqa: E501
                )
        else:
            lines.append("Note: Files will be copied to output/ during copy stage")

    # Log file location (reuses log_file_final computed above)
    if summary.log_file:
        lines.append("")
        lines.append("Pipeline Log:")
        lines.append(f"  \u2022 Current: {summary.log_file}")
        if log_path_changed:
            lines.append(f"  \u2022 Final: {log_file_final} (after copy stage)")

    # Coverage reports
    coverage_dir = Path("htmlcov")
    if coverage_dir.exists():
        lines.append("")
        lines.append("Coverage Reports:")
        lines.append("  \u2022 HTML: htmlcov/index.html")

    lines.append("")
    lines.append("Pipeline complete - ready for deployment")
    lines.append("")

    return "\n".join(lines)


def format_json_summary(
    summary: PipelineSummary,
) -> str:
    """Format summary as JSON.

    Args:
        summary: Pipeline summary

    Returns:
        JSON formatted summary
    """
    data = {
        "total_duration": summary.total_duration,
        "total_duration_formatted": format_duration(summary.total_duration),
        "stages": [
            {
                "stage_num": r.stage_num,
                "stage_name": r.stage_name,
                "success": r.success,
                "duration": r.duration,
                "duration_formatted": format_duration(r.duration),
                "exit_code": r.exit_code,
                "error_message": r.error_message,
            }
            for r in summary.stage_results
        ],
        "performance": {
            "slowest_stage": stage_result_to_dict(summary.slowest_stage),
            "fastest_stage": stage_result_to_dict(summary.fastest_stage),
            "failed_stages": [stage_result_to_dict(r) for r in summary.failed_stages],
        },
        "files": {
            "count": len(summary.inventory),
            "inventory": [
                {
                    "path": str(entry.path),
                    "size": entry.size,
                    "size_formatted": entry.size_formatted,
                    "category": entry.category,
                    "modified": entry.modified,
                }
                for entry in summary.inventory
            ],
        },
    }

    if summary.log_file:
        data["log_file"] = str(summary.log_file)
        data["log_file_final"] = str(get_final_log_path(summary.log_file))

    return json.dumps(data, indent=2)


def format_html_summary(
    summary: PipelineSummary,
    file_inventory_manager: FileInventoryManager,
) -> str:
    """Format summary as HTML.

    Args:
        summary: Pipeline summary
        file_inventory_manager: Manager for file inventory reports

    Returns:
        HTML formatted summary
    """
    html_parts = []
    html_parts.append("<div class='pipeline-summary'>")
    html_parts.append("<h2>Pipeline Summary</h2>")
    if summary.failed_stages:
        failed_names = ", ".join(r.stage_name for r in summary.failed_stages)
        html_parts.append(
            f"<p class='error'>Pipeline completed with failures: {failed_names}</p>"
        )
    else:
        html_parts.append("<p class='success'>All stages completed successfully!</p>")

    if summary.log_file:
        log_file_final = get_final_log_path(summary.log_file)
        html_parts.append(f"<p><strong>Log file:</strong> {summary.log_file}")
        if str(summary.log_file) != str(log_file_final):
            html_parts.append(
                f"<br><em>(Will be available at: {log_file_final} after copy stage)</em></p>"
            )

    html_parts.append("<h3>Stage Results</h3>")
    html_parts.append("<ul class='stage-results'>")

    for result in summary.stage_results:
        css_class = "success" if result.success else "error"
        status_icon = "\u2713" if result.success else "\u2717"
        duration_formatted = format_duration(result.duration)
        percentage = (
            (result.duration * 100) / summary.total_duration
            if summary.total_duration > 0
            else 0
        )

        html_parts.append(f"<li class='{css_class}'>")
        html_parts.append(f"  {status_icon} Stage {result.stage_num}: {result.stage_name} ")
        html_parts.append(f"  ({duration_formatted}, {percentage:.0f}%)")
        if result.error_message:
            html_parts.append(f"  <br><em>Error: {result.error_message}</em>")
        html_parts.append("</li>")

    html_parts.append("</ul>")

    html_parts.append("<h3>Performance Metrics</h3>")
    html_parts.append("<ul class='performance-metrics'>")
    html_parts.append(f"<li>Total Execution Time: {summary.total_duration:.1f}s</li>")

    executed_stages = summary.executed_stages
    if executed_stages:
        avg_time = sum(r.duration for r in executed_stages) / len(executed_stages)
        html_parts.append(f"<li>Average Stage Time: {avg_time:.1f}s</li>")

    if summary.slowest_stage:
        slowest_pct = (summary.slowest_stage.duration * 100) / summary.total_duration
        html_parts.append(
            f"<li>Slowest Stage: {summary.slowest_stage.stage_name} "
            f"({format_duration(summary.slowest_stage.duration)}, {slowest_pct:.0f}%)</li>"
        )

    if summary.fastest_stage:
        html_parts.append(
            f"<li>Fastest Stage: {summary.fastest_stage.stage_name} "
            f"({format_duration(summary.fastest_stage.duration)})</li>"
        )

    html_parts.append("</ul>")

    # File inventory
    if summary.inventory:
        html_parts.append("<h3>Generated Files</h3>")
        base_dir = find_base_output_dir(summary.inventory)
        inventory_html = file_inventory_manager.generate_inventory_report(
            summary.inventory, "html", base_dir
        )
        html_parts.append(inventory_html)

    html_parts.append("</div>")

    return "\n".join(html_parts)
