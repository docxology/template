"""CSV export: detailed per-project metric breakdown.

Generates a single CSV with every metric for every project, annotated with
units, health impact, and recommended ranges.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting.executive_reporter import ExecutiveSummary
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

if TYPE_CHECKING:
    from infrastructure.reporting._executive_models import ProjectMetrics

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
            _write_manuscript_rows(writer, project)
            _write_codebase_rows(writer, project)
            _write_test_rows(writer, project)
            _write_output_rows(writer, project)
            _write_pipeline_rows(writer, project)

    logger.info(f"Detailed project breakdown CSV saved: {csv_path}")
    return csv_path


# ── Internal helpers ─────────────────────────────────────────────────────────


def _write_manuscript_rows(writer: csv.writer, project: ProjectMetrics) -> None:  # type: ignore[type-arg]
    """Write manuscript metric rows for a single project."""
    name = project.name
    m = project.manuscript
    rows = [
        (name, "Manuscript", "Total_Words", m.total_words, "words",
         "Total words in manuscript sections", "High", "1000-20000 words"),
        (name, "Manuscript", "Sections", m.sections, "count",
         "Number of manuscript sections", "Medium", "3-20 sections"),
        (name, "Manuscript", "Equations", m.equations, "count",
         "Mathematical equations in manuscript", "Low", "0-50 equations"),
        (name, "Manuscript", "Figures", m.figures, "count",
         "Figure references in manuscript", "Low", "0-20 figures"),
        (name, "Manuscript", "References", m.references, "count",
         "Citation references", "Medium", "10-200 references"),
    ]
    for row in rows:
        writer.writerow(row)


def _write_codebase_rows(writer: csv.writer, project: ProjectMetrics) -> None:  # type: ignore[type-arg]
    """Write codebase metric rows for a single project."""
    name = project.name
    c = project.codebase
    rows = [
        (name, "Codebase", "Source_Files", c.source_files, "files",
         "Python source files", "Medium", "1-20 files"),
        (name, "Codebase", "Source_Lines", c.source_lines, "lines",
         "Lines of source code", "Medium", "100-5000 lines"),
        (name, "Codebase", "Methods", c.methods, "count",
         "Function/method definitions", "Medium", "10-500 methods"),
        (name, "Codebase", "Classes", c.classes, "count",
         "Class definitions", "Low", "0-50 classes"),
        (name, "Codebase", "Scripts", c.scripts, "files",
         "Analysis scripts", "Low", "0-10 scripts"),
    ]
    for row in rows:
        writer.writerow(row)


def _write_test_rows(writer: csv.writer, project: ProjectMetrics) -> None:  # type: ignore[type-arg]
    """Write test metric rows for a single project."""
    name = project.name
    t = project.tests
    rows = [
        (name, "Testing", "Test_Files", t.test_files, "files",
         "Test files discovered", "High", "1+ files"),
        (name, "Testing", "Total_Tests", t.total_tests, "tests",
         "Total test cases (-1 = unavailable)", "High", "10-1000 tests"),
        (name, "Testing", "Coverage_Percent", t.coverage_percent, "percent",
         "Code coverage percentage", "High", "90-100%"),
        (name, "Testing", "Execution_Time", t.execution_time, "seconds",
         "Test execution time", "Low", "1-300 seconds"),
    ]
    for row in rows:
        writer.writerow(row)


def _write_output_rows(writer: csv.writer, project: ProjectMetrics) -> None:  # type: ignore[type-arg]
    """Write output metric rows for a single project."""
    name = project.name
    o = project.outputs
    rows = [
        (name, "Outputs", "PDF_Files", o.pdf_files, "files",
         "Generated PDF documents", "High", "1+ files"),
        (name, "Outputs", "PDF_Size_MB", f"{o.pdf_size_mb:.2f}", "MB",
         "Total PDF file size", "Low", "0.1-10 MB"),
        (name, "Outputs", "Figures", o.figures, "files",
         "Generated figure files", "Medium", "0-50 figures"),
        (name, "Outputs", "Slides", o.slides, "files",
         "Generated slide files", "Medium", "0-20 slide sets"),
        (name, "Outputs", "Web_Outputs", o.web_outputs, "files",
         "Generated web files", "Medium", "0-20 web files"),
    ]
    for row in rows:
        writer.writerow(row)


def _write_pipeline_rows(writer: csv.writer, project: ProjectMetrics) -> None:  # type: ignore[type-arg]
    """Write pipeline metric rows for a single project."""
    name = project.name
    p = project.pipeline
    rows = [
        (name, "Pipeline", "Total_Duration", p.total_duration, "seconds",
         "Total pipeline execution time", "Medium", "60-600 seconds"),
        (name, "Pipeline", "Stages_Passed", p.stages_passed, "stages",
         "Pipeline stages completed successfully", "High", "6 stages"),
        (name, "Pipeline", "Bottleneck_Stage", p.bottleneck_stage, "stage_name",
         "Slowest pipeline stage", "Medium", "Varies by project"),
        (name, "Pipeline", "Bottleneck_Duration", p.bottleneck_duration, "seconds",
         "Time spent in bottleneck stage", "Medium", "10-300 seconds"),
    ]
    for row in rows:
        writer.writerow(row)
