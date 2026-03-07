"""Multi-project reporting orchestration.

Convenience functions for multi-project executive reporting and per-run summaries.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.multi_project import MultiProjectResult
try:
    from infrastructure.reporting.dashboard_generator import generate_all_dashboards
    _DASHBOARD_AVAILABLE = True
except ImportError:
    _DASHBOARD_AVAILABLE = False
from infrastructure.reporting.executive_reporter import (
    generate_executive_summary,
    save_executive_summary,
)

logger = get_logger(__name__)


def generate_multi_project_report(
    repo_root: Path, project_names: list[str], output_dir: Path
) -> dict[str, Path]:
    """Orchestrate complete multi-project reporting workflow.

    This is a convenience function that runs the full executive reporting pipeline:
    1. Generate executive summary with metrics collection
    2. Save summary reports (JSON, HTML, Markdown)
    3. Generate visual dashboards (PNG, PDF, HTML)

    Args:
        repo_root: Repository root path
        project_names: List of project names to include in report
        output_dir: Directory to save all reports and dashboards

    Returns:
        Dictionary mapping file types to saved file paths
    """
    logger.info(f"Starting multi-project reporting for {len(project_names)} projects...")

    all_files = {}

    try:
        summary = generate_executive_summary(repo_root, project_names)
        summary_files = save_executive_summary(summary, output_dir)
        all_files.update(summary_files)

        if _DASHBOARD_AVAILABLE:
            dashboard_files = generate_all_dashboards(summary, output_dir)
            all_files.update(dashboard_files)

        logger.info(f"Multi-project reporting complete. Generated {len(all_files)} files.")
        for file_type, path in all_files.items():
            logger.info(f"  {file_type.upper()}: {path.name}")

        return all_files

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Multi-project reporting failed: {e}")
        raise


def generate_multi_project_summary_report(
    result: MultiProjectResult, projects: list[Any], output_dir: Path
) -> dict[str, Path]:
    """Generate comprehensive multi-project summary report.

    Args:
        result: Multi-project execution result
        projects: List of project objects
        output_dir: Directory to save reports

    Returns:
        Dictionary mapping format names to saved file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    total_projects_count = len(projects)

    summary: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "total_projects": total_projects_count,
        "successful_projects": result.successful_projects,
        "failed_projects": result.failed_projects,
        "total_duration": result.total_duration,
        "infra_test_duration": result.infra_test_duration,
        "projects": {},
        "performance_analysis": {},
        "error_aggregation": {},
        "recommendations": [],
    }

    project_names = [p.name for p in projects]
    raw_results = result.project_results
    project_results = raw_results if isinstance(raw_results, dict) else {}

    for proj_name in project_names:
        raw = project_results.get(proj_name, [])
        proj_result = raw if isinstance(raw, list) else []

        all_success = len(proj_result) > 0 and all(stage.success for stage in proj_result)
        total_duration = sum(stage.duration for stage in proj_result)
        errors = [stage.error_message for stage in proj_result if stage.error_message]

        summary["projects"][proj_name] = {
            "success": all_success,
            "duration": total_duration,
            "stages_completed": len(proj_result),
            "errors": errors,
        }

    if project_results:
        try:
            durations = []
            for proj_name, proj_data in summary["projects"].items():
                if isinstance(proj_data, dict) and proj_data.get("duration", 0) > 0:
                    durations.append(proj_data["duration"])

            if durations:
                proj_dur = [
                    (n, d["duration"])
                    for n, d in summary["projects"].items()
                    if isinstance(d, dict) and d.get("duration", 0) > 0
                ]
                summary["performance_analysis"] = {
                    "slowest_project": max(proj_dur, key=lambda x: x[1])[0] if proj_dur else None,
                    "fastest_project": min(proj_dur, key=lambda x: x[1])[0] if proj_dur else None,
                    "average_duration": sum(durations) / len(durations),
                    "total_pipeline_time": sum(durations),
                }
        except (TypeError, KeyError, IndexError, ZeroDivisionError) as e:
            logger.warning(f"Error calculating performance analysis: {e}")
            summary["performance_analysis"] = {}

    all_errors = []
    for proj_name, proj_data in summary["projects"].items():
        for err in proj_data.get("errors", []):
            all_errors.append({"project": proj_name, "error": err})
    summary["error_aggregation"] = {
        "total_errors": len(all_errors),
        "errors_by_project": {
            proj: len(summary["projects"].get(proj, {}).get("errors", []))
            for proj in project_names
        },
    }

    if result.failed_projects > 0:
        summary["recommendations"].append(
            {
                "priority": "high",
                "action": "Review failed projects",
                "details": f"{result.failed_projects} project(s) failed execution",
            }
        )

    if summary["performance_analysis"].get("average_duration", 0) > 300:
        summary["recommendations"].append(
            {
                "priority": "medium",
                "action": "Consider performance optimization",
                "details": f"Average project execution time: {summary['performance_analysis']['average_duration']:.1f}s",  # noqa: E501
            }
        )

    saved_files: dict[str, Path] = {}

    json_file = output_dir / "multi_project_summary.json"
    try:
        json_file.write_text(json.dumps(summary, indent=2))
        saved_files["json"] = json_file
        logger.info(f"Multi-project summary saved: {json_file}")
    except OSError as e:
        logger.error(f"Failed to write JSON summary {json_file}: {e}")
        raise

    md_file = output_dir / "multi_project_summary.md"
    try:
        md_file.write_text(_format_multi_project_summary_markdown(summary))
        saved_files["markdown"] = md_file
        logger.info(f"Multi-project summary saved: {md_file}")
    except OSError as e:
        logger.error(f"Failed to write Markdown summary {md_file}: {e}")
        raise

    return saved_files


