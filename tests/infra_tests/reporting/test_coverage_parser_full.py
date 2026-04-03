"""Tests for infrastructure.reporting.coverage_parser — comprehensive coverage."""

import json

from infrastructure.reporting.coverage_parser import (
    _parse_coverage_json,
    _parse_failures_fallback,
    _parse_failures_section,
    _parse_failures_short,
    _parse_failures_timeout,
    _parse_failures_verbose,
    _wait_for_coverage_file,
    check_test_failures,
    extract_coverage_percentage,
    extract_failed_tests,
    extract_timeout_errors,
)


class TestParseFailuresSection:
    def test_basic_failure(self):
        output = (
            "=== FAILURES ===\n"
            "__ test_foo __\n"
            "/path/to/test.py:10: AssertionError: expected True\n"
            "=== short test durations ===\n"
        )
        result = _parse_failures_section(output)
        assert len(result) == 1
        # The parser extracts either the test name from __ markers or filename
        assert result[0]["test"] in ("test_foo", "test.py")
        assert "AssertionError" in result[0]["error_type"]

    def test_no_failures_section(self):
        result = _parse_failures_section("=== 10 passed ===")
        assert result == []


class TestParseFailuresVerbose:
    def test_verbose_failed(self):
        output = "tests/test_foo.py::test_bar FAILED\ntests/test_baz.py::test_ok PASSED"
        result = _parse_failures_verbose(output)
        assert len(result) == 1
        assert "test_bar" in result[0]["test"]

    def test_no_failures(self):
        output = "tests/test_foo.py::test_bar PASSED"
        result = _parse_failures_verbose(output)
        assert result == []


class TestParseFailuresShort:
    def test_short_failed_with_dash(self):
        output = "FAILED tests/test_foo.py::test_bar - AssertionError: expected 1"
        result = _parse_failures_short(output)
        assert len(result) == 1
        assert result[0]["error_type"] == "AssertionError"
        assert "expected 1" in result[0]["error_message"]

    def test_short_failed_no_dash(self):
        output = "FAILED tests/test_foo.py::test_bar"
        result = _parse_failures_short(output)
        assert len(result) == 1
        assert result[0]["error_type"] == "Unknown"

    def test_no_failures(self):
        result = _parse_failures_short("all good")
        assert result == []


class TestParseFailuresTimeout:
    def test_timeout_found(self):
        output = (
            "tests/test_slow.py::test_slow_op FAILED\n"
            "more context\n"
            "more context\n"
            "pytest_timeout: Timeout >10s\n"
        )
        result = _parse_failures_timeout(output)
        assert len(result) >= 1

    def test_no_timeout(self):
        result = _parse_failures_timeout("tests passed fine")
        assert result == []


class TestParseFailuresFallback:
    def test_fallback_failed(self):
        output = "FAILED tests/test_x.py::test_y"
        result = _parse_failures_fallback(output)
        assert len(result) == 1
        assert "test_y" in result[0]["test"]

    def test_no_failures(self):
        result = _parse_failures_fallback("all passed")
        assert result == []


class TestExtractFailedTests:
    def test_with_failures(self):
        stdout = "FAILED tests/test_x.py::test_y - Error: boom"
        result = extract_failed_tests(stdout, "")
        assert len(result) >= 1

    def test_no_failures(self):
        result = extract_failed_tests("10 passed", "")
        assert result == []


class TestExtractTimeoutErrors:
    def test_timeout_found(self):
        stdout = "tests/test_slow.py::test_x FAILED\npytest_timeout: timeout 10.0s\n"
        result = extract_timeout_errors(stdout, "")
        assert len(result) >= 1
        assert "timeout" in result[0]["suggestion"].lower()

    def test_timeout_with_duration(self):
        stdout = "tests/test_foo.py::test_bar FAILED\ntimeout exceeded 5.0 seconds\n"
        result = extract_timeout_errors(stdout, "")
        assert len(result) >= 1
        assert "5.0s" in result[0]["timeout_duration"]

    def test_no_timeouts(self):
        result = extract_timeout_errors("all passed", "")
        assert result == []


class TestCheckTestFailures:
    def test_no_failures(self, tmp_path):
        exceeded, msg = check_test_failures(0, "infra", tmp_path)
        assert exceeded is False
        assert "All tests passed" in msg

    def test_failures_within_tolerance(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MAX_TEST_FAILURES", "5")
        exceeded, msg = check_test_failures(3, "infra", tmp_path)
        assert exceeded is False
        assert "within tolerance" in msg

    def test_failures_exceed_tolerance(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MAX_TEST_FAILURES", "2")
        exceeded, msg = check_test_failures(5, "infra", tmp_path)
        assert exceeded is True
        assert "exceeds tolerance" in msg

    def test_invalid_env_value(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MAX_TEST_FAILURES", "not_a_number")
        exceeded, msg = check_test_failures(1, "infra", tmp_path)
        assert exceeded is True


class TestWaitForCoverageFile:
    def test_file_ready(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps({"totals": {"percent_covered": 80}}) + " " * 100)
        result = _wait_for_coverage_file([f], max_retries=1)
        assert result == f

    def test_file_too_small(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text("{}")  # Too small
        result = _wait_for_coverage_file([f], max_retries=1, delay=0.01)
        assert result is None

    def test_no_files(self, tmp_path):
        result = _wait_for_coverage_file([tmp_path / "nonexistent.json"], max_retries=1, delay=0.01)
        assert result is None


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
        f.write_text("not valid json")
        result = _parse_coverage_json(f)
        assert result is None

    def test_missing_file(self, tmp_path):
        result = _parse_coverage_json(tmp_path / "nonexistent.json")
        assert result is None


class TestExtractCoveragePercentage:
    def test_from_json(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps({"totals": {"percent_covered": 75.0}}) + " " * 100)
        found, pct = extract_coverage_percentage("", [f])
        assert found is True
        assert pct == 75.0

    def test_from_stdout_total(self):
        stdout = "TOTAL    5000    1000    80.00%"
        found, pct = extract_coverage_percentage(stdout, [])
        assert found is True
        assert pct == 80.0

    def test_from_stdout_fallback(self):
        stdout = "coverage: 65.50%"
        found, pct = extract_coverage_percentage(stdout, [])
        assert found is True
        assert pct == 65.5

    def test_no_coverage(self):
        found, pct = extract_coverage_percentage("no coverage info here", [])
        assert found is False
        assert pct is None
