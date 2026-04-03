"""Tests for infrastructure.reporting.report_generator — comprehensive coverage."""

import json

from infrastructure.reporting.report_generator import (
    generate_test_report,
    save_test_report_to_files,
)


class TestGenerateTestReport:
    def test_basic_report(self, tmp_path):
        infra = {"passed": 90, "failed": 5, "skipped": 5, "total": 100, "exit_code": 0}
        project = {"passed": 45, "failed": 3, "skipped": 2, "total": 50, "exit_code": 0}
        report = generate_test_report(infra, project, tmp_path, include_coverage_details=False)
        assert report["summary"]["total_passed"] == 135
        assert report["summary"]["total_failed"] == 8
        assert report["summary"]["total_tests"] == 150
        assert report["summary"]["all_passed"] is True

    def test_all_passed_false_when_failures(self, tmp_path):
        infra = {"passed": 10, "failed": 0, "total": 10, "exit_code": 0}
        project = {"passed": 5, "failed": 2, "total": 7, "exit_code": 1}
        report = generate_test_report(infra, project, tmp_path, include_coverage_details=False)
        assert report["summary"]["all_passed"] is False

    def test_includes_coverage_summary(self, tmp_path):
        infra = {"passed": 10, "total": 10, "exit_code": 0, "coverage_percent": 82.5}
        project = {"passed": 5, "total": 5, "exit_code": 0, "coverage_percent": 91.0}
        report = generate_test_report(infra, project, tmp_path, include_coverage_details=False)
        assert report["summary"]["infrastructure_coverage"] == 82.5
        assert report["summary"]["project_coverage"] == 91.0

    def test_includes_timestamp(self, tmp_path):
        report = generate_test_report({}, {}, tmp_path, include_coverage_details=False)
        assert "timestamp" in report
        assert "T" in report["timestamp"]

    def test_coverage_details_from_json_files(self, tmp_path):
        # Create mock coverage JSON files
        infra_cov = {
            "files": {
                "mod.py": {
                    "executed_lines": [1, 2, 3],
                    "missing_lines": [4],
                    "excluded_lines": [],
                }
            }
        }
        (tmp_path / "coverage_infra.json").write_text(json.dumps(infra_cov))
        report = generate_test_report({}, {}, tmp_path, include_coverage_details=True)
        assert "coverage_details" in report
        assert "infrastructure" in report["coverage_details"]

    def test_no_coverage_details_when_disabled(self, tmp_path):
        report = generate_test_report({}, {}, tmp_path, include_coverage_details=False)
        assert "coverage_details" not in report

    def test_missing_coverage_files_no_error(self, tmp_path):
        report = generate_test_report({}, {}, tmp_path, include_coverage_details=True)
        # Should not have coverage_details if files don't exist
        assert "coverage_details" not in report


class TestSaveTestReportToFiles:
    def test_creates_json_and_markdown(self, tmp_path):
        report = {
            "timestamp": "2026-01-01T00:00:00",
            "infrastructure": {"passed": 10, "failed": 0, "skipped": 0},
            "project": {"passed": 5, "failed": 0, "skipped": 0},
            "summary": {
                "total_passed": 15,
                "total_failed": 0,
                "total_tests": 15,
                "all_passed": True,
            },
        }
        json_path, md_path = save_test_report_to_files(report, tmp_path)
        assert json_path.exists()
        assert md_path.exists()
        assert json_path.name == "test_results.json"
        assert md_path.name == "test_results.md"

    def test_json_content(self, tmp_path):
        report = {
            "timestamp": "2026-01-01T00:00:00",
            "infrastructure": {"passed": 10},
            "project": {"passed": 5},
            "summary": {"total_passed": 15, "total_failed": 0, "total_tests": 15, "all_passed": True},
        }
        json_path, _ = save_test_report_to_files(report, tmp_path)
        data = json.loads(json_path.read_text())
        assert data["summary"]["total_passed"] == 15

    def test_markdown_content(self, tmp_path):
        report = {
            "timestamp": "2026-01-01T00:00:00",
            "infrastructure": {"passed": 10, "failed": 1, "skipped": 2, "coverage_percent": 80.0},
            "project": {"passed": 5, "failed": 0, "skipped": 0, "coverage_percent": 92.0},
            "summary": {"total_passed": 15, "total_failed": 1, "total_tests": 16, "all_passed": False},
        }
        _, md_path = save_test_report_to_files(report, tmp_path)
        md = md_path.read_text()
        assert "Test Results Summary" in md
        assert "Infrastructure Tests" in md
        assert "Project Tests" in md
        assert "80.00%" in md
        assert "92.00%" in md
        assert "FAILED" in md

    def test_creates_output_dir(self, tmp_path):
        nested = tmp_path / "deep" / "dir"
        report = {
            "timestamp": "2026-01-01",
            "infrastructure": {},
            "project": {},
            "summary": {"total_passed": 0, "total_failed": 0, "total_tests": 0, "all_passed": True},
        }
        save_test_report_to_files(report, nested)
        assert nested.exists()
