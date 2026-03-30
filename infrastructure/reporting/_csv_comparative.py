"""CSV export: cross-project comparative analysis with rankings.

Computes per-metric percentiles, ranks, and performance ratings across all
projects in the executive summary.
"""

from __future__ import annotations

import csv
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting.executive_reporter import ExecutiveSummary
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

logger = get_logger(__name__)


def generate_comparative_analysis_csv(summary: ExecutiveSummary, output_dir: Path) -> Path:
    """Generate comparative analysis CSV with rankings and percentiles."""
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_path = organizer.get_output_path("comparative_analysis.csv", output_dir, FileType.CSV)

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "Project",
                "Metric_Category",
                "Metric_Name",
                "Value",
                "Unit",
                "Rank",
                "Percentile",
                "vs_Average",
                "Performance_Rating",
            ]
        )

        projects = summary.project_metrics
        if not projects:
            return csv_path

        # Calculate comparative statistics for each metric
        metrics_data = {
            "manuscript_words": [p.manuscript.total_words for p in projects],
            "manuscript_sections": [p.manuscript.sections for p in projects],
            "codebase_lines": [p.codebase.source_lines for p in projects],
            "pipeline_duration": [p.pipeline.total_duration for p in projects],
            "output_total": [p.outputs.total_outputs for p in projects],
        }

        # Generate comparative data for each project and metric
        for project in projects:
            _write_comparative_row(
                writer, project.name, "Manuscript", "Total_Words", "words",
                project.manuscript.total_words, metrics_data["manuscript_words"],
                higher_is_better=True,
            )
            _write_comparative_row(
                writer, project.name, "Manuscript", "Sections", "count",
                project.manuscript.sections, metrics_data["manuscript_sections"],
                higher_is_better=True,
            )
            _write_comparative_row(
                writer, project.name, "Codebase", "Source_Lines", "lines",
                project.codebase.source_lines, metrics_data["codebase_lines"],
                higher_is_better=True,
            )
            _write_comparative_row(
                writer, project.name, "Pipeline", "Duration", "seconds",
                project.pipeline.total_duration, metrics_data["pipeline_duration"],
                higher_is_better=False,
            )
            _write_comparative_row(
                writer, project.name, "Outputs", "Total_Files", "files",
                project.outputs.total_outputs, metrics_data["output_total"],
                higher_is_better=True,
            )

    logger.info(f"Comparative analysis CSV saved: {csv_path}")
    return csv_path


# ── Internal helpers ─────────────────────────────────────────────────────────


def _write_comparative_row(
    writer: csv.writer,  # type: ignore[type-arg]
    project_name: str,
    category: str,
    metric_name: str,
    unit: str,
    value: float,
    values_list: list[float],
    *,
    higher_is_better: bool,
) -> None:
    """Compute rank/percentile and write a single comparative row."""
    percentile, rank = _calculate_percentile_and_rank(value, values_list, higher_is_better)
    avg = sum(values_list) / len(values_list)
    vs_avg = ((value - avg) / avg * 100) if avg > 0 else 0

    writer.writerow(
        [
            project_name,
            category,
            metric_name,
            value,
            unit,
            rank,
            f"{percentile:.1f}%",
            f"{vs_avg:+.1f}%",
            _get_performance_rating(percentile, higher_is_better),
        ]
    )


def _calculate_percentile_and_rank(
    value: float, values_list: list[float], higher_is_better: bool = True
) -> tuple[float, int]:
    """Calculate percentile rank for a value in a list."""
    if not values_list:
        return 50, 1

    sorted_values = sorted(values_list, reverse=higher_is_better)
    try:
        rank = sorted_values.index(value) + 1
        percentile = (
            (len(values_list) - rank) / (len(values_list) - 1) * 100
            if len(values_list) > 1
            else 100
        )
    except ValueError:
        # Handle ties or missing values
        rank = (
            len([v for v in values_list if (v > value if higher_is_better else v < value)])
            + 1
        )
        percentile = (rank - 1) / len(values_list) * 100

    return percentile, rank


def _get_performance_rating(percentile: float, higher_is_better: bool = True) -> str:
    """Convert percentile to performance rating."""
    if higher_is_better:
        if percentile >= 80:
            return "Excellent"
        elif percentile >= 60:
            return "Good"
        elif percentile >= 40:
            return "Average"
        elif percentile >= 20:
            return "Below Average"
        else:
            return "Poor"
    else:
        # Lower is better (like duration)
        if percentile >= 80:
            return "Poor"
        elif percentile >= 60:
            return "Below Average"
        elif percentile >= 40:
            return "Average"
        elif percentile >= 20:
            return "Good"
        else:
            return "Excellent"
