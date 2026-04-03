"""Tests for infrastructure.reporting.pytest_output_parser — comprehensive coverage."""

from infrastructure.reporting.pytest_output_parser import parse_pytest_output


class TestParsePytestOutput:
    def test_typical_summary(self):
        stdout = "collected 100 items\n100 passed, 2 skipped in 5.5s\n"
        result = parse_pytest_output(stdout, "", 0)
        assert result["passed"] == 100
        assert result["skipped"] == 2
        assert result["failed"] == 0
        assert result["total"] == 102

    def test_with_failures(self):
        stdout = "3 failed, 97 passed, 1 skipped in 10.0s\n"
        result = parse_pytest_output(stdout, "", 1)
        assert result["failed"] == 3
        assert result["passed"] == 97
        assert result["skipped"] == 1

    def test_collection_error(self):
        stdout = "collected 50 items / 2 error\n"
        result = parse_pytest_output(stdout, "", 2)
        assert result["collection_errors"] == 2
        assert result["failed"] == 0

    def test_no_summary_exit_zero(self):
        stdout = "collected 10 items\n..........\n"
        result = parse_pytest_output(stdout, "", 0)
        assert result["passed"] == 10
        assert result["total"] == 10

    def test_no_summary_exit_nonzero(self):
        stdout = "collected 10 items\n..F.......\n"
        result = parse_pytest_output(stdout, "", 1)
        assert result["failed"] == 1
        assert result["total"] == 10

    def test_dots_only_exit_zero(self):
        stdout = ".........\n[100%]\n"
        result = parse_pytest_output(stdout, "", 0)
        assert result["passed"] > 0

    def test_coverage_total_line(self):
        stdout = "TOTAL    5000    1000    80.00%\n"
        result = parse_pytest_output(stdout, "", 0)
        assert result["coverage_percent"] == 80.0

    def test_coverage_fallback(self):
        stdout = "Coverage: 75.5%\n"
        result = parse_pytest_output(stdout, "", 0)
        assert result["coverage_percent"] == 75.5

    def test_warnings_count(self):
        stdout = "1 warning in output\n"
        stderr = "another warning here\n"
        result = parse_pytest_output(stdout, stderr, 0)
        assert result["warnings"] == 2

    def test_execution_phase_timing(self):
        stdout = "10 passed in 5.2s\n"
        result = parse_pytest_output(stdout, "", 0)
        assert result["execution_phases"].get("execution") == 5.2

    def test_marker_categories(self):
        stdout = "::slow test1\n::slow test2\n::integration test3\n"
        result = parse_pytest_output(stdout, "", 0)
        assert result["test_categories"].get("slow", 0) >= 2
        assert result["test_categories"].get("integration", 0) >= 1

    def test_empty_output(self):
        result = parse_pytest_output("", "", 0)
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["total"] == 0

    def test_discovery_count(self):
        stdout = "collected 42 items\n42 passed in 3.0s\n"
        result = parse_pytest_output(stdout, "", 0)
        assert result["discovery_count"] == 42
