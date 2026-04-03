"""Tests for infrastructure/reporting/pipeline_test_runner.py.

Covers: TypedDict instantiation, discovery patterns, reporting helpers,
and the pure-logic portions of test pipeline orchestration.

No mocks used — all tests use real data structures and real function calls.
"""

from __future__ import annotations

import re


from infrastructure.reporting.pipeline_test_runner import (
    TestSuiteResults,
    _DISCOVERY_PATTERNS,
    _log_discovered_tests,
    _report_suite_failure,
    _report_suite_success,
    report_results,
)


class TestTestSuiteResults:
    """Test the TestSuiteResults TypedDict."""

    def test_empty_construction(self):
        """TestSuiteResults supports total=False (all keys optional)."""
        result: TestSuiteResults = {}
        assert isinstance(result, dict)

    def test_full_construction(self):
        """TestSuiteResults can be constructed with all fields."""
        result: TestSuiteResults = {
            "passed": 100,
            "failed": 2,
            "skipped": 5,
            "total": 107,
            "warnings": 3,
            "exit_code": 1,
            "discovery_count": 110,
            "collection_errors": 0,
            "execution_phases": {"setup": 1.0, "call": 5.0},
            "test_categories": {"unit": 80, "integration": 20},
            "coverage_percent": 85.5,
            "failed_tests": [{"test": "test_foo", "error_type": "AssertionError", "error_message": "failed"}],
        }
        assert result["passed"] == 100
        assert result["failed"] == 2
        assert result["coverage_percent"] == 85.5

    def test_partial_construction(self):
        """TestSuiteResults can be partially filled."""
        result: TestSuiteResults = {"passed": 50, "total": 50}
        assert result["passed"] == 50
        assert "failed" not in result


class TestDiscoveryPatterns:
    """Test the _DISCOVERY_PATTERNS regex list."""

    def test_patterns_are_valid_regex(self):
        """All discovery patterns should be valid regex."""
        for pattern in _DISCOVERY_PATTERNS:
            compiled = re.compile(pattern, re.IGNORECASE)
            assert compiled is not None

    def test_pattern_matches_collected(self):
        """Pattern should match '42 tests collected'."""
        text = "============== 42 tests collected =============="
        found = None
        for pattern in _DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found == 42

    def test_pattern_matches_collected_items(self):
        """Pattern should match 'collected 100 items'."""
        text = "collected 100 items"
        found = None
        for pattern in _DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found == 100

    def test_pattern_matches_found_tests(self):
        """Pattern should match 'found 5 tests'."""
        text = "found 5 tests"
        found = None
        for pattern in _DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found == 5

    def test_pattern_matches_tests_found(self):
        """Pattern should match '200 tests found'."""
        text = "200 tests found"
        found = None
        for pattern in _DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found == 200

    def test_pattern_no_match(self):
        """No pattern should match random text."""
        text = "Hello world, nothing to see here"
        found = None
        for pattern in _DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found is None


class TestLogDiscoveredTests:
    """Test the _log_discovered_tests function."""

    def test_log_discovered_tests_with_echo(self, tmp_path):
        """Test discovery with a simple command that outputs test count text."""
        import os
        cmd = ["echo", "collected 10 items"]
        env = os.environ.copy()
        # Should not raise - it just logs
        _log_discovered_tests(cmd, tmp_path, env, "unit")

    def test_log_discovered_tests_with_invalid_command(self, tmp_path):
        """Test discovery with a command that fails (shouldn't raise)."""
        import os
        cmd = ["false"]  # returns exit code 1
        env = os.environ.copy()
        # Should not raise even when command fails
        _log_discovered_tests(cmd, tmp_path, env, "unit")

    def test_log_discovered_tests_unparseable_output(self, tmp_path):
        """Test discovery when output contains no parseable count."""
        import os
        cmd = ["echo", "no count here"]
        env = os.environ.copy()
        _log_discovered_tests(cmd, tmp_path, env, "integration")


class TestReportSuiteFailure:
    """Test _report_suite_failure reporting."""

    def test_report_with_failed_tests(self):
        """Test failure report with failed test details."""
        results = {
            "failed": 3,
            "skipped": 1,
            "warnings": 2,
            "failed_tests": [
                {"test": "test_a", "error_type": "AssertionError", "error_message": "expected 1 got 2"},
                {"test": "test_b", "error_type": "TypeError", "error_message": "int not callable"},
                {"test": "test_c", "error_type": "Unknown", "error_message": ""},
            ],
        }
        # Should not raise
        _report_suite_failure("Infrastructure", results)

    def test_report_with_many_failures(self):
        """Test failure report truncates at 5."""
        failed_tests = [
            {"test": f"test_{i}", "error_type": "AssertionError", "error_message": f"msg {i}"}
            for i in range(10)
        ]
        results = {"failed": 10, "skipped": 0, "warnings": 0, "failed_tests": failed_tests}
        _report_suite_failure("Project", results, "myproject")

    def test_report_with_empty_results(self):
        """Test failure report with minimal results."""
        results = {"failed": 0, "skipped": 0, "warnings": 0, "failed_tests": []}
        _report_suite_failure("Infrastructure", results)

    def test_report_with_long_error_messages(self):
        """Test failure report with long error messages (truncated at 60)."""
        results = {
            "failed": 1,
            "skipped": 0,
            "warnings": 0,
            "failed_tests": [
                {
                    "test": "test_long_error",
                    "error_type": "AssertionError",
                    "error_message": "A" * 100,
                },
            ],
        }
        _report_suite_failure("Infrastructure", results)


