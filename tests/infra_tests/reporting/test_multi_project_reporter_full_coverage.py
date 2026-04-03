"""Tests for infrastructure/reporting/multi_project_reporter.py.

Covers: _build_summary_dict, generate_multi_project_summary_report,
_format_multi_project_summary_markdown.

No mocks used — all tests use real data structures and real file I/O.
"""

from __future__ import annotations

import json
from dataclasses import dataclass


from infrastructure.reporting.multi_project_reporter import (
    _build_summary_dict,
    generate_multi_project_summary_report,
    _format_multi_project_summary_markdown,
)


@dataclass
class FakeStageResult:
    """Minimal stage result for testing."""
    success: bool
    duration: float
    error_message: str = ""


@dataclass
class FakeMultiProjectResult:
    """Minimal MultiProjectResult for testing."""
    successful_projects: int
    failed_projects: int
    total_duration: float
    infra_test_duration: float
    project_results: dict


@dataclass
class FakeProject:
    """Minimal project object for testing."""
    name: str


class TestBuildSummaryDict:
    """Test _build_summary_dict pure logic function."""

    def test_basic_summary(self):
        """Should build summary with one successful project."""
        projects = [FakeProject(name="proj_a")]
        stages = [FakeStageResult(success=True, duration=5.0)]
        result = FakeMultiProjectResult(
            successful_projects=1,
            failed_projects=0,
            total_duration=5.0,
            infra_test_duration=1.0,
            project_results={"proj_a": stages},
        )
        summary = _build_summary_dict(result, projects)
        assert summary["total_projects"] == 1
        assert summary["successful_projects"] == 1
        assert summary["failed_projects"] == 0
        assert summary["projects"]["proj_a"]["success"] is True
        assert summary["projects"]["proj_a"]["duration"] == 5.0

    def test_failed_project(self):
        """Should build summary with failed project."""
        projects = [FakeProject(name="proj_a")]
        stages = [
            FakeStageResult(success=True, duration=2.0),
            FakeStageResult(success=False, duration=1.0, error_message="Build failed"),
        ]
        result = FakeMultiProjectResult(
            successful_projects=0,
            failed_projects=1,
            total_duration=3.0,
            infra_test_duration=0.0,
            project_results={"proj_a": stages},
        )
        summary = _build_summary_dict(result, projects)
        assert summary["failed_projects"] == 1
        assert summary["projects"]["proj_a"]["success"] is False
        assert "Build failed" in summary["projects"]["proj_a"]["errors"]
        assert len(summary["recommendations"]) > 0

    def test_multiple_projects(self):
        """Should handle multiple projects with different results."""
        projects = [FakeProject(name="proj_a"), FakeProject(name="proj_b")]
        result = FakeMultiProjectResult(
            successful_projects=1,
            failed_projects=1,
            total_duration=10.0,
            infra_test_duration=2.0,
            project_results={
                "proj_a": [FakeStageResult(success=True, duration=4.0)],
                "proj_b": [FakeStageResult(success=False, duration=6.0, error_message="Timeout")],
            },
        )
        summary = _build_summary_dict(result, projects)
        assert summary["total_projects"] == 2
        assert summary["projects"]["proj_a"]["success"] is True
        assert summary["projects"]["proj_b"]["success"] is False
        assert summary["performance_analysis"]["slowest_project"] == "proj_b"
        assert summary["performance_analysis"]["fastest_project"] == "proj_a"

    def test_empty_project_results(self):
        """Should handle empty project results dict."""
        projects = [FakeProject(name="proj_a")]
        result = FakeMultiProjectResult(
            successful_projects=0,
            failed_projects=0,
            total_duration=0.0,
            infra_test_duration=0.0,
            project_results={},
        )
        summary = _build_summary_dict(result, projects)
        assert summary["projects"]["proj_a"]["success"] is False
        assert summary["projects"]["proj_a"]["duration"] == 0

    def test_non_dict_project_results(self):
        """Should handle non-dict project_results gracefully."""
        projects = [FakeProject(name="proj_a")]
        result = FakeMultiProjectResult(
            successful_projects=0,
            failed_projects=0,
            total_duration=0.0,
            infra_test_duration=0.0,
            project_results="not a dict",  # type: ignore
        )
        summary = _build_summary_dict(result, projects)
        assert summary["total_projects"] == 1


