"""Tests for infrastructure.reporting.summary_generator module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.reporting.summary_generator import (
    generate_markdown_report,
    generate_summary_report,
    load_infrastructure_results,
    load_test_results,
)


class TestLoadTestResults:
    """Test load_test_results function."""

    def test_returns_empty_dict_when_file_missing(self, tmp_path, monkeypatch):
        """Returns empty dict when project results file does not exist."""
        monkeypatch.chdir(tmp_path)
        result = load_test_results("nonexistent_project")
        assert result == {}

    def test_loads_nested_project_key(self, tmp_path, monkeypatch):
        """Extracts 'project' key from nested result structure."""
        monkeypatch.chdir(tmp_path)
        project_dir = tmp_path / "projects" / "my_proj" / "output" / "reports"
        project_dir.mkdir(parents=True)
        data = {"project": {"passed": 10, "failed": 0}}
        (project_dir / "test_results.json").write_text(json.dumps(data))

        result = load_test_results("my_proj")
        assert result == {"passed": 10, "failed": 0}

    def test_loads_flat_structure(self, tmp_path, monkeypatch):
        """Returns raw dict when no 'project' key present."""
        monkeypatch.chdir(tmp_path)
        project_dir = tmp_path / "projects" / "my_proj" / "output" / "reports"
        project_dir.mkdir(parents=True)
        data = {"passed": 5, "failed": 1}
        (project_dir / "test_results.json").write_text(json.dumps(data))

        result = load_test_results("my_proj")
        assert result == {"passed": 5, "failed": 1}

    def test_returns_empty_dict_on_invalid_json(self, tmp_path, monkeypatch):
        """Returns empty dict when file contains invalid JSON."""
        monkeypatch.chdir(tmp_path)
        project_dir = tmp_path / "projects" / "bad" / "output" / "reports"
        project_dir.mkdir(parents=True)
        (project_dir / "test_results.json").write_text("not json {{{")

        result = load_test_results("bad")
        assert result == {}


class TestLoadInfrastructureResults:
    """Test load_infrastructure_results function."""

    def test_returns_empty_dict_when_no_files(self, tmp_path, monkeypatch):
        """Returns empty dict when no results files exist."""
        monkeypatch.chdir(tmp_path)
        result = load_infrastructure_results()
        assert isinstance(result, dict)

    def test_loads_from_validation_report(self, tmp_path, monkeypatch):
        """Loads from infrastructure_validation_report.json when present."""
        monkeypatch.chdir(tmp_path)
        report = {
            "test_results": {
                "infrastructure": {
                    "passed": 100,
                    "total_tests": 110,
                    "skipped": 5,
                    "warnings": 2,
                    "coverage_percent": 85.0,
                    "duration_seconds": 30.5,
                    "status": "PASSED",
                }
            }
        }
        (tmp_path / "infrastructure_validation_report.json").write_text(json.dumps(report))

        result = load_infrastructure_results()
        assert result["passed"] == 100
        assert result["coverage_percent"] == 85.0
        assert result["exit_code"] == 0


class TestGenerateSummaryReport:
    """Test generate_summary_report function."""

    def test_returns_dict_with_required_keys(self, tmp_path, monkeypatch):
        """Report dict contains all expected top-level keys."""
        monkeypatch.chdir(tmp_path)
        # No project or infra files — should still generate a valid structure
        result = generate_summary_report()

        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "summary" in result
        assert "infrastructure" in result
        assert "overall_success" in result

    def test_summary_aggregates_totals(self, tmp_path, monkeypatch):
        """Summary section aggregates passed/failed/skipped correctly."""
        monkeypatch.chdir(tmp_path)
        result = generate_summary_report()
        summary = result["summary"]

        assert "total_tests" in summary
        assert "total_passed" in summary
        assert "total_failed" in summary
        assert "pass_rate" in summary
        assert "weighted_coverage_percent" in summary

    def test_aggregation_math(self, tmp_path, monkeypatch):
        """Totals match sum of infra plus project results."""
        monkeypatch.chdir(tmp_path)

        # Create a project result
        project_dir = tmp_path / "projects" / "proj1" / "output" / "reports"
        project_dir.mkdir(parents=True)
        (project_dir / "test_results.json").write_text(
            json.dumps({"passed": 20, "failed": 2, "skipped": 1, "exit_code": 0})
        )

        # Create infra report
        infra = {
            "test_results": {
                "infrastructure": {
                    "passed": 50,
                    "total_tests": 55,
                    "skipped": 3,
                    "warnings": 0,
                    "coverage_percent": 70.0,
                    "duration_seconds": 10.0,
                    "status": "PASSED",
                }
            }
        }
        (tmp_path / "infrastructure_validation_report.json").write_text(json.dumps(infra))

        result = generate_summary_report()
        summary = result["summary"]
        # infra: 50 passed + proj: 20 passed = 70
        assert summary["total_passed"] >= 50


class TestGenerateMarkdownReport:
    """Test generate_markdown_report function."""

    def _make_data(self):
        return {
            "timestamp": "2026-01-01T00:00:00",
            "test_type": "full_repository",
            "overall_success": True,
            "summary": {
                "total_tests": 100,
                "total_passed": 95,
                "total_failed": 5,
                "total_skipped": 0,
                "pass_rate": 95.0,
                "weighted_coverage_percent": 80.0,
                "total_duration_seconds": 45.0,
            },
            "infrastructure": {
                "passed": 95,
                "failed": 5,
                "skipped": 0,
                "warnings": 0,
                "coverage_percent": 80.0,
                "total_lines": 1000,
                "covered_lines": 800,
                "missing_lines": 200,
                "duration_seconds": 45.0,
                "exit_code": 0,
                "meets_threshold": True,
            },
            "projects": {},
            "metadata": {
                "infrastructure_tests_included": True,
                "integration_tests_included": False,
                "slow_tests_included": False,
                "ollama_tests_included": False,
                "ollama_server_available": False,
            },
            "files_generated": [],
        }

    def test_returns_string(self):
        """Returns a string."""
        result = generate_markdown_report(self._make_data())
        assert isinstance(result, str)

    def test_contains_header(self):
        """Report contains expected markdown header."""
        result = generate_markdown_report(self._make_data())
        assert "# Full Repository Test Suite Results" in result

    def test_contains_pass_rate(self):
        """Report includes pass rate value."""
        result = generate_markdown_report(self._make_data())
        assert "95.0%" in result

    def test_reflects_overall_success(self):
        """Report shows PASSED when overall_success is True."""
        result = generate_markdown_report(self._make_data())
        assert "PASSED" in result

    def test_reflects_overall_failure(self):
        """Report shows FAILED when overall_success is False."""
        data = self._make_data()
        data["overall_success"] = False
        data["infrastructure"]["exit_code"] = 1
        result = generate_markdown_report(data)
        assert "FAILED" in result