class TestReportSuiteSuccess:
    """Test _report_suite_success reporting."""

    def test_report_success_with_coverage(self):
        """Test success report with coverage above threshold."""
        results = {
            "passed": 50,
            "skipped": 2,
            "coverage_percent": 85.5,
            "warnings": 1,
            "execution_phases": {"setup": 0.5, "call": 3.0, "teardown": 0.1},
        }
        report = {}
        _report_suite_success("Infrastructure", results, 60.0, report)

    def test_report_success_below_threshold(self):
        """Test success report with coverage below threshold."""
        results = {
            "passed": 50,
            "skipped": 0,
            "coverage_percent": 55.0,
            "warnings": 0,
            "execution_phases": {},
        }
        report = {}
        _report_suite_success("Project", results, 90.0, report)

    def test_report_success_no_phases(self):
        """Test success report with no execution phases."""
        results = {
            "passed": 10,
            "skipped": 0,
            "coverage_percent": 92.0,
            "warnings": 0,
        }
        report = {}
        _report_suite_success("Project", results, 90.0, report)


class TestReportResults:
    """Test the report_results comprehensive reporting function."""

    def test_all_passing(self):
        """Test report with both suites passing."""
        infra_results = {
            "passed": 100,
            "total": 100,
            "failed": 0,
            "coverage_percent": 83.0,
            "execution_phases": {"call": 5.0},
        }
        project_results = {
            "passed": 50,
            "total": 50,
            "failed": 0,
            "coverage_percent": 95.0,
            "execution_phases": {"call": 3.0},
        }
        report = {}
        # Should not raise
        report_results(0, 0, infra_results, project_results, report, "myproject")

    def test_infra_failing(self):
        """Test report with infra failing."""
        infra_results = {
            "passed": 90,
            "total": 100,
            "failed": 10,
            "coverage_percent": 80.0,
            "execution_phases": {"call": 5.0},
        }
        project_results = {
            "passed": 50,
            "total": 50,
            "failed": 0,
            "coverage_percent": 95.0,
            "execution_phases": {"call": 3.0},
        }
        report = {}
        report_results(1, 0, infra_results, project_results, report, "myproject")

    def test_project_failing(self):
        """Test report with project failing."""
        infra_results = {
            "passed": 100,
            "total": 100,
            "failed": 0,
            "coverage_percent": 83.0,
            "execution_phases": {"call": 5.0},
        }
        project_results = {
            "passed": 40,
            "total": 50,
            "failed": 10,
            "coverage_percent": 70.0,
            "execution_phases": {"call": 3.0},
        }
        report = {}
        report_results(0, 1, infra_results, project_results, report, "myproject")

    def test_infra_skipped(self):
        """Test report when infra tests were not run."""
        infra_results: dict = {}
        project_results = {
            "passed": 50,
            "total": 50,
            "failed": 0,
            "coverage_percent": 95.0,
            "execution_phases": {"call": 3.0},
        }
        report = {}
        report_results(0, 0, infra_results, project_results, report, "myproject")

    def test_collection_errors(self):
        """Test report with collection errors."""
        infra_results = {
            "passed": 0,
            "total": 0,
            "failed": 0,
            "collection_errors": 3,
            "discovery_count": 100,
            "coverage_percent": 0.0,
            "execution_phases": {},
        }
        project_results = {
            "passed": 50,
            "total": 50,
            "failed": 0,
            "coverage_percent": 95.0,
            "execution_phases": {},
        }
        report = {}
        report_results(1, 0, infra_results, project_results, report, "myproject")

    def test_both_failing(self):
        """Test report with both suites failing."""
        infra_results = {
            "passed": 90,
            "total": 100,
            "failed": 10,
            "coverage_percent": 80.0,
            "execution_phases": {},
        }
        project_results = {
            "passed": 40,
            "total": 50,
            "failed": 10,
            "coverage_percent": 70.0,
            "execution_phases": {},
        }
        report = {}
        report_results(1, 1, infra_results, project_results, report, "myproject")

    def test_success_no_duration(self):
        """Test success report with zero-duration phases."""
        infra_results = {
            "passed": 5,
            "total": 5,
            "failed": 0,
            "coverage_percent": 100.0,
            "execution_phases": {},
        }
        project_results = {
            "passed": 5,
            "total": 5,
            "failed": 0,
            "coverage_percent": 100.0,
            "execution_phases": {},
        }
        report = {}
        report_results(0, 0, infra_results, project_results, report, "myproject")
