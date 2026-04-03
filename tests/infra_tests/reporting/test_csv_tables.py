"""Tests for infrastructure.reporting._csv_tables — comprehensive coverage."""

import csv

from infrastructure.reporting._csv_tables import (
    _classify_recommendation,
    generate_csv_data_tables,
    generate_prioritized_recommendations_csv,
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


def _make_project(name="proj_a", coverage=90.0, total_tests=100, failed=0, words=5000):
    return ProjectMetrics(
        name=name,
        manuscript=ManuscriptMetrics(
            sections=5, total_words=words, equations=10, figures=3, references=20
        ),
        codebase=CodebaseMetrics(source_files=10, source_lines=500),
        tests=TestMetrics(
            total_tests=total_tests,
            passed=total_tests - failed,
            failed=failed,
            coverage_percent=coverage,
            execution_time=30.0,
        ),
        outputs=OutputMetrics(pdf_files=2, pdf_size_mb=1.5, figures=3, total_outputs=5),
        pipeline=PipelineMetrics(
            total_duration=60.0,
            stages_passed=8,
            bottleneck_stage="render",
            bottleneck_duration=20.0,
        ),
    )


def _make_summary(recommendations=None):
    proj = _make_project()
    from infrastructure.reporting._executive_health import calculate_project_health_score

    health = calculate_project_health_score(proj)
    return ExecutiveSummary(
        timestamp="2026-01-01T00:00:00",
        total_projects=1,
        aggregate_metrics={
            "manuscript": {
                "total_words": 5000,
                "total_sections": 5,
                "total_equations": 10,
                "total_figures": 3,
                "total_references": 20,
                "words_stats": {"mean": 5000},
            },
            "tests": {
                "total_tests": 100,
                "total_passed": 100,
                "total_failed": 0,
                "average_coverage": 90.0,
                "total_execution_time": 30.0,
                "coverage_stats": {"mean": 90.0},
            },
            "pipeline": {
                "total_duration": 60.0,
                "average_duration": 60.0,
                "total_stages_passed": 8,
                "total_stages_failed": 0,
                "duration_stats": {"mean": 60.0},
            },
            "outputs": {
                "total_pdfs": 2,
                "total_size_mb": 1.5,
                "total_figures": 3,
                "total_slides": 0,
                "total_web": 0,
            },
        },
        project_metrics=[proj],
        health_scores={
            proj.name: health,
        },
        comparative_tables={},
        recommendations=recommendations or ["Improve test coverage", "Consider adding more tests"],
    )


class TestClassifyRecommendation:
    def test_critical_keyword(self):
        summary = _make_summary()
        result = _classify_recommendation("Critical: fix failing tests immediately", summary)
        assert result["priority_level"] == "High"
        assert result["priority_score"] == 5
        assert result["impact_level"] == "High"

    def test_improve_keyword(self):
        summary = _make_summary()
        result = _classify_recommendation("Improve test coverage below 90%", summary)
        assert result["priority_level"] == "Medium"
        assert result["priority_score"] == 3

    def test_generic_recommendation(self):
        summary = _make_summary()
        result = _classify_recommendation("Add documentation for new module", summary)
        assert result["priority_level"] == "Low"
        assert result["priority_score"] == 1

    def test_test_category(self):
        summary = _make_summary()
        result = _classify_recommendation("Add more tests", summary)
        assert result["category"] == "Testing"

    def test_coverage_category(self):
        summary = _make_summary()
        result = _classify_recommendation("Coverage needs improvement", summary)
        assert result["category"] == "Code Quality"

    def test_manuscript_category(self):
        summary = _make_summary()
        result = _classify_recommendation("Improve manuscript quality", summary)
        assert result["category"] == "Content"

    def test_pipeline_category(self):
        summary = _make_summary()
        result = _classify_recommendation("Optimize pipeline speed", summary)
        assert result["category"] == "Performance"

    def test_output_category(self):
        summary = _make_summary()
        result = _classify_recommendation("Review output files", summary)
        assert result["category"] == "Deliverables"

    def test_affected_project_detected(self):
        summary = _make_summary()
        result = _classify_recommendation("proj_a needs more tests", summary)
        assert result["affected_projects"] == "proj_a"


class TestGeneratePrioritizedRecommendationsCsv:
    def test_creates_csv_file(self, tmp_path):
        summary = _make_summary(["Critical: fix now", "Improve coverage", "Minor cleanup"])
        csv_path = generate_prioritized_recommendations_csv(summary, tmp_path)
        assert csv_path.exists()
        assert csv_path.suffix == ".csv"

        with open(csv_path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        # Header + 3 data rows
        assert len(rows) == 4
        assert rows[0][0] == "Priority_Level"
        # First row should be highest priority (Critical)
        assert rows[1][0] == "High"


class TestGenerateCsvDataTables:
    def test_creates_three_csv_files(self, tmp_path):
        summary = _make_summary()
        result = generate_csv_data_tables(summary, tmp_path)
        assert "metrics" in result
        assert "aggregates" in result
        assert "health" in result
        for path in result.values():
            assert path.exists()
            assert path.suffix == ".csv"

    def test_metrics_csv_has_project_row(self, tmp_path):
        summary = _make_summary()
        result = generate_csv_data_tables(summary, tmp_path)
        with open(result["metrics"]) as f:
            reader = csv.reader(f)
            rows = list(reader)
        # Header + 1 project row
        assert len(rows) == 2
        assert rows[0][0] == "Project"
        assert rows[1][0] == "proj_a"

    def test_aggregate_csv_has_categories(self, tmp_path):
        summary = _make_summary()
        result = generate_csv_data_tables(summary, tmp_path)
        with open(result["aggregates"]) as f:
            reader = csv.reader(f)
            rows = list(reader)
        # Header + many metric rows
        assert len(rows) > 5
        categories = {row[0] for row in rows[1:]}
        assert "Manuscript" in categories
        assert "Tests" in categories
        assert "Pipeline" in categories
        assert "Outputs" in categories

    def test_health_csv_has_scores(self, tmp_path):
        summary = _make_summary()
        result = generate_csv_data_tables(summary, tmp_path)
        with open(result["health"]) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2  # Header + 1 project
        assert rows[0][0] == "Project"
        assert rows[1][0] == "proj_a"