class TestGenerateMultiProjectSummaryReport:
    """Test generate_multi_project_summary_report file I/O."""

    def test_generates_json_and_markdown(self, tmp_path):
        """Should generate JSON and markdown files."""
        projects = [FakeProject(name="proj_a")]
        result = FakeMultiProjectResult(
            successful_projects=1,
            failed_projects=0,
            total_duration=5.0,
            infra_test_duration=1.0,
            project_results={"proj_a": [FakeStageResult(success=True, duration=5.0)]},
        )
        output_dir = tmp_path / "reports"
        files = generate_multi_project_summary_report(result, projects, output_dir)
        assert "json" in files
        assert "markdown" in files
        assert files["json"].exists()
        assert files["markdown"].exists()

        # Validate JSON content
        data = json.loads(files["json"].read_text())
        assert data["total_projects"] == 1

    def test_creates_output_dir(self, tmp_path):
        """Should create output directory if it doesn't exist."""
        projects = [FakeProject(name="proj_a")]
        result = FakeMultiProjectResult(
            successful_projects=1,
            failed_projects=0,
            total_duration=1.0,
            infra_test_duration=0.0,
            project_results={"proj_a": [FakeStageResult(success=True, duration=1.0)]},
        )
        output_dir = tmp_path / "nested" / "deep" / "reports"
        files = generate_multi_project_summary_report(result, projects, output_dir)
        assert output_dir.exists()
        assert files["json"].exists()


class TestFormatMultiProjectSummaryMarkdown:
    """Test _format_multi_project_summary_markdown pure formatting."""

    def test_basic_format(self):
        """Should format a basic summary."""
        summary = {
            "timestamp": "2026-01-01T00:00:00",
            "total_projects": 1,
            "successful_projects": 1,
            "failed_projects": 0,
            "total_duration": 5.0,
            "infra_test_duration": 1.0,
            "projects": {
                "proj_a": {
                    "success": True,
                    "duration": 5.0,
                    "stages_completed": 3,
                    "errors": [],
                },
            },
            "performance_analysis": {
                "slowest_project": "proj_a",
                "fastest_project": "proj_a",
                "average_duration": 5.0,
                "total_pipeline_time": 5.0,
            },
            "error_aggregation": {
                "total_errors": 0,
                "errors_by_project": {"proj_a": 0},
            },
            "recommendations": [],
        }
        md = _format_multi_project_summary_markdown(summary)
        assert "# Multi-Project Execution Summary" in md
        assert "proj_a" in md
        assert "5.0s" in md

    def test_format_with_errors(self):
        """Should include error details in markdown."""
        summary = {
            "timestamp": "2026-01-01T00:00:00",
            "total_projects": 1,
            "successful_projects": 0,
            "failed_projects": 1,
            "total_duration": 3.0,
            "infra_test_duration": 0.0,
            "projects": {
                "proj_a": {
                    "success": False,
                    "duration": 3.0,
                    "stages_completed": 2,
                    "errors": ["Build failed", "Test failed", "Deploy failed", "Extra error"],
                },
            },
            "performance_analysis": {},
            "error_aggregation": {
                "total_errors": 4,
                "errors_by_project": {"proj_a": 4},
            },
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Fix builds",
                    "details": "Multiple failures detected",
                },
            ],
        }
        md = _format_multi_project_summary_markdown(summary)
        assert "Build failed" in md
        assert "Recommendations" in md
        assert "HIGH" in md

    def test_format_no_infra_duration(self):
        """Should skip infra duration line when duration is 0."""
        summary = {
            "timestamp": "2026-01-01T00:00:00",
            "total_projects": 1,
            "successful_projects": 1,
            "failed_projects": 0,
            "total_duration": 1.0,
            "infra_test_duration": 0.0,
            "projects": {
                "proj_a": {
                    "success": True,
                    "duration": 1.0,
                    "stages_completed": 1,
                    "errors": [],
                },
            },
            "performance_analysis": {},
            "error_aggregation": {"total_errors": 0, "errors_by_project": {}},
            "recommendations": [],
        }
        md = _format_multi_project_summary_markdown(summary)
        assert "Infrastructure Tests" not in md
