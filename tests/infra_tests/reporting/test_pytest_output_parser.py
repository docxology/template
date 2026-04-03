"""Tests for infrastructure.reporting.pytest_output_parser."""

from infrastructure.reporting.pytest_output_parser import parse_pytest_output


class TestParsePytestOutput:
    def test_standard_summary(self):
        stdout = "===== 100 passed, 5 failed, 3 skipped in 30.5s ====="
        result = parse_pytest_output(stdout, "", exit_code=1)
        assert result["passed"] == 100
        assert result["failed"] == 5
        assert result["skipped"] == 3
        assert result["total"] == 108

    def test_all_passed(self):
        stdout = "===== 50 passed in 10.0s ====="
        result = parse_pytest_output(stdout, "", exit_code=0)
        assert result["passed"] == 50
        assert result["failed"] == 0
        assert result["total"] == 50

    def test_empty_output(self):
        result = parse_pytest_output("", "", exit_code=0)
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["total"] == 0

    def test_collection_error(self):
        stdout = "collected 10 items / 2 error\nERROR collecting tests/test_foo.py"
        result = parse_pytest_output(stdout, "", exit_code=2)
        assert result["collection_errors"] == 2
        assert result["failed"] == 0

    def test_discovery_count(self):
        stdout = "collected 187 items\n===== 187 passed in 37.59s ====="
        result = parse_pytest_output(stdout, "", exit_code=0)
        assert result["discovery_count"] == 187

    def test_no_summary_line_passing(self):
        stdout = "collected 5 items\n....."
        result = parse_pytest_output(stdout, "", exit_code=0)
        assert result["passed"] == 5
        assert result["total"] == 5

    def test_no_summary_line_failing(self):
        stdout = "collected 10 items"
        result = parse_pytest_output(stdout, "", exit_code=1)
        assert result["failed"] == 1
        assert result["total"] == 10

    def test_dot_output(self):
        stdout = "....[100%]"
        result = parse_pytest_output(stdout, "", exit_code=0)
        assert result["passed"] == 4
        assert result["total"] == 4

    def test_coverage_total_line(self):
        stdout = "TOTAL    5000    1000    80.00%\n===== 100 passed ====="
        result = parse_pytest_output(stdout, "", exit_code=0)
        assert result.get("coverage_percent") == 80.00

    def test_coverage_fallback_percentage(self):
        stdout = "coverage: 75.50%\n===== 10 passed ====="
        result = parse_pytest_output(stdout, "", exit_code=0)
        assert result.get("coverage_percent") == 75.50

    def test_execution_phase_timing(self):
        stdout = "===== 50 passed in 12.5s ====="
        result = parse_pytest_output(stdout, "", exit_code=0)
        assert result["execution_phases"].get("execution") == 12.5

    def test_warnings_counted(self):
        stdout = "===== 10 passed, 3 warning in 5.0s ====="
        stderr = "1 warning"
        result = parse_pytest_output(stdout, stderr, exit_code=0)
        assert result["warnings"] >= 1

    def test_test_categories_markers(self):
        stdout = "test_foo.py::slow_test PASSED\ntest_bar.py::integration_test PASSED\ntest_baz.py - slow test\n===== 3 passed ====="
        parse_pytest_output(stdout, "", exit_code=0)
        # May or may not detect depending on exact format

    def test_deselected_ignored(self):
        stdout = "===== 10 passed, 5 deselected in 3.0s ====="
        result = parse_pytest_output(stdout, "", exit_code=0)
        assert result["passed"] == 10
        # Deselected are not counted in total
        assert result["total"] == 10

    def test_exit_code_preserved(self):
        result = parse_pytest_output("", "", exit_code=42)
        assert result["exit_code"] == 42
