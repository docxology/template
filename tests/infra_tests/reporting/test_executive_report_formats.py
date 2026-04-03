"""Tests for infrastructure.reporting._executive_report_formats — comprehensive coverage."""

from infrastructure.reporting._executive_report_formats import (
    generate_executive_html_report,
    generate_executive_markdown_report,
)
from infrastructure.reporting._executive_models import (
    CodebaseMetrics,
    ExecutiveSummary,
    ManuscriptMetrics,
    OutputMetrics,
    PipelineMetrics,
    ProjectMetrics,
    TestMetrics,
)
from infrastructure.reporting._executive_health import calculate_project_health_score


def _make_project(name="proj_a", words=5000, coverage=90.0, total_tests=100, failed=0):
    return ProjectMetrics(
        name=name,
        manuscript=ManuscriptMetrics(
            sections=5, total_words=words, equations=10, figures=3, references=20
        ),
        codebase=CodebaseMetrics(
            source_files=10, source_lines=500, scripts=3, script_lines=100, methods=20, classes=5
        ),
        tests=TestMetrics(
            total_tests=total_tests,
            passed=total_tests - failed,
            failed=failed,
            coverage_percent=coverage,
            execution_time=30.0,
        ),
        outputs=OutputMetrics(
            pdf_files=2, pdf_size_mb=1.5, figures=3, slides=1, web_outputs=1, total_outputs=7
        ),
        pipeline=PipelineMetrics(
            total_duration=60.0,
            stages_passed=8,
            bottleneck_stage="render",
            bottleneck_duration=20.0,
            bottleneck_percent=33.3,
        ),
    )


def _make_summary(projects=None, recommendations=None):
    if projects is None:
        projects = [_make_project("proj_a"), _make_project("proj_b", words=3000)]
    health_scores = {p.name: calculate_project_health_score(p) for p in projects}
    return ExecutiveSummary(
        timestamp="2026-01-01T00:00:00",
        total_projects=len(projects),
        aggregate_metrics={
            "manuscript": {
                "total_words": sum(p.manuscript.total_words for p in projects),
                "total_sections": sum(p.manuscript.sections for p in projects),
                "total_equations": sum(p.manuscript.equations for p in projects),
                "total_figures": sum(p.manuscript.figures for p in projects),
                "total_references": sum(p.manuscript.references for p in projects),
                "words_stats": {"mean": 4000},
            },
            "codebase": {
                "total_source_lines": sum(p.codebase.source_lines for p in projects),
                "total_methods": sum(p.codebase.methods for p in projects),
                "total_classes": sum(p.codebase.classes for p in projects),
                "total_scripts": sum(p.codebase.scripts for p in projects),
            },
            "tests": {
                "total_tests": sum(p.tests.total_tests for p in projects),
                "total_passed": sum(p.tests.passed for p in projects),
                "total_failed": sum(p.tests.failed for p in projects),
                "average_coverage": 90.0,
                "total_execution_time": sum(p.tests.execution_time for p in projects),
                "coverage_stats": {"mean": 90.0},
                "projects_with_test_data": len(projects),
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
                "total_duration": sum(p.pipeline.total_duration for p in projects),
                "average_duration": 60.0,
                "total_stages_passed": sum(p.pipeline.stages_passed for p in projects),
                "duration_stats": {"mean": 60.0},
            },
        },
        project_metrics=projects,
        health_scores=health_scores,
        comparative_tables={},
        recommendations=recommendations or ["Improve test coverage", "Consider adding docs"],
    )


class TestGenerateExecutiveMarkdownReport:
    def test_basic_structure(self):
        summary = _make_summary()
        md = generate_executive_markdown_report(summary)
        assert "# Executive Summary" in md
        assert "## Executive Overview" in md
        assert "## Aggregate Metrics" in md
        assert "## Project Comparison" in md
        assert "## Actionable Recommendations" in md

    def test_contains_project_names(self):
        summary = _make_summary()
        md = generate_executive_markdown_report(summary)
        assert "proj_a" in md
        assert "proj_b" in md

    def test_contains_key_metrics(self):
        summary = _make_summary()
        md = generate_executive_markdown_report(summary)
        assert "8,000" in md  # total words (5000+3000)
        assert "200" in md  # total tests

    def test_high_priority_recommendations(self):
        summary = _make_summary(recommendations=["Critical: fix failing tests immediately"])
        md = generate_executive_markdown_report(summary)
        assert "HIGH" in md
        assert "High Priority" in md

    def test_medium_priority_recommendations(self):
        summary = _make_summary(recommendations=["Consider improving test coverage below 80%"])
        md = generate_executive_markdown_report(summary)
        assert "MEDIUM" in md

    def test_low_priority_recommendations(self):
        summary = _make_summary(recommendations=["Add more documentation"])
        md = generate_executive_markdown_report(summary)
        assert "LOW" in md

    def test_single_project(self):
        summary = _make_summary(projects=[_make_project("solo")])
        md = generate_executive_markdown_report(summary)
        assert "solo" in md

    def test_health_status_good(self):
        summary = _make_summary()
        md = generate_executive_markdown_report(summary)
        assert "Health Status" in md or "Critical Issues" in md

    def test_dashboard_references(self):
        summary = _make_summary()
        md = generate_executive_markdown_report(summary)
        assert "Visual Dashboards" in md
        assert "health_scores_radar" in md

    def test_comparison_table(self):
        summary = _make_summary()
        md = generate_executive_markdown_report(summary)
        assert "| Project | Words | Tests | Coverage | Duration | PDF Size |" in md
        assert "TOTAL" in md


class TestGenerateExecutiveHtmlReport:
    def test_basic_structure(self):
        summary = _make_summary()
        html = generate_executive_html_report(summary)
        assert "<!DOCTYPE html>" in html or "<html" in html
        assert "Executive Summary" in html

    def test_contains_project_data(self):
        summary = _make_summary()
        html = generate_executive_html_report(summary)
        assert "proj_a" in html
        assert "proj_b" in html

    def test_contains_metrics(self):
        summary = _make_summary()
        html = generate_executive_html_report(summary)
        assert "8,000" in html  # total words
        assert "Total Projects" in html

    def test_high_priority_recommendations(self):
        summary = _make_summary(recommendations=["Critical issue needs immediate attention"])
        html = generate_executive_html_report(summary)
        assert "High Priority" in html

    def test_dashboard_section(self):
        summary = _make_summary()
        html = generate_executive_html_report(summary)
        assert "Visual Dashboards" in html
