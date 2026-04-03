"""Tests for infrastructure.reporting.result_loaders — comprehensive coverage."""

import json

from infrastructure.reporting.result_loaders import (
    load_test_results,
    load_infrastructure_results,
    _EMPTY_INFRA_RESULTS,
)


class TestLoadTestResults:
    def test_load_from_project(self, tmp_path):
        proj = tmp_path / "projects" / "test_proj" / "output" / "reports"
        proj.mkdir(parents=True)
        results = {"project": {"passed": 10, "failed": 1, "skipped": 2}}
        (proj / "test_results.json").write_text(json.dumps(results))
        result = load_test_results("test_proj", repo_root=tmp_path)
        assert result["passed"] == 10

    def test_load_flat_results(self, tmp_path):
        proj = tmp_path / "projects" / "test_proj" / "output" / "reports"
        proj.mkdir(parents=True)
        results = {"passed": 5, "failed": 0}
        (proj / "test_results.json").write_text(json.dumps(results))
        result = load_test_results("test_proj", repo_root=tmp_path)
        assert result["passed"] == 5

    def test_missing_file(self, tmp_path):
        result = load_test_results("nonexistent", repo_root=tmp_path)
        assert result == {}

    def test_custom_project_dir(self, tmp_path):
        proj_dir = tmp_path / "custom" / "project"
        reports = proj_dir / "output" / "reports"
        reports.mkdir(parents=True)
        (reports / "test_results.json").write_text(json.dumps({"passed": 3}))
        result = load_test_results("ignored", project_dir=proj_dir)
        assert result["passed"] == 3


class TestLoadInfrastructureResults:
    def test_from_validation_report(self, tmp_path):
        report = {
            "test_results": {
                "infrastructure": {
                    "total_tests": 100,
                    "passed": 95,
                    "skipped": 3,
                    "warnings": 2,
                    "coverage_percent": 82.5,
                    "duration_seconds": 30.0,
                    "status": "PASSED",
                }
            }
        }
        (tmp_path / "infrastructure_validation_report.json").write_text(json.dumps(report))
        result = load_infrastructure_results(tmp_path)
        assert result["passed"] == 95
        assert result["failed"] == 2  # 100 - 95 - 3
        assert result["coverage_percent"] == 82.5
        assert result["exit_code"] == 0

    def test_from_coverage_json(self, tmp_path):
        cov = {
            "totals": {
                "percent_covered": 80.0,
                "num_statements": 1000,
                "covered_lines": 800,
                "missing_lines": 200,
            }
        }
        (tmp_path / "coverage_infra.json").write_text(json.dumps(cov))
        result = load_infrastructure_results(tmp_path)
        assert result["coverage_percent"] == 80.0
        assert result["total_lines"] == 1000

    def test_no_results_found(self, tmp_path):
        result = load_infrastructure_results(tmp_path)
        assert result["passed"] == 0
        assert result["coverage_percent"] == 0.0

    def test_corrupt_validation_report(self, tmp_path):
        (tmp_path / "infrastructure_validation_report.json").write_text("{bad json")
        result = load_infrastructure_results(tmp_path)
        # Should fall through to coverage JSON or empty
        assert result["passed"] == 0

    def test_empty_infra_results_shape(self):
        assert _EMPTY_INFRA_RESULTS["passed"] == 0
        assert _EMPTY_INFRA_RESULTS["exit_code"] == 0
        assert "coverage_percent" in _EMPTY_INFRA_RESULTS

    def test_failed_status(self, tmp_path):
        report = {
            "test_results": {
                "infrastructure": {
                    "total_tests": 10,
                    "passed": 8,
                    "skipped": 0,
                    "status": "FAILED",
                }
            }
        }
        (tmp_path / "infrastructure_validation_report.json").write_text(json.dumps(report))
        result = load_infrastructure_results(tmp_path)
        assert result["exit_code"] == 1
