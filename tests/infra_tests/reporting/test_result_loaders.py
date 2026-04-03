"""Tests for infrastructure.reporting.result_loaders — comprehensive coverage."""

import json

from infrastructure.reporting.result_loaders import (
    load_test_results,
    load_infrastructure_results,
    _EMPTY_INFRA_RESULTS,
)


class TestLoadTestResults:
    def test_loads_project_results(self, tmp_path):
        reports = tmp_path / "projects" / "demo" / "output" / "reports"
        reports.mkdir(parents=True)
        data = {
            "project": {"total": 50, "passed": 48, "failed": 2, "coverage_percent": 92.0},
            "summary": {"all_passed": False},
        }
        (reports / "test_results.json").write_text(json.dumps(data))
        result = load_test_results("demo", repo_root=tmp_path)
        assert result["total"] == 50
        assert result["passed"] == 48

    def test_returns_empty_when_missing(self, tmp_path):
        result = load_test_results("nonexistent", repo_root=tmp_path)
        assert result == {}

    def test_project_dir_override(self, tmp_path):
        proj = tmp_path / "custom" / "myproj"
        reports = proj / "output" / "reports"
        reports.mkdir(parents=True)
        data = {"project": {"total": 10, "passed": 10}}
        (reports / "test_results.json").write_text(json.dumps(data))
        result = load_test_results("myproj", repo_root=tmp_path, project_dir=proj)
        assert result["total"] == 10

    def test_returns_full_data_when_no_project_key(self, tmp_path):
        reports = tmp_path / "projects" / "flat" / "output" / "reports"
        reports.mkdir(parents=True)
        data = {"total": 30, "passed": 30}
        (reports / "test_results.json").write_text(json.dumps(data))
        result = load_test_results("flat", repo_root=tmp_path)
        assert result["total"] == 30

    def test_corrupt_json_raises(self, tmp_path):
        reports = tmp_path / "projects" / "bad" / "output" / "reports"
        reports.mkdir(parents=True)
        (reports / "test_results.json").write_text("{bad json!!!")
        try:
            load_test_results("bad", repo_root=tmp_path)
            assert False, "Should have raised json.JSONDecodeError"
        except json.JSONDecodeError:
            pass  # Expected


class TestLoadInfrastructureResults:
    def test_returns_empty_when_no_files(self, tmp_path):
        result = load_infrastructure_results(repo_root=tmp_path)
        assert result["passed"] == 0
        assert result["coverage_percent"] == 0.0

    def test_loads_from_validation_report(self, tmp_path):
        data = {
            "test_results": {
                "infrastructure": {
                    "total_tests": 100,
                    "passed": 95,
                    "skipped": 3,
                    "warnings": 2,
                    "coverage_percent": 82.5,
                    "duration_seconds": 15.0,
                    "status": "PASSED",
                }
            }
        }
        (tmp_path / "infrastructure_validation_report.json").write_text(json.dumps(data))
        result = load_infrastructure_results(repo_root=tmp_path)
        assert result["passed"] == 95
        assert result["failed"] == 2  # 100 - 95 - 3
        assert result["skipped"] == 3
        assert result["coverage_percent"] == 82.5
        assert result["exit_code"] == 0

    def test_failed_status_exit_code(self, tmp_path):
        data = {
            "test_results": {
                "infrastructure": {
                    "total_tests": 10,
                    "passed": 8,
                    "skipped": 0,
                    "status": "FAILED",
                }
            }
        }
        (tmp_path / "infrastructure_validation_report.json").write_text(json.dumps(data))
        result = load_infrastructure_results(repo_root=tmp_path)
        assert result["exit_code"] == 1

    def test_falls_back_to_coverage_infra_json(self, tmp_path):
        data = {
            "totals": {
                "percent_covered": 78.5,
                "num_statements": 500,
                "covered_lines": 392,
                "missing_lines": 108,
            }
        }
        (tmp_path / "coverage_infra.json").write_text(json.dumps(data))
        result = load_infrastructure_results(repo_root=tmp_path)
        assert result["coverage_percent"] == 78.5
        assert result["total_lines"] == 500
        assert result["covered_lines"] == 392
        assert result["missing_lines"] == 108

    def test_falls_back_to_htmlcov(self, tmp_path):
        htmlcov = tmp_path / "htmlcov"
        htmlcov.mkdir()
        data = {"totals": {"percent_covered": 65.0, "num_statements": 200}}
        (htmlcov / "coverage.json").write_text(json.dumps(data))
        result = load_infrastructure_results(repo_root=tmp_path)
        assert result["coverage_percent"] == 65.0

    def test_validation_report_takes_priority(self, tmp_path):
        # Both files exist; validation report should win
        val_data = {
            "test_results": {
                "infrastructure": {
                    "total_tests": 50,
                    "passed": 50,
                    "skipped": 0,
                    "coverage_percent": 90.0,
                    "status": "PASSED",
                }
            }
        }
        cov_data = {"totals": {"percent_covered": 60.0}}
        (tmp_path / "infrastructure_validation_report.json").write_text(json.dumps(val_data))
        (tmp_path / "coverage_infra.json").write_text(json.dumps(cov_data))
        result = load_infrastructure_results(repo_root=tmp_path)
        assert result["coverage_percent"] == 90.0

    def test_corrupt_validation_report_fallback(self, tmp_path):
        (tmp_path / "infrastructure_validation_report.json").write_text("{bad")
        data = {"totals": {"percent_covered": 55.0, "num_statements": 100}}
        (tmp_path / "coverage_infra.json").write_text(json.dumps(data))
        result = load_infrastructure_results(repo_root=tmp_path)
        assert result["coverage_percent"] == 55.0

    def test_empty_infra_results_is_correct_shape(self):
        assert "passed" in _EMPTY_INFRA_RESULTS
        assert "failed" in _EMPTY_INFRA_RESULTS
        assert "coverage_percent" in _EMPTY_INFRA_RESULTS
        assert "exit_code" in _EMPTY_INFRA_RESULTS

    def test_empty_infra_data_in_validation_report(self, tmp_path):
        data = {"test_results": {"infrastructure": {}}}
        (tmp_path / "infrastructure_validation_report.json").write_text(json.dumps(data))
        # Empty infra_data is falsy, so fallback path
        result = load_infrastructure_results(repo_root=tmp_path)
        # Should fall through to coverage files (none exist) -> empty
        assert result["passed"] == 0
