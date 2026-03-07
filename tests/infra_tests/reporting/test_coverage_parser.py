"""Tests for infrastructure/reporting/coverage_parser.py.

Uses real pytest-style output strings and real temp files — no mocks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.reporting.coverage_parser import (
    _parse_failures_fallback,
    _parse_failures_section,
    _parse_failures_short,
    _parse_failures_timeout,
    _parse_failures_verbose,
    check_cov_datafile_support,
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
    def test_extracts_test_from_failures_section(self):
        results = _parse_failures_section(FAILURES_SECTION_OUTPUT)
        assert len(results) == 1
        assert results[0]["test"] == "testSomething"
        assert results[0]["error_type"] == "AssertionError"

    def test_returns_empty_for_unrelated_output(self):
        assert _parse_failures_section("no failures here") == []


class TestParseFailuresVerbose:
    def test_extracts_failed_from_verbose(self):
        results = _parse_failures_verbose(VERBOSE_OUTPUT)
        assert len(results) == 1
        assert results[0]["test"] == "tests/test_foo.py::test_bar"

    def test_ignores_passed_lines(self):
        results = _parse_failures_verbose("tests/foo.py::test_x PASSED")
        assert results == []


class TestParseFailuresShort:
    def test_extracts_from_short_lines(self):
        results = _parse_failures_short(SHORT_OUTPUT)
        assert len(results) == 2
        tests = [r["test"] for r in results]
        assert "tests/test_foo.py::test_one" in tests
        assert "tests/test_bar.py::test_two" in tests

    def test_extracts_error_type_when_present(self):
        results = _parse_failures_short(SHORT_OUTPUT)
        one = next(r for r in results if "test_one" in r["test"])
        assert one["error_type"] == "AssertionError"


class TestParseFailuresTimeout:
    def test_extracts_timeout_context(self):
        results = _parse_failures_timeout(TIMEOUT_OUTPUT)
        assert len(results) == 1
        assert results[0]["error_type"] == "TimeoutError"

    def test_empty_on_no_timeout(self):
        assert _parse_failures_timeout("no timeouts here") == []


class TestParseFailuresFallback:
    def test_extracts_failed_line(self):
        output = "FAILED tests/test_x.py::test_y"
        results = _parse_failures_fallback(output)
        assert len(results) == 1
        assert results[0]["test"] == "tests/test_x.py::test_y"

    def test_empty_on_no_matches(self):
        assert _parse_failures_fallback("nothing here") == []


class TestExtractFailedTests:
    def test_prefers_section_strategy(self):
        results = extract_failed_tests(FAILURES_SECTION_OUTPUT, "")
        assert len(results) == 1
        assert results[0]["test"] == "testSomething"

    def test_falls_back_to_short_when_no_section(self):
        results = extract_failed_tests(SHORT_OUTPUT, "")
        assert len(results) == 2

    def test_returns_empty_on_clean_run(self):
        assert extract_failed_tests("1 passed in 0.1s", "") == []


class TestExtractTimeoutErrors:
    def test_detects_timeout_keyword(self):
        errors = extract_timeout_errors("", "Timeout: test timed out after 10 seconds")
        assert len(errors) >= 1
        assert errors[0]["timeout_duration"] == "10s"

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


class TestCheckCovDatafileSupport:
    def test_returns_bool(self):
        result = check_cov_datafile_support()
        assert isinstance(result, bool)
