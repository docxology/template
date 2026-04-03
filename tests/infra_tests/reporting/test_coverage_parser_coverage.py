"""Tests for infrastructure.reporting.coverage_parser — comprehensive coverage."""

import json

from infrastructure.reporting.coverage_parser import (
    _parse_failures_section,
    _parse_failures_verbose,
    _parse_failures_short,
    _parse_failures_timeout,
    _parse_failures_fallback,
    extract_failed_tests,
    extract_timeout_errors,
    check_test_failures,
    _wait_for_coverage_file,
    _parse_coverage_json,
    extract_coverage_percentage,
    MIN_VALID_COVERAGE_FILE_BYTES,
)


class TestParseFailuresSection:
    def test_typical_failure(self):
        output = (
            "======== FAILURES ========\n"
            "_____ TestExample _____\n"
            "/path/to/test.py:10: AssertionError: expected 1 got 2\n"
            "======== 1 failed, 5 passed durations ========\n"
        )
        result = _parse_failures_section(output)
        assert len(result) == 1
        assert result[0]["test"] == "TestExample"
        assert result[0]["error_type"] == "AssertionError"

    def test_no_failures_section(self):
        result = _parse_failures_section("all tests passed\n")
        assert result == []


class TestParseFailuresVerbose:
    def test_failed_line(self):
        output = "tests/test_foo.py::test_bar FAILED\n"
        result = _parse_failures_verbose(output)
        assert len(result) == 1
        assert "test_bar" in result[0]["test"]

    def test_no_failures(self):
        result = _parse_failures_verbose("tests/test_foo.py::test_bar PASSED\n")
        assert result == []

    def test_skip_summary_lines(self):
        output = "======== 1 FAILED ========\n"
        result = _parse_failures_verbose(output)
        assert result == []


class TestParseFailuresShort:
    def test_failed_line(self):
        output = "FAILED tests/test_foo.py::test_bar - AssertionError: bad\n"
        result = _parse_failures_short(output)
        assert len(result) == 1
        assert "test_bar" in result[0]["test"]
        assert result[0]["error_type"] == "AssertionError"

    def test_failed_no_dash(self):
        output = "FAILED tests/test_foo.py::test_bar\n"
        result = _parse_failures_short(output)
        assert len(result) == 1
        assert result[0]["error_type"] == "Unknown"

    def test_no_failures(self):
        result = _parse_failures_short("all passed\n")
        assert result == []


class TestParseFailuresTimeout:
    def test_timeout_with_context(self):
        output = (
            "tests/test_slow.py::test_thing FAILED\n"
            "some output\n"
            "pytest_timeout: Timeout >10s\n"
        )
        result = _parse_failures_timeout(output)
        assert len(result) >= 1
        assert result[0]["error_type"] == "TimeoutError"

    def test_no_timeout(self):
        result = _parse_failures_timeout("tests passed fine\n")
        assert result == []


class TestParseFailuresFallback:
    def test_failed_line(self):
        output = "FAILED tests/test_foo.py::test_bar\n"
        result = _parse_failures_fallback(output)
        assert len(result) == 1

    def test_no_failures(self):
        result = _parse_failures_fallback("all good\n")
        assert result == []


class TestExtractFailedTests:
    def test_cascading_strategies(self):
        # Uses verbose format
        result = extract_failed_tests(
            "tests/test_foo.py::test_bar FAILED\n", ""
        )
        assert len(result) >= 1

    def test_no_failures(self):
        result = extract_failed_tests("5 passed\n", "")
        assert result == []


class TestExtractTimeoutErrors:
    def test_timeout_detected(self):
        stdout = (
            "tests/test_slow.py::test_thing FAILED\n"
            "Timeout >10s exceeded\n"
        )
        result = extract_timeout_errors(stdout, "")
        assert len(result) >= 1
        assert result[0]["timeout_duration"] == "10s"

    def test_timeout_with_test_context(self):
        stdout = (
            "tests/test_slow.py::test_func FAILED\n"
            "output line\n"
            "timeout hit at 5.0 seconds\n"
        )
        result = extract_timeout_errors(stdout, "")
        assert len(result) >= 1

    def test_no_timeout(self):
        result = extract_timeout_errors("all passed\n", "")
        assert result == []


class TestCheckTestFailures:
    def test_no_failures(self, tmp_path):
        should_halt, msg = check_test_failures(0, "infra", tmp_path)
        assert should_halt is False
        assert "All tests passed" in msg

    def test_within_tolerance(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MAX_TEST_FAILURES", "5")
        should_halt, msg = check_test_failures(
            3, "infra", tmp_path, env_var="MAX_TEST_FAILURES"
        )
        assert should_halt is False
        assert "within tolerance" in msg

    def test_exceeds_tolerance(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MAX_TEST_FAILURES", "2")
        should_halt, msg = check_test_failures(
            5, "infra", tmp_path, env_var="MAX_TEST_FAILURES"
        )
        assert should_halt is True
        assert "exceeds tolerance" in msg

    def test_invalid_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MAX_TEST_FAILURES", "invalid")
        should_halt, msg = check_test_failures(
            1, "infra", tmp_path, env_var="MAX_TEST_FAILURES"
        )
        assert should_halt is True  # max_failures=0, so 1 > 0


class TestWaitForCoverageFile:
    def test_valid_file(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text("x" * (MIN_VALID_COVERAGE_FILE_BYTES + 10))
        result = _wait_for_coverage_file([f], max_retries=1, delay=0.01)
        assert result == f

    def test_file_too_small(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text("tiny")
        result = _wait_for_coverage_file([f], max_retries=1, delay=0.01)
        assert result is None

    def test_no_file(self, tmp_path):
        result = _wait_for_coverage_file(
            [tmp_path / "missing.json"], max_retries=1, delay=0.01
        )
        assert result is None

    def test_multiple_paths_first_valid(self, tmp_path):
        f1 = tmp_path / "a.json"
        f2 = tmp_path / "b.json"
        f2.write_text("x" * (MIN_VALID_COVERAGE_FILE_BYTES + 10))
        result = _wait_for_coverage_file([f1, f2], max_retries=1, delay=0.01)
        assert result == f2


class TestParseCoverageJson:
    def test_valid_json(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps({"totals": {"percent_covered": 85.5}}))
        result = _parse_coverage_json(f)
        assert result == 85.5

    def test_zero_coverage(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps({"totals": {"percent_covered": 0}}))
        result = _parse_coverage_json(f)
        assert result is None

    def test_corrupt_json(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text("{invalid json")
        result = _parse_coverage_json(f)
        assert result is None

    def test_missing_totals(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps({"other": "data"}))
        result = _parse_coverage_json(f)
        assert result is None


class TestExtractCoveragePercentage:
    def test_from_json(self, tmp_path):
        f = tmp_path / "coverage.json"
        data = {"totals": {"percent_covered": 82.3}}
        content = json.dumps(data)
        f.write_text(content + " " * MIN_VALID_COVERAGE_FILE_BYTES)
        found, pct = extract_coverage_percentage("", [f])
        assert found is True
        assert pct == 82.3

    def test_from_stdout_total(self):
        stdout = "TOTAL    1000    200    80.00%\n"
        found, pct = extract_coverage_percentage(stdout, [])
        assert found is True
        assert pct == 80.0

    def test_from_stdout_simple(self):
        stdout = "Coverage: 75.5%\n"
        found, pct = extract_coverage_percentage(stdout, [])
        assert found is True
        assert pct == 75.5

    def test_not_found(self):
        found, pct = extract_coverage_percentage("no coverage info", [])
        assert found is False
        assert pct is None
