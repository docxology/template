"""Tests for infrastructure/reporting/coverage_parser.py.

Uses real pytest-style output strings and real temp files — no mocks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.reporting.coverage_parser import (
    MIN_VALID_COVERAGE_FILE_BYTES,
    _parse_coverage_json,
    _parse_failures_fallback,
    _parse_failures_section,
    _parse_failures_short,
    _parse_failures_timeout,
    _parse_failures_verbose,
    _wait_for_coverage_file,
    check_cov_datafile_support,
    check_test_failures,
    extract_coverage_percentage,
    extract_failed_tests,
    extract_timeout_errors,
)


FAILURES_SECTION_OUTPUT = """\
===================== FAILURES ======================
__ testSomething __
/path/to/test_file.py:42: AssertionError: expected 1, got 2
=========================== short test summary info ============================
"""

VERBOSE_OUTPUT = """\
tests/test_foo.py::test_bar FAILED
tests/test_foo.py::test_baz PASSED
"""

SHORT_OUTPUT = """\
FAILED tests/test_foo.py::test_one - AssertionError: expected True
FAILED tests/test_bar.py::test_two
"""

TIMEOUT_OUTPUT = """\
tests/test_slow.py::test_long FAILED
E   Timeout: test timed out after 10 seconds
"""


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
        assert result[0]["test"] in ("test_foo", "test.py")
        assert "AssertionError" in result[0]["error_type"]

    def test_no_failures_section(self):
        assert _parse_failures_section("=== 10 passed ===") == []


class TestParseFailuresVerbose:
    def test_verbose_failed(self):
        output = "tests/test_foo.py::test_bar FAILED\ntests/test_baz.py::test_ok PASSED"
        result = _parse_failures_verbose(output)
        assert len(result) == 1
        assert "test_bar" in result[0]["test"]

    def test_no_failures(self):
        assert _parse_failures_verbose("tests/test_foo.py::test_bar PASSED") == []


class TestParseFailuresShort:
    @pytest.mark.parametrize(
        "output,expected_type,message_fragment",
        [
            ("FAILED tests/test_foo.py::test_bar - AssertionError: expected 1", "AssertionError", "expected 1"),
            ("FAILED tests/test_foo.py::test_bar", "Unknown", None),
        ],
    )
    def test_short_failed(self, output, expected_type, message_fragment):
        result = _parse_failures_short(output)
        assert len(result) == 1
        assert result[0]["error_type"] == expected_type
        if message_fragment:
            assert message_fragment in result[0]["error_message"]

    def test_no_failures(self):
        assert _parse_failures_short("all good") == []


class TestParseFailuresTimeout:
    def test_timeout_found(self):
        output = "tests/test_slow.py::test_slow_op FAILED\nmore context\nmore context\npytest_timeout: Timeout >10s\n"
        assert len(_parse_failures_timeout(output)) >= 1

    def test_no_timeout(self):
        assert _parse_failures_timeout("tests passed fine") == []


class TestParseFailuresFallback:
    def test_fallback_failed(self):
        result = _parse_failures_fallback("FAILED tests/test_x.py::test_y")
        assert len(result) == 1
        assert "test_y" in result[0]["test"]

    def test_no_failures(self):
        assert _parse_failures_fallback("all passed") == []


class TestExtractFailedTests:
    def test_prefers_section_strategy(self):
        results = extract_failed_tests(FAILURES_SECTION_OUTPUT, "")
        assert len(results) == 1
        assert results[0]["test"] == "testSomething"
        assert results[0]["error_type"] == "AssertionError"

    def test_falls_back_to_short_when_no_section(self):
        results = extract_failed_tests(SHORT_OUTPUT, "")
        assert len(results) == 2
        tests = [r["test"] for r in results]
        assert "tests/test_foo.py::test_one" in tests
        assert "tests/test_bar.py::test_two" in tests

    def test_short_strategy_extracts_error_type(self):
        results = extract_failed_tests(SHORT_OUTPUT, "")
        one = next(r for r in results if "test_one" in r["test"])
        assert one["error_type"] == "AssertionError"

    def test_falls_back_to_verbose_format(self):
        results = extract_failed_tests(VERBOSE_OUTPUT, "")
        assert len(results) == 1
        assert results[0]["test"] == "tests/test_foo.py::test_bar"

    def test_timeout_output_detected(self):
        results = extract_failed_tests(TIMEOUT_OUTPUT, "")
        # The timeout parser may not win over the verbose parser; at minimum a failure is detected
        assert len(results) >= 1
        assert any("test_long" in r["test"] for r in results)

    def test_returns_empty_on_clean_run(self):
        assert extract_failed_tests("1 passed in 0.1s", "") == []

    def test_fallback_for_plain_failed_line(self):
        results = extract_failed_tests("FAILED tests/test_x.py::test_y", "")
        assert len(results) == 1
        assert results[0]["test"] == "tests/test_x.py::test_y"


class TestExtractTimeoutErrors:
    def test_detects_timeout_keyword(self):
        errors = extract_timeout_errors("", "Timeout: test timed out after 10 seconds")
        assert len(errors) >= 1
        assert errors[0]["timeout_duration"] == "10s"

    def test_timeout_with_duration(self):
        stdout = "tests/test_foo.py::test_bar FAILED\ntimeout exceeded 5.0 seconds\n"
        result = extract_timeout_errors(stdout, "")
        assert len(result) >= 1
        assert "5.0s" in result[0]["timeout_duration"]

    def test_empty_on_no_timeout(self):
        assert extract_timeout_errors("all passed", "") == []


class TestExtractCoveragePercentage:
    def test_reads_from_real_json_file(self, tmp_path: Path):
        cov_json = tmp_path / "coverage.json"
        cov_data = {
            "totals": {
                "percent_covered": 82.5,
                "num_statements": 100,
                "covered_lines": 82,
                "missing_lines": 18,
            }
        }
        cov_json.write_text(json.dumps(cov_data))
        found, pct = extract_coverage_percentage("", [cov_json])
        assert found is True
        assert pct == pytest.approx(82.5)

    def test_falls_back_to_stdout_when_no_json(self, tmp_path: Path):
        stdout = "TOTAL    100     18    82.00%"
        found, pct = extract_coverage_percentage(stdout, [tmp_path / "nonexistent.json"])
        assert found is True
        assert pct == pytest.approx(82.0)

    def test_returns_not_found_when_nothing(self, tmp_path: Path):
        found, pct = extract_coverage_percentage("no coverage here", [tmp_path / "missing.json"])
        assert found is False
        assert pct is None

    def test_skips_small_json_file(self, tmp_path: Path):
        tiny = tmp_path / "tiny.json"
        tiny.write_text("{}")  # < 100 bytes
        found, _pct = extract_coverage_percentage("", [tiny])
        assert found is False

    @pytest.mark.parametrize(
        "stdout,expected_pct",
        [
            ("TOTAL    5000    1000    80.00%", 80.0),
            ("coverage: 65.50%", 65.5),
        ],
    )
    def test_from_stdout_patterns(self, stdout, expected_pct):
        found, pct = extract_coverage_percentage(stdout, [])
        assert found is True
        assert pct == pytest.approx(expected_pct)


class TestCheckCovDatafileSupport:
    def test_returns_bool(self):
        result = check_cov_datafile_support()
        assert isinstance(result, bool)

    def test_result_matches_actual_pytest_help(self):
        # Verify the function correctly reflects whether --cov-datafile is in pytest --help
        import subprocess

        result = subprocess.run(
            ["python", "-m", "pytest", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        expected = "--cov-datafile" in result.stdout
        assert check_cov_datafile_support() == expected


class TestCheckTestFailures:
    def test_no_failures(self, tmp_path: Path) -> None:
        should_halt, msg = check_test_failures(0, "infra", tmp_path)
        assert should_halt is False
        assert "All tests passed" in msg

    def test_within_tolerance(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MAX_TEST_FAILURES", "5")
        should_halt, msg = check_test_failures(3, "infra", tmp_path, env_var="MAX_TEST_FAILURES")
        assert should_halt is False
        assert "within tolerance" in msg

    def test_exceeds_tolerance(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MAX_TEST_FAILURES", "2")
        should_halt, msg = check_test_failures(5, "infra", tmp_path, env_var="MAX_TEST_FAILURES")
        assert should_halt is True
        assert "exceeds tolerance" in msg

    def test_invalid_env_value(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MAX_TEST_FAILURES", "not_a_number")
        should_halt, _msg = check_test_failures(1, "infra", tmp_path, env_var="MAX_TEST_FAILURES")
        assert should_halt is True


class TestParseCoverageJson:
    def test_valid_json(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text(json.dumps({"totals": {"percent_covered": 85.5}}), encoding="utf-8")
        assert _parse_coverage_json(cov) == pytest.approx(85.5)

    def test_zero_coverage(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text(json.dumps({"totals": {"percent_covered": 0}}), encoding="utf-8")
        assert _parse_coverage_json(cov) is None

    def test_corrupt_json_returns_none(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text("{invalid", encoding="utf-8")
        assert _parse_coverage_json(cov) is None

    def test_missing_file(self, tmp_path: Path) -> None:
        assert _parse_coverage_json(tmp_path / "nonexistent.json") is None


class TestWaitForCoverageFile:
    def test_valid_file(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text("x" * (MIN_VALID_COVERAGE_FILE_BYTES + 10), encoding="utf-8")
        assert _wait_for_coverage_file([cov], max_retries=1, delay=0.01) == cov

    def test_file_too_small(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text("{}", encoding="utf-8")
        assert _wait_for_coverage_file([cov], max_retries=1, delay=0.01) is None

    def test_no_files(self, tmp_path: Path) -> None:
        assert _wait_for_coverage_file([tmp_path / "nonexistent.json"], max_retries=1, delay=0.01) is None
