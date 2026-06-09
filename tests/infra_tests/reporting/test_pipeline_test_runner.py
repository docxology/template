"""Tests for infrastructure/reporting/pipeline_test_runner.py.

Covers: TypedDict instantiation, discovery patterns, reporting helpers,
and the pure-logic portions of test pipeline orchestration.

No mocks used — all tests use real data structures and real function calls.
"""

from __future__ import annotations

import logging
import re


from infrastructure.core.pytest_orchestration import (
    DISCOVERY_PATTERNS,
    PIPELINE_SMOKE_INFRA_TEST_PATHS,
    log_discovered_tests,
    parse_test_discovery_timeout,
    resolve_infrastructure_test_paths,
)
from infrastructure.reporting.pipeline_test_reporting import (
    _report_suite_failure,
    _report_suite_success,
    report_results,
)
from infrastructure.reporting.pipeline_test_runner import (
    INFRASTRUCTURE_TEST_SCOPES,
    TestSuiteResults,
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
    """Test the DISCOVERY_PATTERNS regex list."""

    def test_patterns_are_valid_regex(self):
        """All discovery patterns should be valid regex."""
        for pattern in DISCOVERY_PATTERNS:
            compiled = re.compile(pattern, re.IGNORECASE)
            assert compiled is not None

    def test_pattern_matches_collected(self):
        """Pattern should match '42 tests collected'."""
        text = "============== 42 tests collected =============="
        found = None
        for pattern in DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found == 42

    def test_pattern_matches_collected_items(self):
        """Pattern should match 'collected 100 items'."""
        text = "collected 100 items"
        found = None
        for pattern in DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found == 100

    def test_pattern_matches_found_tests(self):
        """Pattern should match 'found 5 tests'."""
        text = "found 5 tests"
        found = None
        for pattern in DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found == 5

    def test_pattern_matches_tests_found(self):
        """Pattern should match '200 tests found'."""
        text = "200 tests found"
        found = None
        for pattern in DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found == 200

    def test_pattern_no_match(self):
        """No pattern should match random text."""
        text = "Hello world, nothing to see here"
        found = None
        for pattern in DISCOVERY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = int(match.group(1))
                break
        assert found is None


class TestInfrastructureTestScopes:
    """Test infrastructure suite scope selection."""

    def test_scopes_are_public_choices(self):
        """CLI choices expose full and pipeline-smoke scopes."""
        assert INFRASTRUCTURE_TEST_SCOPES == ("full", "pipeline-smoke")

    def test_full_scope_uses_repo_suite_and_integration(self, tmp_path):
        """Full scope covers the complete infrastructure and integration tree."""
        paths = resolve_infrastructure_test_paths(tmp_path, "full")

        assert str(tmp_path / "tests" / "infra_tests") in paths
        assert str(tmp_path / "tests" / "integration") in paths
        assert any("test_module_interoperability.py" in path for path in paths)

    def test_pipeline_smoke_scope_uses_curated_real_contract(self, tmp_path):
        """Pipeline smoke stays focused on core contracts instead of the whole repo suite."""
        paths = resolve_infrastructure_test_paths(tmp_path, "pipeline-smoke")

        assert paths == [str(tmp_path / relative_path) for relative_path in PIPELINE_SMOKE_INFRA_TEST_PATHS]
        assert all("tests/infra_tests" in path for path in paths)
        assert not any("tests/integration" in path for path in paths)

    def test_unknown_scope_fails_fast(self, tmp_path):
        """Unknown scopes are rejected instead of silently falling back."""
        import pytest

        with pytest.raises(ValueError, match="Unknown infrastructure test scope"):
            resolve_infrastructure_test_paths(tmp_path, "everything")  # type: ignore[arg-type]

    def test_discovery_timeout_defaults_by_scope(self, monkeypatch):
        """Full discovery gets a longer timeout than pipeline smoke."""
        monkeypatch.delenv("TEST_DISCOVERY_TIMEOUT_SEC", raising=False)

        assert parse_test_discovery_timeout("full") == 120.0
        assert parse_test_discovery_timeout("pipeline-smoke") == 30.0

    def test_discovery_timeout_env_override(self, monkeypatch):
        """Discovery timeout can be raised locally for large checkouts."""
        monkeypatch.setenv("TEST_DISCOVERY_TIMEOUT_SEC", "45")

        assert parse_test_discovery_timeout("full") == 45.0


class TestLogDiscoveredTests:
    """Test the log_discovered_tests function."""

    def testlog_discovered_tests_with_echo(self, tmp_path):
        """Test discovery with a simple command that outputs test count text."""
        import os

        cmd = ["echo", "collected 10 items"]
        env = os.environ.copy()
        # Should not raise - it just logs
        log_discovered_tests(cmd, tmp_path, env, "unit")

    def testlog_discovered_tests_with_invalid_command(self, tmp_path):
        """Test discovery with a command that fails (shouldn't raise)."""
        import os

        cmd = ["false"]  # returns exit code 1
        env = os.environ.copy()
        # Should not raise even when command fails
        log_discovered_tests(cmd, tmp_path, env, "unit")

    def testlog_discovered_tests_unparseable_output(self, tmp_path):
        """Test discovery when output contains no parseable count."""
        import os

        cmd = ["echo", "no count here"]
        env = os.environ.copy()
        log_discovered_tests(cmd, tmp_path, env, "integration")


class TestReportSuiteFailure:
    """Test _report_suite_failure reporting."""

    def test_report_with_failed_tests(self, caplog):
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
        with caplog.at_level(logging.INFO):
            _report_suite_failure("Infrastructure", results)
        assert "Failed: 3 test(s) failed" in caplog.text
        assert "test_a" in caplog.text
        assert "AssertionError: expected 1 got 2" in caplog.text
        # Unknown error types must not emit a detail line.
        assert "Unknown:" not in caplog.text

    def test_report_with_many_failures(self, caplog):
        """Test failure report truncates at 5."""
        failed_tests = [
            {"test": f"test_{i}", "error_type": "AssertionError", "error_message": f"msg {i}"} for i in range(10)
        ]
        results = {"failed": 10, "skipped": 0, "warnings": 0, "failed_tests": failed_tests}
        with caplog.at_level(logging.INFO):
            _report_suite_failure("Project", results, "myproject")
        assert "test_4" in caplog.text
        assert "test_5" not in caplog.text  # truncated after 5 entries
        assert "and 5 more failures" in caplog.text

    def test_report_with_empty_results(self, caplog):
        """Test failure report with minimal results."""
        results = {"failed": 0, "skipped": 0, "warnings": 0, "failed_tests": []}
        with caplog.at_level(logging.INFO):
            _report_suite_failure("Infrastructure", results)
        assert "Failed: 0 test(s) failed" in caplog.text
        assert "Failed Tests:" not in caplog.text

    def test_report_with_long_error_messages(self, caplog):
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
        with caplog.at_level(logging.INFO):
            _report_suite_failure("Infrastructure", results)
        assert "A" * 60 + "..." in caplog.text
        assert "A" * 61 not in caplog.text


class TestReportSuiteSuccess:
    """Test _report_suite_success reporting."""

    def test_report_success_with_coverage(self, caplog):
        """Test success report with coverage above threshold."""
        results = {
            "passed": 50,
            "skipped": 2,
            "coverage_percent": 85.5,
            "warnings": 1,
            "execution_phases": {"setup": 0.5, "call": 3.0, "teardown": 0.1},
        }
        report = {}
        with caplog.at_level(logging.INFO):
            _report_suite_success("Infrastructure", results, 60.0, report)
        assert "50" in caplog.text
        assert "85.5" in caplog.text

    def test_report_success_below_threshold(self, caplog):
        """Test success report with coverage below threshold."""
        results = {
            "passed": 50,
            "skipped": 0,
            "coverage_percent": 55.0,
            "warnings": 0,
            "execution_phases": {},
        }
        report = {}
        with caplog.at_level(logging.INFO):
            _report_suite_success("Project", results, 90.0, report)
        assert "55.0" in caplog.text

    def test_report_success_no_phases(self, caplog):
        """Test success report with no execution phases."""
        results = {
            "passed": 10,
            "skipped": 0,
            "coverage_percent": 92.0,
            "warnings": 0,
        }
        report = {}
        with caplog.at_level(logging.INFO):
            _report_suite_success("Project", results, 90.0, report)
        assert "92.0" in caplog.text


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


class TestReportInfraOnlyResults:
    def test_success_path(self):
        from infrastructure.reporting.pipeline_test_reporting import report_infra_only_results

        report_infra_only_results(0, {"passed": 3, "total": 3, "failed": 0, "failed_tests": []})

    def test_failure_lists_failed_tests(self):
        from infrastructure.reporting.pipeline_test_reporting import report_infra_only_results

        report_infra_only_results(
            1,
            {
                "passed": 1,
                "total": 2,
                "failed": 1,
                "failed_tests": [{"test": "t::x", "error_type": "Assert", "error_message": "boom"}],
            },
        )
