"""CSV export: prioritized recommendations and aggregate data tables.

Contains the recommendation prioritizer and the bulk CSV data-table generator
(project metrics, aggregate metrics, health scores).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting.executive_reporter import ExecutiveSummary
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

logger = get_logger(__name__)


# ── Prioritized recommendations ─────────────────────────────────────────────


def generate_prioritized_recommendations_csv(summary: ExecutiveSummary, output_dir: Path) -> Path:
    """Generate prioritized recommendations CSV with impact and effort estimates."""
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_path = organizer.get_output_path(
        "recommendations_prioritized.csv",
        output_dir,
        FileType.CSV,
    )

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "Priority_Level",
                "Priority_Score",
                "Category",
                "Recommendation",
                "Impact_Level",
                "Effort_Level",
                "Time_Estimate",
                "Affected_Projects",
                "Rationale",
                "Next_Steps",
            ]
        )

        # Categorize recommendations with priority scoring
        recommendations_data = []

        for rec in summary.recommendations:
            item = _classify_recommendation(rec, summary)
            recommendations_data.append(item)

        # Sort by priority score (highest first)
        recommendations_data.sort(key=lambda x: x["priority_score"], reverse=True)

        # Write sorted recommendations
        for item in recommendations_data:
            writer.writerow(
                [
                    item["priority_level"],
                    item["priority_score"],
                    item["category"],
                    item["rec"],
                    item["impact_level"],
                    item["effort_level"],
                    item["time_estimate"],
                    item["affected_projects"],
                    f"Priority {item['priority_level']} - {item['impact_level']} impact",
                    item["next_steps"],
                ]
            )

    logger.info(f"Prioritized recommendations CSV saved: {csv_path}")
    return csv_path


def _classify_recommendation(rec: str, summary: ExecutiveSummary) -> dict[str, Any]:
    """Classify a single recommendation string into priority/category metadata."""
    priority_score = 1
    priority_level = "Low"
    impact_level = "Low"
    effort_level = "Low"
    time_estimate = "1-2 hours"
    category = "General"
    affected_projects = "All"
    next_steps = "Review and implement as appropriate"

    if any(
        keyword in rec.lower() for keyword in ["critical", "immediate", "failing", "broken"]
    ):
        priority_score = 5
        priority_level = "High"
        impact_level = "High"
        effort_level = "Medium"
        time_estimate = "1-2 days"
    elif any(keyword in rec.lower() for keyword in ["below", "improve", "consider"]):
        priority_score = 3
        priority_level = "Medium"
        impact_level = "Medium"
        effort_level = "Low"
        time_estimate = "4-8 hours"

    # Categorize by content
    if "test" in rec.lower():
        category = "Testing"
    elif "coverage" in rec.lower():
        category = "Code Quality"
    elif "manuscript" in rec.lower() or "research" in rec.lower():
        category = "Content"
    elif "pipeline" in rec.lower():
        category = "Performance"
    elif "output" in rec.lower():
        category = "Deliverables"

    # Extract affected projects from recommendation text
    if "project," in rec.lower():
        affected_projects = "Multiple"
    elif any(proj.name in rec for proj in summary.project_metrics):
        affected_projects = next(
            (proj.name for proj in summary.project_metrics if proj.name in rec),
            "All",
        )

    return {
        "rec": rec,
        "priority_score": priority_score,
        "priority_level": priority_level,
        "category": category,
        "impact_level": impact_level,
        "effort_level": effort_level,
        "time_estimate": time_estimate,
        "affected_projects": affected_projects,
        "next_steps": next_steps,
    }


# ── Bulk CSV data tables ────────────────────────────────────────────────────


def generate_csv_data_tables(summary: ExecutiveSummary, output_dir: Path) -> dict[str, Path]:
    """Generate CSV data tables for dashboard data export.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved CSV file paths
    """
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_files: dict[str, Path] = {}

    csv_files["metrics"] = _write_project_metrics_csv(summary, output_dir, organizer)
    csv_files["aggregates"] = _write_aggregate_metrics_csv(summary, output_dir, organizer)
    csv_files["health"] = _write_health_scores_csv(summary, output_dir, organizer)

    return csv_files


def _write_project_metrics_csv(
    summary: ExecutiveSummary, output_dir: Path, organizer: OutputOrganizer
) -> Path:
    """Write per-project metrics CSV."""
    from infrastructure.reporting.executive_reporter import calculate_project_health_score

    metrics_csv = organizer.get_output_path("project_metrics.csv", output_dir, FileType.CSV)
    with open(metrics_csv, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                "Project",
                "Health_Score",
                "Health_Grade",
                "Manuscript_Words",
                "Manuscript_Sections",
                "Manuscript_Equations",
                "Manuscript_Figures",
                "Test_Total",
                "Test_Passed",
                "Test_Failed",
                "Test_Coverage_Pct",
                "Test_Execution_Time",
                "Pipeline_Duration",
                "Pipeline_Stages_Passed",
                "Pipeline_Bottleneck_Stage",
                "Pipeline_Bottleneck_Duration",
                "Output_PDFs",
                "Output_PDF_Size_MB",
                "Output_Figures",
                "Output_Slides",
                "Output_Web",
                "Output_Total",
            ]
        )

        for project in summary.project_metrics:
            health = calculate_project_health_score(project)
            writer.writerow(
                [
                    project.name,
                    health["percentage"],
                    health["grade"],
                    project.manuscript.total_words,
                    project.manuscript.sections,
                    project.manuscript.equations,
                    project.manuscript.figures,
                    project.tests.total_tests,
                    project.tests.passed,
                    project.tests.failed,
                    project.tests.coverage_percent,
                    project.tests.execution_time,
                    project.pipeline.total_duration,
                    project.pipeline.stages_passed,
                    project.pipeline.bottleneck_stage,
                    project.pipeline.bottleneck_duration,
                    project.outputs.pdf_files,
                    project.outputs.pdf_size_mb,
                    project.outputs.figures,
                    project.outputs.slides,
                    project.outputs.web_outputs,
                    project.outputs.total_outputs,
                ]
            )

    logger.info(f"Generated CSV metrics table: {metrics_csv}")
    return metrics_csv


def _write_aggregate_metrics_csv(
    summary: ExecutiveSummary, output_dir: Path, organizer: OutputOrganizer
) -> Path:
    """Write aggregate (cross-project) metrics CSV."""
    aggregate_csv = organizer.get_output_path("aggregate_metrics.csv", output_dir, FileType.CSV)
    with open(aggregate_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Metric", "Value", "Unit"])

        agg = summary.aggregate_metrics

        # Manuscript aggregates
        manuscript = agg.get("manuscript", {})
        writer.writerow(["Manuscript", "Total_Words", manuscript.get("total_words", 0), "words"])
        writer.writerow(
            ["Manuscript", "Total_Sections", manuscript.get("total_sections", 0), "sections"]
        )
        writer.writerow(
            ["Manuscript", "Total_Equations", manuscript.get("total_equations", 0), "equations"]
        )
        writer.writerow(
            ["Manuscript", "Total_Figures", manuscript.get("total_figures", 0), "figures"]
        )
        writer.writerow(
            ["Manuscript", "Total_References", manuscript.get("total_references", 0), "references"]
        )

        # Test aggregates
        tests = agg.get("tests", {})
        writer.writerow(["Tests", "Total_Tests", tests.get("total_tests", 0), "tests"])
        writer.writerow(["Tests", "Total_Passed", tests.get("total_passed", 0), "tests"])
        writer.writerow(["Tests", "Total_Failed", tests.get("total_failed", 0), "tests"])
        writer.writerow(["Tests", "Average_Coverage", tests.get("average_coverage", 0), "percent"])
        writer.writerow(
            ["Tests", "Total_Execution_Time", tests.get("total_execution_time", 0), "seconds"]
        )

        # Pipeline aggregates
        pipeline = agg.get("pipeline", {})
        writer.writerow(
            ["Pipeline", "Total_Duration", pipeline.get("total_duration", 0), "seconds"]
        )
        writer.writerow(
            ["Pipeline", "Average_Duration", pipeline.get("average_duration", 0), "seconds"]
        )
        writer.writerow(
            ["Pipeline", "Total_Stages_Passed", pipeline.get("total_stages_passed", 0), "stages"]
        )
        writer.writerow(
            ["Pipeline", "Total_Stages_Failed", pipeline.get("total_stages_failed", 0), "stages"]
        )

        # Output aggregates
        outputs = agg.get("outputs", {})
        writer.writerow(["Outputs", "Total_PDFs", outputs.get("total_pdfs", 0), "files"])
        writer.writerow(["Outputs", "Total_Size_MB", outputs.get("total_size_mb", 0), "MB"])
        writer.writerow(["Outputs", "Total_Figures", outputs.get("total_figures", 0), "files"])
        writer.writerow(["Outputs", "Total_Slides", outputs.get("total_slides", 0), "files"])
        writer.writerow(["Outputs", "Total_Web", outputs.get("total_web", 0), "files"])

    logger.info(f"Generated CSV aggregates table: {aggregate_csv}")
    return aggregate_csv


def _write_health_scores_csv(
    summary: ExecutiveSummary, output_dir: Path, organizer: OutputOrganizer
) -> Path:
    """Write per-project health scores CSV."""
    health_csv = organizer.get_output_path("health_scores.csv", output_dir, FileType.CSV)
    with open(health_csv, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                "Project",
                "Overall_Score",
                "Overall_Percentage",
                "Overall_Grade",
                "Overall_Status",
                "Test_Coverage_Score",
                "Test_Coverage_Grade",
                "Test_Failures_Score",
                "Test_Failures_Grade",
                "Manuscript_Size_Score",
                "Manuscript_Size_Grade",
                "Outputs_Score",
                "Outputs_Grade",
            ]
        )

        for project_name, health in summary.health_scores.items():
            writer.writerow(
                [
                    project_name,
                    health["score"],
                    health["percentage"],
                    health["grade"],
                    health["status"],
                    health["factors"]["test_coverage"]["score"],
                    health["factors"]["test_coverage"]["grade"],
                    health["factors"]["test_failures"]["score"],
                    health["factors"]["test_failures"]["grade"],
                    health["factors"]["manuscript_size"]["score"],
                    health["factors"]["manuscript_size"]["grade"],
                    health["factors"]["outputs"]["score"],
                    health["factors"]["outputs"]["grade"],
                ]
            )

    logger.info(f"Generated CSV health scores table: {health_csv}")
    return health_csv
