"""Tests for infrastructure.reporting.markdown_formatter module.

Tests markdown report generation and console summary formatting.
"""

from __future__ import annotations

import pytest

from infrastructure.reporting.markdown_formatter import (
    _format_console_summary,
    generate_markdown_report,
)


def _make_report_data(
    overall_success: bool = True,
    infra_passed: int = 100,
    infra_failed: int = 0,
    infra_skipped: int = 5,
    infra_coverage: float = 75.0,
    projects: dict | None = None,
) -> dict:
    """Build a minimal valid report_data dictionary for testing."""
    data = {
        "timestamp": "2026-01-15T10:30:00",
        "test_type": "full",
        "overall_success": overall_success,
        "summary": {
            "total_tests": infra_passed + infra_failed + infra_skipped,
            "total_passed": infra_passed,
            "total_failed": infra_failed,
            "total_skipped": infra_skipped,
            "pass_rate": (infra_passed / max(infra_passed + infra_failed, 1)) * 100,
            "weighted_coverage_percent": infra_coverage,
            "total_duration_seconds": 120.5,
        },
        "infrastructure": {
            "exit_code": 0 if infra_failed == 0 else 1,
            "passed": infra_passed,
            "failed": infra_failed,
            "skipped": infra_skipped,
            "warnings": 3,
            "coverage_percent": infra_coverage,
            "meets_threshold": infra_coverage >= 60.0,
            "covered_lines": 5000,
            "total_lines": 6667,
            "duration_seconds": 90.5,
        },
        "metadata": {
            "infrastructure_tests_included": True,
            "integration_tests_included": False,
            "slow_tests_included": False,
            "ollama_tests_included": False,
            "ollama_server_available": False,
        },
        "files_generated": ["test_results_summary.json", "test_results_summary.md"],
    }
    if projects:
        data["projects"] = projects
    return data


class TestGenerateMarkdownReport:
    """Tests for generate_markdown_report."""

    def test_basic_report_structure(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "# Full Repository Test Suite Results" in md
        assert "## Summary" in md
        assert "## Infrastructure Tests" in md
        assert "## Test Configuration" in md
        assert "## Generated Files" in md

    def test_report_contains_timestamp(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "2026-01-15" in md

    def test_report_contains_pass_rate(self):
        data = _make_report_data(infra_passed=95, infra_failed=5)
        md = generate_markdown_report(data)
        assert "95.0%" in md

    def test_report_overall_passed(self):
        data = _make_report_data(overall_success=True)
        md = generate_markdown_report(data)
        assert "PASSED" in md

    def test_report_overall_failed(self):
        data = _make_report_data(overall_success=False, infra_failed=5)
        md = generate_markdown_report(data)
        assert "FAILED" in md

    def test_report_with_warnings(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "Warnings" in md

    def test_report_coverage_meets_threshold(self):
        data = _make_report_data(infra_coverage=75.0)
        md = generate_markdown_report(data)
        assert "meets" in md

    def test_report_coverage_below_threshold(self):
        data = _make_report_data(infra_coverage=50.0)
        md = generate_markdown_report(data)
        assert "below" in md

    def test_report_with_project(self):
        projects = {
            "code_project": {
                "exit_code": 0,
                "passed": 50,
                "failed": 0,
                "skipped": 2,
                "warnings": 0,
                "coverage_percent": 95.0,
                "meets_threshold": True,
                "covered_lines": 1000,
                "total_lines": 1053,
                "duration_seconds": 30.0,
            }
        }
        data = _make_report_data(projects=projects)
        md = generate_markdown_report(data)
        assert "Code Project Tests" in md
        assert "95.0%" in md

    def test_report_metadata_flags(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "Infrastructure Tests" in md
        assert "Included" in md

    def test_report_files_generated(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "test_results_summary.json" in md
        assert "test_results_summary.md" in md

    def test_report_with_active_projects_metadata(self):
        data = _make_report_data()
        data["metadata"]["active_projects"] = ["code_project", "template"]
        md = generate_markdown_report(data)
        assert "code_project" in md
        assert "template" in md

    def test_zero_warnings_no_warning_line(self):
        data = _make_report_data()
        data["infrastructure"]["warnings"] = 0
        md = generate_markdown_report(data)
        # Should not have a Warnings line for infrastructure
        lines = md.split("\n")
        infra_section_started = False
        for line in lines:
            if "## Infrastructure Tests" in line:
                infra_section_started = True
            if infra_section_started and line.startswith("## ") and "Infrastructure" not in line:
                break
            if infra_section_started and "**Warnings**" in line:
                pytest.fail("Warnings line should not appear when warnings is 0")


class TestFormatConsoleSummary:
    """Tests for _format_console_summary."""

    def test_basic_console_output(self):
        data = _make_report_data()
        output = _format_console_summary(data)
        assert "FULL REPOSITORY TEST SUITE SUMMARY" in output
        assert "PASSED" in output
        assert "Infrastructure" in output

    def test_console_output_with_projects(self):
        projects = {
            "my_project": {
                "passed": 50,
                "coverage_percent": 92.0,
            }
        }
        data = _make_report_data(projects=projects)
        output = _format_console_summary(data)
        assert "my_project" in output
        assert "92.0%" in output

    def test_console_long_project_name_truncated(self):
        projects = {
            "very_long_project_name_that_exceeds_limit": {
                "passed": 50,
                "coverage_percent": 92.0,
            }
        }
        data = _make_report_data(projects=projects)
        output = _format_console_summary(data)
        assert "..." in output

    def test_console_has_separator_lines(self):
        data = _make_report_data()
        output = _format_console_summary(data)
        assert "=" * 80 in output

    def test_console_shows_pass_rate(self):
        data = _make_report_data()
        output = _format_console_summary(data)
        assert "pass rate" in output

    def test_console_failed_overall(self):
        data = _make_report_data(overall_success=False)
        output = _format_console_summary(data)
        assert "FAILED" in output
