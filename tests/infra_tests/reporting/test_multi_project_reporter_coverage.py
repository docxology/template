"""Tests for infrastructure.reporting.multi_project_reporter — additional coverage."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from infrastructure.core.pipeline.multi_project import MultiProjectResult
from infrastructure.core.pipeline import PipelineStageResult
from infrastructure.reporting.multi_project_reporter import (
    _build_summary_dict,
    _format_multi_project_summary_markdown,
    generate_multi_project_summary_report,
)


@dataclass
class _FakeProject:
    name: str


def _make_stage(
    name: str, success: bool = True, duration: float = 1.0
) -> PipelineStageResult:
    return PipelineStageResult(
        stage_num=1,
        stage_name=name,
        success=success,
        exit_code=0 if success else 1,
        duration=duration,
        error_message="" if success else f"{name} failed",
    )


class TestBuildSummaryDict:
    def test_performance_analysis(self):
        projects = [_FakeProject("fast"), _FakeProject("slow")]
        result = MultiProjectResult(
            project_results={
                "fast": [_make_stage("test", True, 1.0)],
                "slow": [_make_stage("test", True, 10.0)],
            },
            successful_projects=2,
            failed_projects=0,
            total_duration=15.0,
            infra_test_duration=0.0,
        )
        summary = _build_summary_dict(result, projects)
        perf = summary["performance_analysis"]
        assert perf["slowest_project"] == "slow"
        assert perf["fastest_project"] == "fast"
        assert perf["average_duration"] == pytest.approx(5.5)
        assert perf["total_pipeline_time"] == pytest.approx(11.0)

    def test_error_aggregation(self):
        projects = [_FakeProject("a"), _FakeProject("b")]
        result = MultiProjectResult(
            project_results={
                "a": [_make_stage("test", False, 1.0), _make_stage("render", False, 0.5)],
                "b": [_make_stage("test", True, 1.0)],
            },
            successful_projects=1,
            failed_projects=1,
            total_duration=5.0,
            infra_test_duration=0.0,
        )
        summary = _build_summary_dict(result, projects)
        assert summary["error_aggregation"]["total_errors"] == 2
        assert summary["error_aggregation"]["errors_by_project"]["a"] == 2
        assert summary["error_aggregation"]["errors_by_project"]["b"] == 0

    def test_recommendations_on_failure(self):
        projects = [_FakeProject("x")]
        result = MultiProjectResult(
            project_results={"x": [_make_stage("test", False)]},
            successful_projects=0,
            failed_projects=1,
            total_duration=1.0,
            infra_test_duration=0.0,
        )
        summary = _build_summary_dict(result, projects)
        assert any(r["priority"] == "high" for r in summary["recommendations"])

    def test_recommendations_on_slow_pipeline(self):
        projects = [_FakeProject("a")]
        result = MultiProjectResult(
            project_results={"a": [_make_stage("test", True, 500.0)]},
            successful_projects=1,
            failed_projects=0,
            total_duration=500.0,
            infra_test_duration=0.0,
        )
        summary = _build_summary_dict(result, projects)
        assert any(r["priority"] == "medium" for r in summary["recommendations"])

    def test_project_not_in_results(self):
        """Project listed but not in project_results dict."""
        projects = [_FakeProject("missing")]
        result = MultiProjectResult(
            project_results={},
            successful_projects=0,
            failed_projects=0,
            total_duration=0.0,
            infra_test_duration=0.0,
        )
        summary = _build_summary_dict(result, projects)
        proj = summary["projects"]["missing"]
        # Empty stage list: len([]) > 0 is False, so success is False
        assert proj["success"] is False
        assert proj["duration"] == 0

    def test_non_dict_project_results(self):
        """project_results is not a dict (edge case)."""
        projects = [_FakeProject("a")]
        result = MultiProjectResult(
            project_results="invalid",  # type: ignore[arg-type]
            successful_projects=0,
            failed_projects=0,
            total_duration=0.0,
            infra_test_duration=0.0,
        )
        summary = _build_summary_dict(result, projects)
        # Falls back to empty dict, project not in it, empty list -> success False
        assert summary["projects"]["a"]["success"] is False


class TestFormatMarkdown:
    def _make_summary(self, **overrides):
        base = {
            "timestamp": "2026-04-01T00:00:00",
            "total_projects": 2,
            "successful_projects": 2,
            "failed_projects": 0,
            "total_duration": 10.0,
            "infra_test_duration": 1.0,
            "projects": {
                "alpha": {
                    "success": True,
                    "duration": 5.0,
                    "stages_completed": 3,
                    "errors": [],
                },
                "beta": {
                    "success": False,
                    "duration": 4.0,
                    "stages_completed": 2,
                    "errors": ["test failed", "render failed", "validate failed", "extra error"],
                },
            },
            "performance_analysis": {
                "slowest_project": "alpha",
                "fastest_project": "beta",
                "average_duration": 4.5,
                "total_pipeline_time": 9.0,
            },
            "error_aggregation": {
                "total_errors": 4,
                "errors_by_project": {"alpha": 0, "beta": 4},
            },
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Fix failures",
                    "details": "Beta project failed",
                }
            ],
        }
        base.update(overrides)
        return base

    def test_full_markdown_output(self):
        summary = self._make_summary()
        md = _format_multi_project_summary_markdown(summary)
        assert "# Multi-Project Execution Summary" in md
        assert "**Generated:**" in md
        assert "## Overview" in md
        assert "## Project Results" in md
        assert "## Performance Analysis" in md
        assert "## Error Summary" in md
        assert "## Recommendations" in md

    def test_infra_test_duration_shown(self):
        summary = self._make_summary(infra_test_duration=2.5)
        md = _format_multi_project_summary_markdown(summary)
        assert "Infrastructure Tests" in md
        assert "2.5s" in md

    def test_infra_test_duration_zero_hidden(self):
        summary = self._make_summary(infra_test_duration=0)
        md = _format_multi_project_summary_markdown(summary)
        assert "Infrastructure Tests" not in md

    def test_errors_truncated(self):
        summary = self._make_summary()
        md = _format_multi_project_summary_markdown(summary)
        # beta has 4 errors, only first 3 shown + "and 1 more"
        assert "... and 1 more" in md

    def test_no_performance_analysis(self):
        summary = self._make_summary(performance_analysis={})
        md = _format_multi_project_summary_markdown(summary)
        assert "## Performance Analysis" not in md

    def test_no_error_aggregation(self):
        summary = self._make_summary(error_aggregation={})
        md = _format_multi_project_summary_markdown(summary)
        assert "## Error Summary" not in md

    def test_no_recommendations(self):
        summary = self._make_summary(recommendations=[])
        md = _format_multi_project_summary_markdown(summary)
        assert "## Recommendations" not in md

    def test_errors_by_project_zero_hidden(self):
        summary = self._make_summary(
            error_aggregation={
                "total_errors": 1,
                "errors_by_project": {"alpha": 0, "beta": 1},
            }
        )
        md = _format_multi_project_summary_markdown(summary)
        # alpha with 0 errors should NOT appear in errors-by-project list
        lines = md.split("\n")
        error_lines = [l for l in lines if l.startswith("- alpha:")]
        assert len(error_lines) == 0


class TestGenerateReport:
    def test_creates_output_dir(self, tmp_path):
        out = tmp_path / "new_dir"
        projects = [_FakeProject("p")]
        result = MultiProjectResult(
            project_results={"p": [_make_stage("t")]},
            successful_projects=1,
            failed_projects=0,
            total_duration=1.0,
            infra_test_duration=0.0,
        )
        files = generate_multi_project_summary_report(result, projects, out)
        assert out.exists()
        assert files["json"].exists()
        assert files["markdown"].exists()
