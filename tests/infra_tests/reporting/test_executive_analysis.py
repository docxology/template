"""Tests for infrastructure.reporting._executive_analysis.

Covers generate_aggregate_metrics(), generate_comparative_tables(), and
the private _calc_aggregate_stats() helper.  All tests use real
ProjectMetrics dataclass instances with no mocking framework.
"""

from __future__ import annotations

import math


from infrastructure.reporting._executive_analysis import (
    _calc_aggregate_stats,
    generate_aggregate_metrics,
    generate_comparative_tables,
)
from infrastructure.reporting._executive_models import (
    CodebaseMetrics,
    ManuscriptMetrics,
    OutputMetrics,
    PipelineMetrics,
    ProjectMetrics,
    TestMetrics,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_project(
    name: str = "proj",
    words: int = 1000,
    sections: int = 5,
    equations: int = 2,
    figures: int = 3,
    references: int = 10,
    source_lines: int = 200,
    methods: int = 10,
    classes: int = 2,
    scripts: int = 3,
    total_tests: int = 20,
    passed: int = 20,
    failed: int = 0,
    coverage: float = 95.0,
    exec_time: float = 5.0,
    pdf_files: int = 1,
    pdf_size_mb: float = 0.5,
    output_figures: int = 4,
    slides: int = 0,
    web_outputs: int = 0,
    duration: float = 60.0,
    stages_passed: int = 10,
    stages_failed: int = 0,
    bottleneck: str = "render",
    bottleneck_pct: float = 40.0,
) -> ProjectMetrics:
    return ProjectMetrics(
        name=name,
        manuscript=ManuscriptMetrics(
            sections=sections,
            total_words=words,
            equations=equations,
            figures=figures,
            references=references,
        ),
        codebase=CodebaseMetrics(
            source_lines=source_lines,
            methods=methods,
            classes=classes,
            scripts=scripts,
        ),
        tests=TestMetrics(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            coverage_percent=coverage,
            execution_time=exec_time,
        ),
        outputs=OutputMetrics(
            pdf_files=pdf_files,
            pdf_size_mb=pdf_size_mb,
            figures=output_figures,
            slides=slides,
            web_outputs=web_outputs,
        ),
        pipeline=PipelineMetrics(
            total_duration=duration,
            stages_passed=stages_passed,
            stages_failed=stages_failed,
            bottleneck_stage=bottleneck,
            bottleneck_percent=bottleneck_pct,
        ),
    )


# ---------------------------------------------------------------------------
# _calc_aggregate_stats
# ---------------------------------------------------------------------------


class TestCalcAggregateStats:
    """Tests for the private _calc_aggregate_stats helper."""

    def test_empty_list_returns_zeros(self) -> None:
        result = _calc_aggregate_stats([])
        assert result == {"min": 0.0, "max": 0.0, "median": 0.0, "mean": 0.0}

    def test_single_value(self) -> None:
        result = _calc_aggregate_stats([5.0])
        assert result["min"] == 5.0
        assert result["max"] == 5.0
        assert result["median"] == 5.0
        assert result["mean"] == 5.0

    def test_two_values(self) -> None:
        result = _calc_aggregate_stats([2.0, 8.0])
        assert result["min"] == 2.0
        assert result["max"] == 8.0
        assert math.isclose(result["median"], 5.0)
        assert math.isclose(result["mean"], 5.0)

    def test_odd_count_median(self) -> None:
        result = _calc_aggregate_stats([1.0, 3.0, 5.0])
        assert result["median"] == 3.0

    def test_even_count_median(self) -> None:
        result = _calc_aggregate_stats([1.0, 2.0, 3.0, 4.0])
        assert math.isclose(result["median"], 2.5)

    def test_mean_calculation(self) -> None:
        result = _calc_aggregate_stats([10.0, 20.0, 30.0])
        assert math.isclose(result["mean"], 20.0)

    def test_all_same_values(self) -> None:
        result = _calc_aggregate_stats([7.0, 7.0, 7.0])
        assert result["min"] == 7.0
        assert result["max"] == 7.0
        assert result["median"] == 7.0
        assert result["mean"] == 7.0


# ---------------------------------------------------------------------------
# generate_aggregate_metrics
# ---------------------------------------------------------------------------


class TestGenerateAggregateMetrics:
    """Tests for generate_aggregate_metrics()."""

    def test_empty_list_returns_no_data(self) -> None:
        result = generate_aggregate_metrics([])
        assert result == {"no_data": True}

    def test_single_project_structure(self) -> None:
        proj = _make_project(words=500, sections=3)
        result = generate_aggregate_metrics([proj])
        assert "manuscript" in result
        assert "codebase" in result
        assert "tests" in result
        assert "outputs" in result
        assert "pipeline" in result

    def test_manuscript_totals(self) -> None:
        p1 = _make_project("a", words=1000, sections=5, equations=2, figures=3, references=10)
        p2 = _make_project("b", words=2000, sections=8, equations=4, figures=6, references=20)
        result = generate_aggregate_metrics([p1, p2])
        assert result["manuscript"]["total_words"] == 3000
        assert result["manuscript"]["total_sections"] == 13
        assert result["manuscript"]["total_equations"] == 6
        assert result["manuscript"]["total_figures"] == 9
        assert result["manuscript"]["total_references"] == 30

    def test_codebase_totals(self) -> None:
        p1 = _make_project("a", source_lines=100, methods=5, classes=1, scripts=2)
        p2 = _make_project("b", source_lines=200, methods=10, classes=3, scripts=4)
        result = generate_aggregate_metrics([p1, p2])
        assert result["codebase"]["total_source_lines"] == 300
        assert result["codebase"]["total_methods"] == 15
        assert result["codebase"]["total_classes"] == 4
        assert result["codebase"]["total_scripts"] == 6

    def test_test_totals(self) -> None:
        p1 = _make_project("a", total_tests=10, passed=9, failed=1, coverage=90.0)
        p2 = _make_project("b", total_tests=20, passed=20, failed=0, coverage=100.0)
        result = generate_aggregate_metrics([p1, p2])
        assert result["tests"]["total_tests"] == 30
        assert result["tests"]["total_passed"] == 29
        assert result["tests"]["total_failed"] == 1
        assert math.isclose(result["tests"]["average_coverage"], 95.0)

    def test_unavailable_test_data_excluded(self) -> None:
        """Projects with total_tests=-1 are excluded from test aggregates."""
        p1 = _make_project("a", total_tests=-1)
        p2 = _make_project("b", total_tests=15, passed=15, coverage=100.0)
        result = generate_aggregate_metrics([p1, p2])
        assert result["tests"]["projects_with_test_data"] == 1
        assert result["tests"]["total_tests"] == 15

    def test_output_totals(self) -> None:
        p1 = _make_project("a", pdf_files=1, pdf_size_mb=0.5, output_figures=3)
        p2 = _make_project("b", pdf_files=2, pdf_size_mb=1.0, output_figures=5)
        result = generate_aggregate_metrics([p1, p2])
        assert result["outputs"]["total_pdfs"] == 3
        assert math.isclose(result["outputs"]["total_size_mb"], 1.5)
        assert result["outputs"]["total_figures"] == 8

    def test_pipeline_totals(self) -> None:
        p1 = _make_project("a", duration=30.0, stages_passed=5, stages_failed=0)
        p2 = _make_project("b", duration=60.0, stages_passed=8, stages_failed=1)
        result = generate_aggregate_metrics([p1, p2])
        assert math.isclose(result["pipeline"]["total_duration"], 90.0)
        assert math.isclose(result["pipeline"]["average_duration"], 45.0)
        assert result["pipeline"]["total_stages_passed"] == 13
        assert result["pipeline"]["total_stages_failed"] == 1

    def test_manuscript_words_stats_present(self) -> None:
        p1 = _make_project("a", words=100)
        p2 = _make_project("b", words=300)
        result = generate_aggregate_metrics([p1, p2])
        stats = result["manuscript"]["words_stats"]
        assert "min" in stats
        assert "max" in stats
        assert "median" in stats
        assert "mean" in stats
        assert stats["min"] == 100
        assert stats["max"] == 300


# ---------------------------------------------------------------------------
# generate_comparative_tables
# ---------------------------------------------------------------------------


class TestGenerateComparativeTables:
    """Tests for generate_comparative_tables()."""

    def test_structure_keys_present(self) -> None:
        proj = _make_project()
        result = generate_comparative_tables([proj])
        assert "manuscript_comparison" in result
        assert "test_comparison" in result
        assert "output_comparison" in result
        assert "pipeline_comparison" in result

    def test_manuscript_comparison_contains_project(self) -> None:
        proj = _make_project("my_proj", words=1500)
        result = generate_comparative_tables([proj])
        rows = result["manuscript_comparison"]
        assert len(rows) == 1
        assert rows[0]["project"] == "my_proj"
        assert rows[0]["words"] == 1500

    def test_test_comparison_contains_coverage_string(self) -> None:
        proj = _make_project("proj", coverage=87.5)
        result = generate_comparative_tables([proj])
        rows = result["test_comparison"]
        assert "87.5%" in rows[0]["coverage"]

    def test_output_comparison_size_is_string(self) -> None:
        proj = _make_project("proj", pdf_size_mb=1.23)
        result = generate_comparative_tables([proj])
        rows = result["output_comparison"]
        # size_mb is formatted as a string
        assert isinstance(rows[0]["size_mb"], str)

    def test_pipeline_comparison_duration_is_string(self) -> None:
        proj = _make_project("proj", duration=120.0)
        result = generate_comparative_tables([proj])
        rows = result["pipeline_comparison"]
        assert "120" in rows[0]["duration"]

    def test_multiple_projects_all_appear(self) -> None:
        projects = [_make_project(name=f"proj_{i}") for i in range(3)]
        result = generate_comparative_tables(projects)
        names = [r["project"] for r in result["manuscript_comparison"]]
        assert names == ["proj_0", "proj_1", "proj_2"]

    def test_empty_list_produces_empty_tables(self) -> None:
        result = generate_comparative_tables([])
        for key in ("manuscript_comparison", "test_comparison", "output_comparison", "pipeline_comparison"):
            assert result[key] == []
