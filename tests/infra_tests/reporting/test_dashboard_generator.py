"""Tests for dashboard generator module.

Tests visual dashboard generation in multiple formats (PNG, PDF, HTML).
"""

from pathlib import Path

import pytest

from infrastructure.reporting.dashboard_generator import (
    create_coverage_chart, create_manuscript_size_chart,
    create_output_distribution_chart, create_pipeline_duration_chart,
    create_summary_table, create_test_count_chart, generate_all_dashboards,
    generate_matplotlib_dashboard, generate_plotly_dashboard)
from infrastructure.reporting.executive_reporter import (
    CodebaseMetrics, ExecutiveSummary, ManuscriptMetrics, OutputMetrics,
    PipelineMetrics, ProjectMetrics, TestMetrics,
    calculate_project_health_score)


@pytest.fixture
def sample_projects():
    """Create sample project metrics for testing."""
    project1 = ProjectMetrics(
        name="project1",
        manuscript=ManuscriptMetrics(
            total_words=1000, sections=4, equations=10, figures=5, references=20
        ),
        codebase=CodebaseMetrics(source_lines=500, methods=25, classes=5, scripts=3),
        tests=TestMetrics(
            total_tests=100,
            passed=100,
            failed=0,
            coverage_percent=95.0,
            execution_time=10.0,
        ),
        outputs=OutputMetrics(
            pdf_files=5,
            pdf_size_mb=2.0,
            figures=5,
            data_files=3,
            slides=10,
            web_outputs=2,
            total_outputs=25,
        ),
        pipeline=PipelineMetrics(
            total_duration=120.0,
            stages_passed=6,
            stages_failed=0,
            bottleneck_stage="tests",
            bottleneck_duration=45.0,
            bottleneck_percent=37.5,
        ),
    )

    project2 = ProjectMetrics(
        name="project2",
        manuscript=ManuscriptMetrics(
            total_words=800, sections=3, equations=8, figures=4, references=15
        ),
        codebase=CodebaseMetrics(source_lines=400, methods=20, classes=4, scripts=2),
        tests=TestMetrics(
            total_tests=80,
            passed=75,
            failed=5,
            coverage_percent=92.0,
            execution_time=8.0,
        ),
        outputs=OutputMetrics(
            pdf_files=4,
            pdf_size_mb=1.5,
            figures=4,
            data_files=2,
            slides=8,
            web_outputs=1,
            total_outputs=19,
        ),
        pipeline=PipelineMetrics(
            total_duration=100.0,
            stages_passed=6,
            stages_failed=0,
            bottleneck_stage="render",
            bottleneck_duration=40.0,
            bottleneck_percent=40.0,
        ),
    )

    return [project1, project2]


@pytest.fixture
def sample_aggregate():
    """Create sample aggregate metrics."""
    return {
        "manuscript": {"total_words": 1800, "total_sections": 7},
        "codebase": {"total_source_lines": 900, "total_methods": 45},
        "tests": {"total_tests": 180, "total_passed": 175, "average_coverage": 93.5},
        "outputs": {
            "total_pdfs": 9,
            "total_size_mb": 3.5,
            "total_figures": 9,
            "total_slides": 18,
            "total_web": 3,
        },
        "pipeline": {"total_duration": 220.0, "average_duration": 110.0},
    }


@pytest.fixture
def sample_summary(sample_projects, sample_aggregate):
    """Create sample executive summary."""
    health_scores = {p.name: calculate_project_health_score(p) for p in sample_projects}
    return ExecutiveSummary(
        timestamp="2025-12-28T10:00:00",
        total_projects=2,
        aggregate_metrics=sample_aggregate,
        project_metrics=sample_projects,
        health_scores=health_scores,
        comparative_tables={},
        recommendations=["Test recommendation"],
    )


class TestChartGeneration:
    """Test individual chart generation functions."""

    def test_create_test_count_chart(self, sample_projects):
        """Test test count bar chart generation."""
        fig = create_test_count_chart(sample_projects)

        assert fig is not None
        assert len(fig.axes) > 0

        # Clean up
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_create_coverage_chart(self, sample_projects):
        """Test coverage bar chart generation."""
        fig = create_coverage_chart(sample_projects)

        assert fig is not None
        assert len(fig.axes) > 0

        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_create_pipeline_duration_chart(self, sample_projects):
        """Test pipeline duration stacked bar chart."""
        fig = create_pipeline_duration_chart(sample_projects)

        assert fig is not None
        assert len(fig.axes) > 0

        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_create_output_distribution_chart(self, sample_aggregate):
        """Test output distribution pie chart."""
        fig = create_output_distribution_chart(sample_aggregate)

        assert fig is not None
        assert len(fig.axes) > 0

        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_create_output_distribution_chart_empty(self):
        """Test output distribution chart with no outputs."""
        empty_aggregate = {
            "outputs": {
                "total_pdfs": 0,
                "total_figures": 0,
                "total_slides": 0,
                "total_web": 0,
            }
        }
        fig = create_output_distribution_chart(empty_aggregate)

        assert fig is not None

        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_create_manuscript_size_chart(self, sample_projects):
        """Test manuscript size bar chart."""
        fig = create_manuscript_size_chart(sample_projects)

        assert fig is not None
        assert len(fig.axes) > 0

        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_create_summary_table(self, sample_projects, sample_aggregate):
        """Test summary table generation."""
        fig = create_summary_table(sample_projects, sample_aggregate)

        assert fig is not None
        assert len(fig.axes) > 0

        import matplotlib.pyplot as plt

        plt.close(fig)


