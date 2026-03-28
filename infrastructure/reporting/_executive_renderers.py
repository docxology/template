"""Orchestration for executive summary generation and persistence.

Provides the top-level ``generate_executive_summary`` and
``save_executive_summary`` functions that wire together metric
collection, analysis, and report rendering.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer
from infrastructure.reporting.pipeline_io import _atomic_write_json, _atomic_write_text

from ._executive_analysis import (
    generate_aggregate_metrics,
    generate_comparative_tables,
)
from ._executive_collectors import collect_project_metrics
from ._executive_health import (
    calculate_project_health_score,
    generate_recommendations,
)
from ._executive_models import ExecutiveSummary
from ._executive_report_formats import (
    generate_html_report,
    generate_markdown_report,
)

logger = get_logger(__name__)


def generate_executive_summary(repo_root: Path, project_names: list[str]) -> ExecutiveSummary:
    """Generate complete executive summary for all projects.

    Args:
        repo_root: Repository root path
        project_names: List of project names to include

    Returns:
        ExecutiveSummary instance
    """
    logger.info(f"Generating executive summary for {len(project_names)} project(s)")

    # Collect metrics for all projects
    project_metrics = []
    for project_name in project_names:
        try:
            metrics = collect_project_metrics(repo_root, project_name)
            project_metrics.append(metrics)
        except (OSError, json.JSONDecodeError, KeyError, ValueError, UnicodeDecodeError) as e:  # noqa: BLE001 — skip failed projects; collect remaining
            logger.error(f"Error collecting metrics for {project_name}: {e}")

    # Generate aggregates, comparisons, recommendations
    aggregates = generate_aggregate_metrics(project_metrics)
    comparatives = generate_comparative_tables(project_metrics)
    recommendations = generate_recommendations(project_metrics)

    # Calculate health scores for all projects
    health_scores = {p.name: calculate_project_health_score(p) for p in project_metrics}

    summary = ExecutiveSummary(
        timestamp=datetime.now().isoformat(),
        total_projects=len(project_metrics),
        aggregate_metrics=aggregates,
        project_metrics=project_metrics,
        health_scores=health_scores,
        comparative_tables=comparatives,
        recommendations=recommendations,
    )

    logger.info("Executive summary generated successfully")
    return summary


def save_executive_summary(summary: ExecutiveSummary, output_dir: Path) -> dict[str, Path]:
    """Save executive summary in multiple formats.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary mapping format to saved file path
    """
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files: dict[str, Path] = {}

    # Save JSON (machine-readable)
    json_path = organizer.get_output_path("consolidated_report.json", output_dir, FileType.JSON)
    _atomic_write_json(json_path, asdict(summary), default=str)
    saved_files["json"] = json_path
    logger.info(f"Saved JSON report: {json_path}")

    # Save Markdown (human-readable)
    md_path = organizer.get_output_path("consolidated_report.md", output_dir, FileType.MARKDOWN)
    _atomic_write_text(md_path, generate_markdown_report(summary))
    saved_files["markdown"] = md_path
    logger.info(f"Saved Markdown report: {md_path}")

    # Save HTML (styled)
    html_path = organizer.get_output_path("consolidated_report.html", output_dir, FileType.HTML)
    _atomic_write_text(html_path, generate_html_report(summary))
    saved_files["html"] = html_path
    logger.info(f"Saved HTML report: {html_path}")

    return saved_files
