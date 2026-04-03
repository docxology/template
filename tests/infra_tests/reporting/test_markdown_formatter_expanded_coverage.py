"""Tests for infrastructure.reporting.markdown_formatter — expanded coverage."""

from infrastructure.reporting.markdown_formatter import (
    generate_markdown_report,
    _format_console_summary,
)


def _make_report_data(
    overall_success=True,
    infra_coverage=82.0,
    projects=None,
    warnings=0,
):
    """Build a minimal report_data dict for testing."""
    data = {
        "timestamp": "2025-01-15T12:00:00",
        "test_type": "full",
        "overall_success": overall_success,
        "summary": {
            "total_tests": 5000,
            "total_passed": 4990,
            "total_failed": 5,
            "total_skipped": 5,
            "pass_rate": 99.8,
            "weighted_coverage_percent": infra_coverage,
            "total_duration_seconds": 120.5,
        },
        "infrastructure": {
            "exit_code": 0,
            "passed": 4500,
            "failed": 2,
            "skipped": 3,
            "warnings": warnings,
            "coverage_percent": infra_coverage,
            "meets_threshold": infra_coverage >= 60.0,
            "covered_lines": 16000,
            "total_lines": 19500,
            "duration_seconds": 90.0,
        },
        "projects": projects or {},
        "metadata": {
            "infrastructure_tests_included": True,
            "integration_tests_included": False,
            "slow_tests_included": False,
            "ollama_tests_included": False,
            "ollama_server_available": False,
        },
        "files_generated": ["test_results_summary.json", "test_results_summary.md"],
    }
    return data


class TestGenerateMarkdownReport:
    def test_basic_report(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "# Full Repository Test Suite Results" in md
        assert "2025-01-15T12:00:00" in md
        assert "PASSED" in md
        assert "5,000" in md or "5000" in md

    def test_failed_report(self):
        data = _make_report_data(overall_success=False)
        md = generate_markdown_report(data)
        assert "FAILED" in md

    def test_with_warnings(self):
        data = _make_report_data(warnings=5)
        md = generate_markdown_report(data)
        assert "Warnings" in md

    def test_with_projects(self):
        projects = {
            "code_project": {
                "exit_code": 0,
                "passed": 400,
                "failed": 0,
                "skipped": 2,
                "warnings": 0,
                "coverage_percent": 95.0,
                "meets_threshold": True,
                "covered_lines": 950,
                "total_lines": 1000,
                "duration_seconds": 15.0,
            },
            "template": {
                "exit_code": 1,
                "passed": 80,
                "failed": 3,
                "skipped": 1,
                "warnings": 1,
                "coverage_percent": 88.0,
                "meets_threshold": False,
                "covered_lines": 440,
                "total_lines": 500,
                "duration_seconds": 8.0,
            },
        }
        data = _make_report_data(projects=projects)
        md = generate_markdown_report(data)
        assert "Code Project" in md
        assert "Template" in md
        assert "95.0%" in md

    def test_metadata_active_projects(self):
        data = _make_report_data()
        data["metadata"]["active_projects"] = ["code_project", "template"]
        md = generate_markdown_report(data)
        assert "code_project" in md
        assert "template" in md

    def test_files_generated_listed(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "test_results_summary.json" in md

    def test_below_threshold(self):
        data = _make_report_data(infra_coverage=55.0)
        md = generate_markdown_report(data)
        assert "below" in md


class TestFormatConsoleSummary:
    def test_basic_console(self):
        data = _make_report_data()
        output = _format_console_summary(data)
        assert "FULL REPOSITORY TEST SUITE SUMMARY" in output
        assert "PASSED" in output
        assert "Infrastructure" in output

    def test_failed_console(self):
        data = _make_report_data(overall_success=False)
        output = _format_console_summary(data)
        assert "FAILED" in output

    def test_with_projects(self):
        projects = {
            "code_project": {
                "exit_code": 0,
                "passed": 400,
                "failed": 0,
                "skipped": 2,
                "warnings": 0,
                "coverage_percent": 95.0,
                "meets_threshold": True,
                "covered_lines": 950,
                "total_lines": 1000,
                "duration_seconds": 15.0,
            },
        }
        data = _make_report_data(projects=projects)
        output = _format_console_summary(data)
        assert "code_project" in output

    def test_long_project_name_truncated(self):
        projects = {
            "very_long_project_name_that_exceeds_limit": {
                "exit_code": 0,
                "passed": 100,
                "failed": 0,
                "skipped": 0,
                "warnings": 0,
                "coverage_percent": 90.0,
                "meets_threshold": True,
                "covered_lines": 900,
                "total_lines": 1000,
                "duration_seconds": 5.0,
            },
        }
        data = _make_report_data(projects=projects)
        output = _format_console_summary(data)
        assert "..." in output