class TestMatplotlibDashboard:
    """Test matplotlib dashboard generation."""

    def test_generate_matplotlib_dashboard(self, sample_summary, tmp_path):
        """Test generating matplotlib dashboard (PNG and PDF)."""
        saved_files = generate_matplotlib_dashboard(sample_summary, tmp_path)

        assert "png" in saved_files
        assert "pdf" in saved_files

        # Verify files exist
        assert saved_files["png"].exists()
        assert saved_files["pdf"].exists()

        # Verify file sizes are reasonable
        assert saved_files["png"].stat().st_size > 1000  # At least 1KB
        assert saved_files["pdf"].stat().st_size > 1000

    def test_generate_matplotlib_dashboard_single_project(self, tmp_path):
        """Test dashboard generation with single project."""
        project = ProjectMetrics(
            name="single_project",
            manuscript=ManuscriptMetrics(total_words=1000),
            codebase=CodebaseMetrics(),
            tests=TestMetrics(total_tests=50, passed=50, coverage_percent=95.0),
            outputs=OutputMetrics(pdf_files=3),
            pipeline=PipelineMetrics(total_duration=60.0),
        )

        health_scores = {project.name: calculate_project_health_score(project)}
        summary = ExecutiveSummary(
            timestamp="2025-12-28T10:00:00",
            total_projects=1,
            aggregate_metrics={
                "manuscript": {},
                "codebase": {},
                "tests": {},
                "outputs": {},
                "pipeline": {},
            },
            project_metrics=[project],
            health_scores=health_scores,
            comparative_tables={},
            recommendations=[],
        )

        saved_files = generate_matplotlib_dashboard(summary, tmp_path)

        assert len(saved_files) == 2  # PNG and PDF


class TestPlotlyDashboard:
    """Test plotly dashboard generation."""

    def test_generate_plotly_dashboard(self, sample_summary, tmp_path):
        """Test generating plotly dashboard (interactive HTML)."""
        try:
            import plotly

            html_path = generate_plotly_dashboard(sample_summary, tmp_path)

            if html_path:  # If plotly is available
                assert html_path.exists()
                assert html_path.suffix == ".html"
                assert html_path.stat().st_size > 1000  # At least 1KB
        except ImportError:
            # Plotly not installed - test should handle gracefully
            html_path = generate_plotly_dashboard(sample_summary, tmp_path)
            assert html_path is None


class TestAllDashboards:
    """Test generating all dashboard formats."""

    def test_generate_all_dashboards(self, sample_summary, tmp_path):
        """Test generating all dashboard formats."""
        all_files = generate_all_dashboards(sample_summary, tmp_path)

        # Should have at least PNG and PDF (matplotlib always works)
        assert "png" in all_files
        assert "pdf" in all_files

        # May or may not have HTML depending on plotly availability
        # Just check that files were generated
        assert len(all_files) >= 2

        # Verify all files exist
        for file_path in all_files.values():
            assert file_path.exists()

    def test_generate_all_dashboards_empty_projects(self, tmp_path):
        """Test dashboard generation with no projects."""
        summary = ExecutiveSummary(
            timestamp="2025-12-28T10:00:00",
            total_projects=0,
            aggregate_metrics={
                "manuscript": {},
                "codebase": {},
                "tests": {},
                "outputs": {},
                "pipeline": {},
            },
            project_metrics=[],
            health_scores={},
            comparative_tables={},
            recommendations=[],
        )

        all_files = generate_all_dashboards(summary, tmp_path)

        # Should still generate files (may be empty/placeholder)
        assert len(all_files) >= 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_chart_with_zero_values(self):
        """Test chart generation with all zero values."""
        project = ProjectMetrics(
            name="zero_project",
            manuscript=ManuscriptMetrics(total_words=0),
            codebase=CodebaseMetrics(),
            tests=TestMetrics(total_tests=0, passed=0, coverage_percent=0.0),
            outputs=OutputMetrics(),
            pipeline=PipelineMetrics(total_duration=0.0),
        )

        # Should not crash
        fig = create_test_count_chart([project])
        assert fig is not None

        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_chart_with_large_values(self):
        """Test chart generation with very large values."""
        project = ProjectMetrics(
            name="large_project",
            manuscript=ManuscriptMetrics(total_words=1000000),
            codebase=CodebaseMetrics(),
            tests=TestMetrics(
                total_tests=100000, passed=100000, coverage_percent=100.0
            ),
            outputs=OutputMetrics(pdf_files=1000),
            pipeline=PipelineMetrics(total_duration=10000.0),
        )

        # Should handle large values
        fig = create_manuscript_size_chart([project])
        assert fig is not None

        import matplotlib.pyplot as plt

        plt.close(fig)
