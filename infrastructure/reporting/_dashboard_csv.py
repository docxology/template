"""CSV data export functions for executive reporting dashboards.

Extracted from ``_dashboard_matplotlib.py`` — detailed project breakdowns,
comparative analysis, and prioritized recommendations.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting.executive_reporter import ExecutiveSummary, ProjectMetrics
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

logger = get_logger(__name__)

def generate_detailed_project_breakdown_csv(summary: ExecutiveSummary, output_dir: Path) -> Path:
    """Generate detailed project breakdown CSV with all metrics and explanations."""
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_path = organizer.get_output_path("detailed_project_breakdown.csv", output_dir, FileType.CSV)

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header with explanations
        writer.writerow(
            [
                "Project",
                "Category",
                "Metric",
                "Value",
                "Unit",
                "Description",
                "Health_Impact",
                "Recommended_Range",
            ]
        )

        for project in summary.project_metrics:
            # Manuscript metrics
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Total_Words",
                    project.manuscript.total_words,
                    "words",
                    "Total words in manuscript sections",
                    "High",
                    "1000-20000 words",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Sections",
                    project.manuscript.sections,
                    "count",
                    "Number of manuscript sections",
                    "Medium",
                    "3-20 sections",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Equations",
                    project.manuscript.equations,
                    "count",
                    "Mathematical equations in manuscript",
                    "Low",
                    "0-50 equations",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Figures",
                    project.manuscript.figures,
                    "count",
                    "Figure references in manuscript",
                    "Low",
                    "0-20 figures",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "References",
                    project.manuscript.references,
                    "count",
                    "Citation references",
                    "Medium",
                    "10-200 references",
                ]
            )

            # Codebase metrics
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Source_Files",
                    project.codebase.source_files,
                    "files",
                    "Python source files",
                    "Medium",
                    "1-20 files",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Source_Lines",
                    project.codebase.source_lines,
                    "lines",
                    "Lines of source code",
                    "Medium",
                    "100-5000 lines",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Methods",
                    project.codebase.methods,
                    "count",
                    "Function/method definitions",
                    "Medium",
                    "10-500 methods",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Classes",
                    project.codebase.classes,
                    "count",
                    "Class definitions",
                    "Low",
                    "0-50 classes",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Scripts",
                    project.codebase.scripts,
                    "files",
                    "Analysis scripts",
                    "Low",
                    "0-10 scripts",
                ]
            )

            # Test metrics
            writer.writerow(
                [
                    project.name,
                    "Testing",
                    "Test_Files",
                    project.tests.test_files,
                    "files",
                    "Test files discovered",
                    "High",
                    "1+ files",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Testing",
                    "Total_Tests",
                    project.tests.total_tests,
                    "tests",
                    "Total test cases (-1 = unavailable)",
                    "High",
                    "10-1000 tests",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Testing",
                    "Coverage_Percent",
                    project.tests.coverage_percent,
                    "percent",
                    "Code coverage percentage",
                    "High",
                    "90-100%",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Testing",
                    "Execution_Time",
                    project.tests.execution_time,
                    "seconds",
                    "Test execution time",
                    "Low",
                    "1-300 seconds",
                ]
            )

            # Output metrics
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "PDF_Files",
                    project.outputs.pdf_files,
                    "files",
                    "Generated PDF documents",
                    "High",
                    "1+ files",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "PDF_Size_MB",
                    f"{project.outputs.pdf_size_mb:.2f}",
                    "MB",
                    "Total PDF file size",
                    "Low",
                    "0.1-10 MB",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "Figures",
                    project.outputs.figures,
                    "files",
                    "Generated figure files",
                    "Medium",
                    "0-50 figures",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "Slides",
                    project.outputs.slides,
                    "files",
                    "Generated slide files",
                    "Medium",
                    "0-20 slide sets",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "Web_Outputs",
                    project.outputs.web_outputs,
                    "files",
                    "Generated web files",
                    "Medium",
                    "0-20 web files",
                ]
            )

            # Pipeline metrics
            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Total_Duration",
                    project.pipeline.total_duration,
                    "seconds",
                    "Total pipeline execution time",
                    "Medium",
                    "60-600 seconds",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Stages_Passed",
                    project.pipeline.stages_passed,
                    "stages",
                    "Pipeline stages completed successfully",
                    "High",
                    "6 stages",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Bottleneck_Stage",
                    project.pipeline.bottleneck_stage,
                    "stage_name",
                    "Slowest pipeline stage",
                    "Medium",
                    "Varies by project",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Bottleneck_Duration",
                    project.pipeline.bottleneck_duration,
                    "seconds",
                    "Time spent in bottleneck stage",
                    "Medium",
                    "10-300 seconds",
                ]
            )

    logger.info(f"Detailed project breakdown CSV saved: {csv_path}")
    return csv_path


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

        def calculate_percentile_and_rank(value: float, values_list: list[float], higher_is_better: bool = True) -> tuple[float, int]:
            """Calculate percentile rank for a value in a list."""
            if not values_list:
                return (
                    50,
                    len([v for v in values_list if (v > value if higher_is_better else v < value)])
                    + 1,
                )

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

        def get_performance_rating(percentile: float, higher_is_better: bool = True) -> str:
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

        # Generate comparative data for each project and metric
        for project in projects:
            # Manuscript metrics
            percentile, rank = calculate_percentile_and_rank(
                project.manuscript.total_words,
                metrics_data["manuscript_words"],
                higher_is_better=True,
            )
            avg = sum(metrics_data["manuscript_words"]) / len(metrics_data["manuscript_words"])
            vs_avg = ((project.manuscript.total_words - avg) / avg * 100) if avg > 0 else 0

            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Total_Words",
                    project.manuscript.total_words,
                    "words",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, True),
                ]
            )

            percentile, rank = calculate_percentile_and_rank(
                project.manuscript.sections,
                metrics_data["manuscript_sections"],
                higher_is_better=True,
            )
            avg = sum(metrics_data["manuscript_sections"]) / len(
                metrics_data["manuscript_sections"]
            )
            vs_avg = ((project.manuscript.sections - avg) / avg * 100) if avg > 0 else 0

            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Sections",
                    project.manuscript.sections,
                    "count",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, True),
                ]
            )

            # Codebase metrics
            percentile, rank = calculate_percentile_and_rank(
                project.codebase.source_lines,
                metrics_data["codebase_lines"],
                higher_is_better=True,
            )
            avg = sum(metrics_data["codebase_lines"]) / len(metrics_data["codebase_lines"])
            vs_avg = ((project.codebase.source_lines - avg) / avg * 100) if avg > 0 else 0

            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Source_Lines",
                    project.codebase.source_lines,
                    "lines",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, True),
                ]
            )

            # Pipeline metrics
            percentile, rank = calculate_percentile_and_rank(
                project.pipeline.total_duration,
                metrics_data["pipeline_duration"],
                higher_is_better=False,
            )
            avg = sum(metrics_data["pipeline_duration"]) / len(metrics_data["pipeline_duration"])
            vs_avg = ((project.pipeline.total_duration - avg) / avg * 100) if avg > 0 else 0

            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Duration",
                    project.pipeline.total_duration,
                    "seconds",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, False),
                ]
            )

            # Output metrics
            percentile, rank = calculate_percentile_and_rank(
                project.outputs.total_outputs,
                metrics_data["output_total"],
                higher_is_better=True,
            )
            avg = sum(metrics_data["output_total"]) / len(metrics_data["output_total"])
            vs_avg = ((project.outputs.total_outputs - avg) / avg * 100) if avg > 0 else 0

            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "Total_Files",
                    project.outputs.total_outputs,
                    "files",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, True),
                ]
            )

    logger.info(f"Comparative analysis CSV saved: {csv_path}")
    return csv_path


def generate_prioritized_recommendations_csv(summary: ExecutiveSummary, output_dir: Path) -> Path:
    """Generate prioritized recommendations CSV with impact and effort estimates."""
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_path = organizer.get_output_path(
        "recommendations_prioritized.csv",  # type: ignore[arg-type]
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
            # Determine priority based on keywords and content
            priority_score = 1  # Default low
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
                # Parse project names from recommendation
                affected_projects = "Multiple"
            elif any(proj.name in rec for proj in summary.project_metrics):
                affected_projects = next(
                    (proj.name for proj in summary.project_metrics if proj.name in rec),
                    "All",
                )

            recommendations_data.append(
                {
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
            )

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


def generate_csv_data_tables(summary: ExecutiveSummary, output_dir: Path) -> dict[str, Path]:
    """Generate CSV data tables for dashboard data export.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved CSV file paths
    """
    import csv

    from infrastructure.reporting.executive_reporter import calculate_project_health_score

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_files = {}

    # Project metrics CSV
    organizer = OutputOrganizer()
    metrics_csv = organizer.get_output_path("project_metrics.csv", output_dir, FileType.CSV)
    with open(metrics_csv, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
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

        # Data rows
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

    csv_files["metrics"] = metrics_csv
    logger.info(f"Generated CSV metrics table: {metrics_csv}")

    # Aggregate metrics CSV
    aggregate_csv = organizer.get_output_path("aggregate_metrics.csv", output_dir, FileType.CSV)
    with open(aggregate_csv, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["Category", "Metric", "Value", "Unit"])

        agg = summary.aggregate_metrics

        # Manuscript aggregates
        manuscript = agg.get("manuscript", {})
        writer.writerow(["Manuscript", "Total_Words", manuscript.get("total_words", 0), "words"])
        writer.writerow(
            [
                "Manuscript",
                "Total_Sections",
                manuscript.get("total_sections", 0),
                "sections",
            ]
        )
        writer.writerow(
            [
                "Manuscript",
                "Total_Equations",
                manuscript.get("total_equations", 0),
                "equations",
            ]
        )
        writer.writerow(
            [
                "Manuscript",
                "Total_Figures",
                manuscript.get("total_figures", 0),
                "figures",
            ]
        )
        writer.writerow(
            [
                "Manuscript",
                "Total_References",
                manuscript.get("total_references", 0),
                "references",
            ]
        )

        # Test aggregates
        tests = agg.get("tests", {})
        writer.writerow(["Tests", "Total_Tests", tests.get("total_tests", 0), "tests"])
        writer.writerow(["Tests", "Total_Passed", tests.get("total_passed", 0), "tests"])
        writer.writerow(["Tests", "Total_Failed", tests.get("total_failed", 0), "tests"])
        writer.writerow(["Tests", "Average_Coverage", tests.get("average_coverage", 0), "percent"])
        writer.writerow(
            [
                "Tests",
                "Total_Execution_Time",
                tests.get("total_execution_time", 0),
                "seconds",
            ]
        )

        # Pipeline aggregates
        pipeline = agg.get("pipeline", {})
        writer.writerow(
            ["Pipeline", "Total_Duration", pipeline.get("total_duration", 0), "seconds"]
        )
        writer.writerow(
            [
                "Pipeline",
                "Average_Duration",
                pipeline.get("average_duration", 0),
                "seconds",
            ]
        )
        writer.writerow(
            [
                "Pipeline",
                "Total_Stages_Passed",
                pipeline.get("total_stages_passed", 0),
                "stages",
            ]
        )
        writer.writerow(
            [
                "Pipeline",
                "Total_Stages_Failed",
                pipeline.get("total_stages_failed", 0),
                "stages",
            ]
        )

        # Output aggregates
        outputs = agg.get("outputs", {})
        writer.writerow(["Outputs", "Total_PDFs", outputs.get("total_pdfs", 0), "files"])
        writer.writerow(["Outputs", "Total_Size_MB", outputs.get("total_size_mb", 0), "MB"])
        writer.writerow(["Outputs", "Total_Figures", outputs.get("total_figures", 0), "files"])
        writer.writerow(["Outputs", "Total_Slides", outputs.get("total_slides", 0), "files"])
        writer.writerow(["Outputs", "Total_Web", outputs.get("total_web", 0), "files"])

    csv_files["aggregates"] = aggregate_csv
    logger.info(f"Generated CSV aggregates table: {aggregate_csv}")

    # Health scores CSV
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

    csv_files["health"] = health_csv
    logger.info(f"Generated CSV health scores table: {health_csv}")

    return csv_files


