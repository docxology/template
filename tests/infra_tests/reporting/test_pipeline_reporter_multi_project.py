"""generate_multi_project_summary_report and its markdown formatter tests (formerly part of test_pipeline_reporter.py)."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.reporting.multi_project_reporter import generate_multi_project_summary_report

from ._pipeline_reporter_helpers import _MockProject, _MockResult, _MockStageResult


class TestGenerateMultiProjectSummaryReport:
    """Test generate_multi_project_summary_report function."""

    def test_generate_with_successful_projects(self, tmp_path: Path) -> None:
        """Test generating summary report with successful projects."""
        projects = [_MockProject("project1"), _MockProject("project2")]
        result = _MockResult(
            successful_projects=2,
            failed_projects=0,
            total_duration=10.0,
            infra_test_duration=2.0,
            project_results={
                "project1": [_MockStageResult(True, 3.0), _MockStageResult(True, 2.0)],
                "project2": [_MockStageResult(True, 2.5), _MockStageResult(True, 2.5)],
            },
        )
        output_dir = tmp_path / "output"

        saved = generate_multi_project_summary_report(result, projects, output_dir)

        assert "json" in saved
        assert "markdown" in saved
        assert saved["json"].exists()
        assert saved["markdown"].exists()

        data = json.loads(saved["json"].read_text())
        assert data["total_projects"] == 2
        assert data["successful_projects"] == 2
        assert "project1" in data["projects"]

    def test_generate_with_failed_projects(self, tmp_path: Path) -> None:
        """Test generating summary report with failed projects."""
        projects = [_MockProject("project1"), _MockProject("project2")]
        result = _MockResult(
            successful_projects=1,
            failed_projects=1,
            total_duration=8.0,
            infra_test_duration=0.0,
            project_results={
                "project1": [_MockStageResult(True, 3.0)],
                "project2": [_MockStageResult(False, 2.0, "Test failed", ["Error 1"])],
            },
        )
        output_dir = tmp_path / "output"

        saved = generate_multi_project_summary_report(result, projects, output_dir)

        data = json.loads(saved["json"].read_text())
        assert data["failed_projects"] == 1
        assert len(data["recommendations"]) > 0

    def test_generate_with_empty_project_results(self, tmp_path: Path) -> None:
        """Test generating summary report with empty project results."""
        projects = [_MockProject("project1")]
        result = _MockResult(
            successful_projects=0,
            failed_projects=1,
            total_duration=0.0,
            infra_test_duration=0.0,
            project_results={"project1": []},
        )
        output_dir = tmp_path / "output"

        saved = generate_multi_project_summary_report(result, projects, output_dir)

        data = json.loads(saved["json"].read_text())
        assert "project1" in data["projects"]
        assert data["projects"]["project1"]["success"] is False

    def test_generate_with_dict_project_results(self, tmp_path: Path) -> None:
        """Test generating summary report with dict-style project results gets converted defensively.

        The code defensively converts dict values to empty lists, so dict-style results
        will be treated as empty (unknown format).
        """
        projects = [_MockProject("project1")]
        result = _MockResult(
            successful_projects=1,
            failed_projects=0,
            total_duration=5.0,
            infra_test_duration=0.0,
            project_results={"project1": {"success": True, "duration": 5.0, "stages_completed": 3, "errors": []}},
        )
        output_dir = tmp_path / "output"

        saved = generate_multi_project_summary_report(result, projects, output_dir)

        data = json.loads(saved["json"].read_text())
        # Dict values are defensively converted to empty lists, then treated as unknown format
        assert "project1" in data["projects"]
        # The project will show as failed because empty list triggers unknown format handling
        assert data["projects"]["project1"]["success"] is False

    def test_generate_with_performance_recommendation(self, tmp_path: Path) -> None:
        """Test summary report generates performance recommendation for slow projects."""
        projects = [_MockProject("project1")]
        result = _MockResult(
            successful_projects=1,
            failed_projects=0,
            total_duration=600.0,
            infra_test_duration=0.0,
            project_results={"project1": [_MockStageResult(True, 400.0)]},
        )
        output_dir = tmp_path / "output"

        saved = generate_multi_project_summary_report(result, projects, output_dir)

        data = json.loads(saved["json"].read_text())
        # Should have performance recommendation due to > 300s average
        recommendations = data.get("recommendations", [])
        has_perf_rec = any("performance" in r.get("action", "").lower() for r in recommendations)
        assert has_perf_rec

    def test_generate_with_non_dict_project_results(self, tmp_path: Path) -> None:
        """Test handling non-dict project_results attribute."""
        projects = [_MockProject("project1")]
        result = _MockResult(
            successful_projects=0,
            failed_projects=1,
            total_duration=0.0,
            infra_test_duration=0.0,
            project_results="invalid",  # Non-dict value
        )
        output_dir = tmp_path / "output"

        saved = generate_multi_project_summary_report(result, projects, output_dir)

        data = json.loads(saved["json"].read_text())
        # Should handle gracefully
        assert data["total_projects"] == 1


class TestFormatMultiProjectSummaryMarkdown:
    """Test _format_multi_project_summary_markdown function."""

    def test_format_basic_markdown(self) -> None:
        """Test basic markdown formatting."""
        from infrastructure.reporting.multi_project_reporter import (
            _format_multi_project_summary_markdown,
        )

        summary = {
            "timestamp": "2025-01-01T00:00:00",
            "total_projects": 2,
            "successful_projects": 1,
            "failed_projects": 1,
            "total_duration": 10.0,
            "infra_test_duration": 0,
            "projects": {
                "project1": {
                    "success": True,
                    "duration": 5.0,
                    "stages_completed": 3,
                    "errors": [],
                },
                "project2": {
                    "success": False,
                    "duration": 5.0,
                    "stages_completed": 2,
                    "errors": ["Test failed"],
                },
            },
            "performance_analysis": {},
            "error_aggregation": {
                "total_errors": 1,
                "errors_by_project": {"project1": 0, "project2": 1},
            },
            "recommendations": [],
        }

        md = _format_multi_project_summary_markdown(summary)

        assert "Multi-Project Execution Summary" in md
        assert "project1" in md
        assert "project2" in md
        assert "✅" in md  # Success icon
        assert "❌" in md  # Failure icon

    def test_format_with_infra_test_duration(self) -> None:
        """Test markdown includes infrastructure test duration."""
        from infrastructure.reporting.multi_project_reporter import (
            _format_multi_project_summary_markdown,
        )

        summary = {
            "timestamp": "2025-01-01T00:00:00",
            "total_projects": 1,
            "successful_projects": 1,
            "failed_projects": 0,
            "total_duration": 10.0,
            "infra_test_duration": 3.5,
            "projects": {
                "project1": {
                    "success": True,
                    "duration": 6.5,
                    "stages_completed": 3,
                    "errors": [],
                }
            },
            "performance_analysis": {},
            "error_aggregation": {"total_errors": 0, "errors_by_project": {}},
            "recommendations": [],
        }

        md = _format_multi_project_summary_markdown(summary)
        assert "Infrastructure Tests" in md
        assert "3.5s" in md

    def test_format_with_performance_analysis(self) -> None:
        """Test markdown includes performance analysis."""
        from infrastructure.reporting.multi_project_reporter import (
            _format_multi_project_summary_markdown,
        )

        summary = {
            "timestamp": "2025-01-01T00:00:00",
            "total_projects": 2,
            "successful_projects": 2,
            "failed_projects": 0,
            "total_duration": 15.0,
            "projects": {
                "project1": {
                    "success": True,
                    "duration": 5.0,
                    "stages_completed": 3,
                    "errors": [],
                },
                "project2": {
                    "success": True,
                    "duration": 10.0,
                    "stages_completed": 3,
                    "errors": [],
                },
            },
            "performance_analysis": {
                "slowest_project": "project2",
                "fastest_project": "project1",
                "average_duration": 7.5,
                "total_pipeline_time": 15.0,
            },
            "error_aggregation": {"total_errors": 0, "errors_by_project": {}},
            "recommendations": [],
        }

        md = _format_multi_project_summary_markdown(summary)
        assert "Performance Analysis" in md
        assert "Slowest Project" in md
        assert "project2" in md

    def test_format_with_recommendations(self) -> None:
        """Test markdown includes recommendations."""
        from infrastructure.reporting.multi_project_reporter import (
            _format_multi_project_summary_markdown,
        )

        summary = {
            "timestamp": "2025-01-01T00:00:00",
            "total_projects": 1,
            "successful_projects": 0,
            "failed_projects": 1,
            "total_duration": 5.0,
            "projects": {
                "project1": {
                    "success": False,
                    "duration": 5.0,
                    "stages_completed": 1,
                    "errors": ["Failed"],
                }
            },
            "performance_analysis": {},
            "error_aggregation": {
                "total_errors": 1,
                "errors_by_project": {"project1": 1},
            },
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Review failed projects",
                    "details": "1 project(s) failed",
                },
            ],
        }

        md = _format_multi_project_summary_markdown(summary)
        assert "Recommendations" in md
        assert "HIGH" in md
        assert "Review failed projects" in md

    def test_format_with_many_errors(self) -> None:
        """Test markdown truncates error list."""
        from infrastructure.reporting.multi_project_reporter import (
            _format_multi_project_summary_markdown,
        )

        summary = {
            "timestamp": "2025-01-01T00:00:00",
            "total_projects": 1,
            "successful_projects": 0,
            "failed_projects": 1,
            "total_duration": 5.0,
            "projects": {
                "project1": {
                    "success": False,
                    "duration": 5.0,
                    "stages_completed": 1,
                    "errors": [f"Error {i}" for i in range(5)],
                }
            },
            "performance_analysis": {},
            "error_aggregation": {
                "total_errors": 5,
                "errors_by_project": {"project1": 5},
            },
            "recommendations": [],
        }

        md = _format_multi_project_summary_markdown(summary)
        assert "... and 2 more" in md  # Should truncate to first 3 errors
