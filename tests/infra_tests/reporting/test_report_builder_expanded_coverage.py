"""Tests for infrastructure.reporting.report_builder — expanded coverage."""

from infrastructure.reporting.report_builder import (
    _calculate_weighted_coverage,
    _aggregate_counts,
    _is_ollama_available,
)


class TestCalculateWeightedCoverage:
    def test_single_suite(self):
        results = [{"coverage_percent": 80.0, "total_lines": 1000}]
        assert _calculate_weighted_coverage(results) == 80.0

    def test_multiple_suites(self):
        results = [
            {"coverage_percent": 90.0, "total_lines": 900},
            {"coverage_percent": 60.0, "total_lines": 100},
        ]
        expected = (90.0 * 900 + 60.0 * 100) / 1000
        assert abs(_calculate_weighted_coverage(results) - expected) < 0.01

    def test_zero_lines(self):
        results = [{"coverage_percent": 80.0, "total_lines": 0}]
        assert _calculate_weighted_coverage(results) == 0.0

    def test_empty_list(self):
        assert _calculate_weighted_coverage([]) == 0.0

    def test_missing_keys(self):
        results = [{}]
        assert _calculate_weighted_coverage(results) == 0.0


class TestAggregateCounts:
    def test_single_suite(self):
        results = [{"passed": 100, "failed": 5, "skipped": 3, "duration_seconds": 10.0}]
        counts = _aggregate_counts(results)
        assert counts["total_tests"] == 108
        assert counts["total_passed"] == 100
        assert counts["total_failed"] == 5
        assert counts["total_skipped"] == 3
        assert abs(counts["pass_rate"] - (100 / 108 * 100)) < 0.1
        assert counts["total_duration_seconds"] == 10.0

    def test_multiple_suites(self):
        results = [
            {"passed": 50, "failed": 2, "skipped": 1, "duration_seconds": 5.0},
            {"passed": 30, "failed": 0, "skipped": 0, "duration_seconds": 3.0},
        ]
        counts = _aggregate_counts(results)
        assert counts["total_passed"] == 80
        assert counts["total_failed"] == 2
        assert counts["total_duration_seconds"] == 8.0

    def test_zero_tests(self):
        results = [{"passed": 0, "failed": 0, "skipped": 0, "duration_seconds": 0.0}]
        counts = _aggregate_counts(results)
        assert counts["total_tests"] == 0
        assert counts["pass_rate"] == 0

    def test_empty_list(self):
        counts = _aggregate_counts([])
        assert counts["total_tests"] == 0
        assert counts["pass_rate"] == 0

    def test_missing_keys(self):
        results = [{}]
        counts = _aggregate_counts(results)
        assert counts["total_tests"] == 0


class TestIsOllamaAvailable:
    def test_returns_bool(self):
        result = _is_ollama_available()
        assert isinstance(result, bool)