def _format_multi_project_summary_markdown(summary: dict[str, Any]) -> str:
    """Format multi-project summary as markdown."""
    lines = [
        "# Multi-Project Execution Summary",
        "",
        f"**Generated:** {summary['timestamp']}",
        "",
        "## Overview",
        "",
        f"- **Total Projects:** {summary['total_projects']}",
        f"- **Successful:** {summary['successful_projects']}",
        f"- **Failed:** {summary['failed_projects']}",
        f"- **Total Duration:** {summary['total_duration']:.1f}s",
        "",
    ]

    if summary.get("infra_test_duration", 0) > 0:
        lines.extend([f"- **Infrastructure Tests:** {summary['infra_test_duration']:.1f}s", ""])

    lines.extend(["## Project Results", ""])

    for proj_name, proj_data in summary["projects"].items():
        status_icon = "✅" if proj_data["success"] else "❌"
        lines.append(f"### {status_icon} {proj_name}")
        lines.append(f"- **Status:** {'Success' if proj_data['success'] else 'Failed'}")
        lines.append(f"- **Duration:** {proj_data['duration']:.1f}s")
        lines.append(f"- **Stages Completed:** {proj_data['stages_completed']}")

        if proj_data["errors"]:
            lines.append("- **Errors:**")
            for err in proj_data["errors"][:3]:
                lines.append(f"  - {err}")
            if len(proj_data["errors"]) > 3:
                lines.append(f"  - ... and {len(proj_data['errors']) - 3} more")
        lines.append("")

    if summary.get("performance_analysis"):
        perf = summary["performance_analysis"]
        lines.extend(
            [
                "## Performance Analysis",
                "",
                f"- **Slowest Project:** {perf.get('slowest_project', 'N/A')}",
                f"- **Fastest Project:** {perf.get('fastest_project', 'N/A')}",
                f"- **Average Duration:** {perf.get('average_duration', 0):.1f}s",
                f"- **Total Pipeline Time:** {perf.get('total_pipeline_time', 0):.1f}s",
                "",
            ]
        )

    if summary.get("error_aggregation"):
        err_agg = summary["error_aggregation"]
        lines.extend(
            [
                "## Error Summary",
                "",
                f"- **Total Errors:** {err_agg['total_errors']}",
                "",
            ]
        )

        if err_agg.get("errors_by_project"):
            lines.append("**Errors by Project:**")
            for proj, count in err_agg["errors_by_project"].items():
                if count > 0:
                    lines.append(f"- {proj}: {count} error(s)")
            lines.append("")

    if summary.get("recommendations"):
        lines.extend(["## Recommendations", ""])
        for rec in summary["recommendations"]:
            lines.append(f"### {rec['priority'].upper()}: {rec['action']}")
            lines.append(f"{rec['details']}")
            lines.append("")

    return "\n".join(lines)
