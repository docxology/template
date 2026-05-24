"""Tests for infrastructure.reporting.report_builder — comprehensive coverage."""

import json

import pytest

from infrastructure.reporting.report_builder import (
    _calculate_weighted_coverage,
    _aggregate_counts,
    _is_ollama_available,
    generate_summary_report,
    discover_active_projects,
)


class TestCalculateWeightedCoverage:
    def test_single_result(self):
        results = [{"coverage_percent": 80.0, "total_lines": 100}]
        assert _calculate_weighted_coverage(results) == 80.0

    def test_weighted_by_lines(self):
        results = [
            {"coverage_percent": 100.0, "total_lines": 100},
            {"coverage_percent": 0.0, "total_lines": 100},
        ]
        assert _calculate_weighted_coverage(results) == 50.0

    def test_unequal_weights(self):
        results = [
            {"coverage_percent": 90.0, "total_lines": 900},
            {"coverage_percent": 10.0, "total_lines": 100},
        ]
        # (90*900 + 10*100) / 1000 = 82.0
        assert abs(_calculate_weighted_coverage(results) - 82.0) < 0.01

    def test_no_lines(self):
        results = [{"coverage_percent": 90.0, "total_lines": 0}]
        assert _calculate_weighted_coverage(results) == 0.0

    def test_empty_list(self):
        assert _calculate_weighted_coverage([]) == 0.0

    def test_missing_keys_default_zero(self):
        results = [{}]
        assert _calculate_weighted_coverage(results) == 0.0


class TestAggregateCounts:
    @pytest.mark.parametrize(
        "results,expected",
        [
            (
                [{"passed": 100, "failed": 5, "skipped": 3, "duration_seconds": 10.0}],
                {"total_tests": 108, "total_passed": 100, "total_failed": 5, "total_skipped": 3},
            ),
            (
                [
                    {"passed": 50, "failed": 2, "skipped": 1, "duration_seconds": 5.0},
                    {"passed": 30, "failed": 0, "skipped": 0, "duration_seconds": 3.0},
                ],
                {"total_passed": 80, "total_failed": 2, "total_duration_seconds": 8.0},
            ),
            (
                [{"passed": 0, "failed": 0, "skipped": 0, "duration_seconds": 0.0}],
                {"total_tests": 0, "pass_rate": 0},
            ),
        ],
    )
    def test_aggregate_counts_parametrized(self, results, expected):
        agg = _aggregate_counts(results)
        for key, value in expected.items():
            if key == "pass_rate":
                assert agg[key] == value
            elif key == "total_duration_seconds":
                assert agg[key] == value
            else:
                assert agg[key] == value

    def test_basic_aggregation(self):
        results = [
            {"passed": 10, "failed": 2, "skipped": 1, "duration_seconds": 5.0},
            {"passed": 20, "failed": 0, "skipped": 3, "duration_seconds": 10.0},
        ]
        agg = _aggregate_counts(results)
        assert agg["total_passed"] == 30
        assert agg["total_failed"] == 2
        assert agg["total_skipped"] == 4
        assert agg["total_tests"] == 36
        assert agg["total_duration_seconds"] == 15.0
        assert abs(agg["pass_rate"] - (30 / 36 * 100)) < 0.01

    def test_empty_list(self):
        agg = _aggregate_counts([])
        assert agg["total_tests"] == 0
        assert agg["pass_rate"] == 0

    def test_all_passed(self):
        results = [{"passed": 50, "failed": 0, "skipped": 0}]
        agg = _aggregate_counts(results)
        assert agg["pass_rate"] == 100.0

    def test_missing_keys(self):
        results = [{}]
        agg = _aggregate_counts(results)
        assert agg["total_tests"] == 0


class TestIsOllamaAvailable:
    def test_returns_bool(self):
        result = _is_ollama_available()
        assert isinstance(result, bool)


class TestGenerateSummaryReport:
    def test_basic_report(self, tmp_path):
        # Create a minimal valid project (needs src/ with .py and tests/)
        proj = tmp_path / "projects" / "demo"
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "__init__.py").write_text("")
        (proj / "src" / "core.py").write_text("x = 1\n")
        (proj / "tests").mkdir()
        (proj / "tests" / "__init__.py").write_text("")
        (proj / "manuscript").mkdir()
        (proj / "manuscript" / "config.yaml").write_text("paper:\n  title: Test\n")
        reports = proj / "output" / "reports"
        reports.mkdir(parents=True)
        test_data = {"project": {"passed": 5, "failed": 0, "coverage_percent": 90.0}}
        (reports / "test_results.json").write_text(json.dumps(test_data))

        report = generate_summary_report(tmp_path)
        assert "timestamp" in report
        assert "summary" in report
        assert "infrastructure" in report
        assert "projects" in report
        assert "demo" in report["projects"]

    def test_no_projects(self, tmp_path):
        (tmp_path / "projects").mkdir()
        report = generate_summary_report(tmp_path)
        assert report["projects"] == {}

    def test_report_has_metadata(self, tmp_path):
        (tmp_path / "projects").mkdir()
        report = generate_summary_report(tmp_path)
        assert "metadata" in report
        assert "active_projects" in report["metadata"]
        assert "files_generated" in report


class TestDiscoverActiveProjects:
    def test_finds_projects(self, tmp_path):
        p1 = tmp_path / "projects" / "alpha"
        p2 = tmp_path / "projects" / "beta"
        for p in [p1, p2]:
            (p / "src").mkdir(parents=True)
            (p / "src" / "__init__.py").write_text("")
            (p / "src" / "mod.py").write_text("x = 1\n")
            (p / "tests").mkdir()
            (p / "tests" / "__init__.py").write_text("")
        result = discover_active_projects(tmp_path)
        assert "alpha" in result
        assert "beta" in result

    def test_empty_projects_dir(self, tmp_path):
        (tmp_path / "projects").mkdir()
        result = discover_active_projects(tmp_path)
        assert result == []
