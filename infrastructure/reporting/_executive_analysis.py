"""Aggregation and comparison for executive reporting.

Contains aggregate metric generation and comparative table building
across multiple projects.
"""

from __future__ import annotations

from typing import Any

from ._executive_models import ProjectMetrics


def generate_aggregate_metrics(projects: list[ProjectMetrics]) -> dict[str, Any]:
    """Generate aggregate metrics across all projects.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Dictionary of aggregate metrics with totals, averages, and min/max statistics
    """
    if not projects:
        return {}

    # Helper function to calculate statistics
    def _calc_aggregate_stats(values: list[float]) -> dict[str, float]:
        """Calculate min, max, median, and average for a list of values."""
        if not values:
            return {"min": 0.0, "max": 0.0, "median": 0.0, "avg": 0.0}

        sorted_values = sorted(values)
        n = len(sorted_values)
        median = (
            sorted_values[n // 2]
            if n % 2 == 1
            else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        )

        return {
            "min": min(values),
            "max": max(values),
            "median": median,
            "avg": sum(values) / len(values),
        }

    # Collect values for statistics
    manuscript_words = [p.manuscript.total_words for p in projects]

    # Filter out projects with unavailable test data (total_tests = -1)
    available_test_projects = [p for p in projects if p.tests.total_tests >= 0]
    test_coverage = (
        [p.tests.coverage_percent for p in available_test_projects]
        if available_test_projects
        else [0.0]
    )
    pipeline_durations = [p.pipeline.total_duration for p in projects]

    aggregates = {
        "manuscript": {
            "total_words": sum(manuscript_words),
            "total_sections": sum(p.manuscript.sections for p in projects),
            "total_equations": sum(p.manuscript.equations for p in projects),
            "total_figures": sum(p.manuscript.figures for p in projects),
            "total_references": sum(p.manuscript.references for p in projects),
            "words_stats": _calc_aggregate_stats(manuscript_words),
        },
        "codebase": {
            "total_source_lines": sum(p.codebase.source_lines for p in projects),
            "total_methods": sum(p.codebase.methods for p in projects),
            "total_classes": sum(p.codebase.classes for p in projects),
            "total_scripts": sum(p.codebase.scripts for p in projects),
        },
        "tests": {
            "total_tests": (
                sum(p.tests.total_tests for p in available_test_projects)
                if available_test_projects
                else 0
            ),
            "total_passed": (
                sum(p.tests.passed for p in available_test_projects)
                if available_test_projects
                else 0
            ),
            "total_failed": (
                sum(p.tests.failed for p in available_test_projects)
                if available_test_projects
                else 0
            ),
            "average_coverage": (
                sum(test_coverage) / len(available_test_projects)
                if available_test_projects
                else 0.0
            ),
            "coverage_stats": _calc_aggregate_stats(test_coverage),
            "total_execution_time": (
                sum(p.tests.execution_time for p in available_test_projects)
                if available_test_projects
                else 0.0
            ),
            "projects_with_test_data": len(available_test_projects),
            "total_projects": len(projects),
        },
        "outputs": {
            "total_pdfs": sum(p.outputs.pdf_files for p in projects),
            "total_size_mb": sum(p.outputs.pdf_size_mb for p in projects),
            "total_figures": sum(p.outputs.figures for p in projects),
            "total_slides": sum(p.outputs.slides for p in projects),
            "total_web": sum(p.outputs.web_outputs for p in projects),
        },
        "pipeline": {
            "total_duration": sum(pipeline_durations),
            "average_duration": sum(pipeline_durations) / len(projects),
            "duration_stats": _calc_aggregate_stats(pipeline_durations),
            "total_stages_passed": sum(p.pipeline.stages_passed for p in projects),
            "total_stages_failed": sum(p.pipeline.stages_failed for p in projects),
        },
    }

    return aggregates


def generate_comparative_tables(projects: list[ProjectMetrics]) -> dict[str, Any]:
    """Generate comparative tables for all projects.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Dictionary of comparative tables
    """
    tables = {
        "manuscript_comparison": [
            {
                "project": p.name,
                "words": p.manuscript.total_words,
                "sections": p.manuscript.sections,
                "equations": p.manuscript.equations,
                "figures": p.manuscript.figures,
            }
            for p in projects
        ],
        "test_comparison": [
            {
                "project": p.name,
                "tests": p.tests.total_tests,
                "passed": p.tests.passed,
                "coverage": f"{p.tests.coverage_percent:.1f}%",
                "time": f"{p.tests.execution_time:.1f}s",
            }
            for p in projects
        ],
        "output_comparison": [
            {
                "project": p.name,
                "pdfs": p.outputs.pdf_files,
                "size_mb": f"{p.outputs.pdf_size_mb:.1f}",
                "figures": p.outputs.figures,
                "slides": p.outputs.slides,
            }
            for p in projects
        ],
        "pipeline_comparison": [
            {
                "project": p.name,
                "duration": f"{p.pipeline.total_duration:.0f}s",
                "bottleneck": p.pipeline.bottleneck_stage,
                "bottleneck_pct": f"{p.pipeline.bottleneck_percent:.0f}%",
            }
            for p in projects
        ],
    }

    return tables
