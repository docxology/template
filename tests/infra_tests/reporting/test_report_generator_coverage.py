"""Tests for infrastructure.reporting.report_generator — comprehensive coverage."""

import json

from infrastructure.reporting.report_generator import (
    generate_test_report,
    save_test_report_to_files,
)


class TestGenerateTestReport:
    def test_basic_report(self, tmp_path):
        infra = {"passed": 100, "failed": 2, "skipped": 3, "total": 105, "exit_code": 0}
        project = {"passed": 50, "failed": 0, "skipped": 1, "total": 51, "exit_code": 0}
        report = generate_test_report(infra, project, tmp_path, include_coverage_details=False)
        assert report["summary"]["total_passed"] == 150
        assert report["summary"]["total_failed"] == 2
        assert report["summary"]["total_tests"] == 156
        assert report["summary"]["all_passed"] is True

    def test_with_coverage(self, tmp_path):
        infra = {"passed": 10, "failed": 0, "total": 10, "exit_code": 0, "coverage_percent": 85.0}
        project = {"passed": 5, "failed": 0, "total": 5, "exit_code": 0, "coverage_percent": 92.0}
        report = generate_test_report(infra, project, tmp_path, include_coverage_details=False)
        assert report["summary"]["infrastructure_coverage"] == 85.0
        assert report["summary"]["project_coverage"] == 92.0

    def test_failed_exit_code(self, tmp_path):
        infra = {"passed": 10, "failed": 1, "total": 11, "exit_code": 1}
        project = {"passed": 5, "failed": 0, "total": 5, "exit_code": 0}
        report = generate_test_report(infra, project, tmp_path, include_coverage_details=False)
        assert report["summary"]["all_passed"] is False

    def test_with_coverage_details(self, tmp_path):
        # Create coverage JSON files
        infra_cov = tmp_path / "coverage_infra.json"
        infra_cov.write_text(json.dumps({
            "totals": {"percent_covered": 80.0},
            "files": {"mod.py": {"summary": {"percent_covered": 80.0}}}
        }))
        project_cov = tmp_path / "coverage_project.json"
        project_cov.write_text(json.dumps({
            "totals": {"percent_covered": 90.0},
            "files": {"src.py": {"summary": {"percent_covered": 90.0}}}
        }))
        infra = {"passed": 10, "failed": 0, "total": 10, "exit_code": 0}
        project = {"passed": 5, "failed": 0, "total": 5, "exit_code": 0}
        report = generate_test_report(infra, project, tmp_path, include_coverage_details=True)
        assert "coverage_details" in report

    def test_empty_results(self, tmp_path):
        report = generate_test_report({}, {}, tmp_path, include_coverage_details=False)
        assert report["summary"]["total_passed"] == 0
        assert report["summary"]["total_failed"] == 0


class TestSaveTestReportToFiles:
    def test_saves_json_and_md(self, tmp_path):
        report = {
            "timestamp": "2024-01-01T00:00:00",
            "infrastructure": {"passed": 10, "failed": 0, "skipped": 1, "coverage_percent": 85.0},
            "project": {"passed": 5, "failed": 1, "skipped": 0, "coverage_percent": 90.0},
            "summary": {
                "total_passed": 15,
                "total_failed": 1,
                "total_tests": 16,
                "all_passed": False,
            },
        }
        json_path, md_path = save_test_report_to_files(report, tmp_path / "out")
        assert json_path.exists()
        assert md_path.exists()

        # Verify JSON
        with open(json_path) as f:
            saved = json.load(f)
        assert saved["summary"]["total_passed"] == 15

        # Verify markdown
        md_text = md_path.read_text()
        assert "Test Results Summary" in md_text
        assert "85.00%" in md_text
        assert "90.00%" in md_text
        assert "FAILED" in md_text

    def test_creates_output_dir(self, tmp_path):
        report = {
            "timestamp": "2024-01-01",
            "infrastructure": {},
            "project": {},
            "summary": {"total_passed": 0, "total_failed": 0, "total_tests": 0, "all_passed": True},
        }
        out_dir = tmp_path / "deep" / "nested" / "dir"
        json_path, md_path = save_test_report_to_files(report, out_dir)
        assert json_path.exists()
        assert md_path.exists()

    def test_all_passed_status(self, tmp_path):
        report = {
            "timestamp": "2024-01-01",
            "infrastructure": {"passed": 10},
            "project": {"passed": 5},
            "summary": {"total_passed": 15, "total_failed": 0, "total_tests": 15, "all_passed": True},
        }
        _, md_path = save_test_report_to_files(report, tmp_path)
        md_text = md_path.read_text()
        assert "PASSED" in md_text
