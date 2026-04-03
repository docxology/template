"""Tests for infrastructure.reporting.markdown_formatter."""

from infrastructure.reporting.markdown_formatter import (
    _format_console_summary,
    generate_markdown_report,
)


def _make_report_data():
    return {
        "timestamp": "2026-01-15T10:30:00",
        "test_type": "comprehensive",
        "overall_success": True,
        "summary": {
            "total_tests": 500,
            "total_passed": 490,
            "total_failed": 5,
            "total_skipped": 5,
            "pass_rate": 98.0,
            "weighted_coverage_percent": 85.0,
            "total_duration_seconds": 120.0,
        },
        "infrastructure": {
            "exit_code": 0,
            "passed": 300,
            "failed": 2,
            "skipped": 3,
            "warnings": 5,
            "coverage_percent": 75.0,
            "meets_threshold": True,
            "covered_lines": 3000,
            "total_lines": 4000,
            "duration_seconds": 60.0,
        },
        "projects": {
            "code_project": {
                "exit_code": 0,
                "passed": 190,
                "failed": 3,
                "skipped": 2,
                "warnings": 0,
                "coverage_percent": 92.0,
                "meets_threshold": True,
                "covered_lines": 500,
                "total_lines": 543,
                "duration_seconds": 30.0,
            },
        },
        "metadata": {
            "infrastructure_tests_included": True,
            "integration_tests_included": False,
            "slow_tests_included": True,
            "ollama_tests_included": False,
            "ollama_server_available": False,
            "active_projects": ["code_project"],
        },
        "files_generated": ["test_results_summary.json", "test_results_summary.md"],
    }


class TestGenerateMarkdownReport:
    def test_basic_structure(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "# Full Repository Test Suite Results" in md
        assert "## Summary" in md
        assert "## Infrastructure Tests" in md
        assert "## Code Project Tests" in md
        assert "## Test Configuration" in md
        assert "## Generated Files" in md

    def test_contains_stats(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "500" in md
        assert "98.0%" in md
        assert "85.0%" in md

    def test_overall_status_passed(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "PASSED" in md

    def test_overall_status_failed(self):
        data = _make_report_data()
        data["overall_success"] = False
        md = generate_markdown_report(data)
        assert "FAILED" in md

    def test_infra_warnings_included(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "**Warnings**: 5" in md

    def test_infra_no_warnings(self):
        data = _make_report_data()
        data["infrastructure"]["warnings"] = 0
        md = generate_markdown_report(data)
        # "Warnings" should NOT appear for infra section when 0
        lines = md.split("\n")
        infra_section = False
        for line in lines:
            if "## Infrastructure Tests" in line:
                infra_section = True
            if infra_section and "## " in line and "Infrastructure" not in line:
                break
            if infra_section and "**Warnings**" in line:
                raise AssertionError("Warnings line should not appear when count is 0")

    def test_project_warnings_included(self):
        data = _make_report_data()
        data["projects"]["code_project"]["warnings"] = 3
        md = generate_markdown_report(data)
        assert "**Warnings**: 3" in md

    def test_no_projects(self):
        data = _make_report_data()
        data["projects"] = {}
        md = generate_markdown_report(data)
        assert "## Summary" in md

    def test_metadata_includes_active_projects(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "code_project" in md

    def test_generated_files_listed(self):
        data = _make_report_data()
        md = generate_markdown_report(data)
        assert "`test_results_summary.json`" in md


class TestFormatConsoleSummary:
    def test_basic_structure(self):
        data = _make_report_data()
        output = _format_console_summary(data)
        assert "FULL REPOSITORY TEST SUITE SUMMARY" in output
        assert "PASSED" in output
        assert "Infrastructure" in output

    def test_long_project_name_truncated(self):
        data = _make_report_data()
        data["projects"]["this_is_a_very_long_project_name_xyz"] = data["projects"].pop("code_project")
        output = _format_console_summary(data)
        assert "..." in output

    def test_short_project_name(self):
        data = _make_report_data()
        output = _format_console_summary(data)
        assert "code_project" in output
