"""Tests for infrastructure.reporting._dashboard_charts — comprehensive coverage."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from infrastructure.reporting._dashboard_charts import (
    create_manuscript_complexity_chart,
    create_performance_timeline_chart,
    create_summary_table,
)
from infrastructure.reporting._executive_models import (
    ProjectMetrics,
    ManuscriptMetrics,
    CodebaseMetrics,
    TestMetrics,
    OutputMetrics,
    PipelineMetrics,
)


def _make_project(name, words=5000, equations=10, figures=5, references=20,
                   tests=50, coverage=85.0, duration=30.0, pdf_files=2,
                   pdf_size=1.5, execution_time=10.0, sections=8):
    return ProjectMetrics(
        name=name,
        manuscript=ManuscriptMetrics(
            sections=sections,
            total_words=words,
            total_lines=words // 10,
            equations=equations,
            figures=figures,
            references=references,
        ),
        codebase=CodebaseMetrics(source_files=10, source_lines=1000),
        tests=TestMetrics(
            test_files=5,
            total_tests=tests,
            passed=tests - 2,
            failed=2,
            coverage_percent=coverage,
            execution_time=execution_time,
        ),
        outputs=OutputMetrics(
            pdf_files=pdf_files,
            pdf_size_mb=pdf_size,
            figures=figures,
            total_outputs=pdf_files + figures,
        ),
        pipeline=PipelineMetrics(
            total_duration=duration,
            stages_passed=8,
            stages_failed=0,
        ),
    )


def _make_projects():
    return [
        _make_project("project_a", words=10000, equations=20, figures=8, references=40,
                       tests=100, coverage=92.0, duration=45.0),
        _make_project("project_b", words=5000, equations=5, figures=3, references=15,
                       tests=40, coverage=78.0, duration=20.0),
        _make_project("project_c", words=15000, equations=30, figures=12, references=60,
                       tests=80, coverage=88.0, duration=60.0),
    ]


def _make_aggregate():
    return {
        "manuscript": {
            "total_words": 30000,
            "words_stats": {"mean": 10000, "min": 5000, "max": 15000},
        },
        "tests": {
            "total_tests": 220,
            "average_coverage": 86.0,
            "coverage_stats": {"mean": 86.0, "min": 78.0, "max": 92.0},
        },
        "pipeline": {
            "total_duration": 125.0,
            "duration_stats": {"mean": 41.7, "min": 20.0, "max": 60.0},
        },
        "outputs": {
            "total_pdfs": 6,
            "total_figures": 23,
        },
    }


class TestCreateManuscriptComplexityChart:
    def test_basic(self):
        projects = _make_projects()
        fig = create_manuscript_complexity_chart(projects)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_single_project(self):
        projects = [_make_project("solo", words=8000, equations=15)]
        fig = create_manuscript_complexity_chart(projects)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_two_projects(self):
        projects = [
            _make_project("alpha", words=3000, equations=5, figures=2, references=10),
            _make_project("beta", words=12000, equations=25, figures=10, references=50),
        ]
        fig = create_manuscript_complexity_chart(projects)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_minimal_values(self):
        """Projects with minimal metrics should render."""
        projects = [
            _make_project("minimal", words=1, equations=1, figures=1, references=1, sections=1),
        ]
        fig = create_manuscript_complexity_chart(projects)
        assert isinstance(fig, Figure)
        plt.close(fig)


class TestCreatePerformanceTimelineChart:
    def test_basic(self):
        projects = _make_projects()
        fig = create_performance_timeline_chart(projects)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_single_project(self):
        projects = [_make_project("one")]
        fig = create_performance_timeline_chart(projects)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_varied_performance(self):
        projects = [
            _make_project("fast", duration=5.0, execution_time=2.0, pdf_files=3, pdf_size=0.5),
            _make_project("slow", duration=120.0, execution_time=50.0, pdf_files=1, pdf_size=5.0),
        ]
        fig = create_performance_timeline_chart(projects)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_zero_duration(self):
        """Zero duration should not cause division by zero."""
        projects = [_make_project("zero", duration=0.0, pdf_files=1)]
        fig = create_performance_timeline_chart(projects)
        assert isinstance(fig, Figure)
        plt.close(fig)


class TestCreateSummaryTable:
    def test_basic(self):
        projects = _make_projects()
        aggregate = _make_aggregate()
        fig = create_summary_table(projects, aggregate)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_single_project(self):
        projects = [_make_project("solo", coverage=95.0)]
        aggregate = {
            "manuscript": {"total_words": 5000, "words_stats": {"mean": 5000}},
            "tests": {"total_tests": 50, "average_coverage": 95.0, "coverage_stats": {"mean": 95.0}},
            "pipeline": {"total_duration": 30.0, "duration_stats": {"mean": 30.0}},
            "outputs": {"total_pdfs": 2, "total_figures": 5},
        }
        fig = create_summary_table(projects, aggregate)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_various_grades(self):
        """Test health score coloring for different grade levels."""
        projects = [
            _make_project("excellent", coverage=95.0, tests=100),
            _make_project("good", coverage=80.0, tests=60),
            _make_project("fair", coverage=65.0, tests=30),
            _make_project("poor", coverage=40.0, tests=10),
        ]
        aggregate = {
            "manuscript": {"total_words": 20000, "words_stats": {"mean": 5000}},
            "tests": {"total_tests": 200, "average_coverage": 70.0, "coverage_stats": {"mean": 70.0}},
            "pipeline": {"total_duration": 100.0, "duration_stats": {"mean": 25.0}},
            "outputs": {"total_pdfs": 8, "total_figures": 20},
        }
        fig = create_summary_table(projects, aggregate)
        assert isinstance(fig, Figure)
        plt.close(fig)
