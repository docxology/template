"""Tests for infrastructure.reporting.pipeline_io — expanded coverage for save_pipeline_report."""

import json

from infrastructure.reporting.pipeline_io import (
    save_pipeline_report,
)
from infrastructure.reporting.pipeline_report_model import (
    PipelineReport,
    generate_pipeline_report,
)
from infrastructure.core.runtime.checkpoint import StageResult


def _make_report(**overrides):
    defaults = {
        "timestamp": "2026-04-01T12:00:00",
        "total_duration": 30.0,
        "stages": [
            StageResult(name="setup", exit_code=0, duration=2.0, status="passed"),
            StageResult(name="build", exit_code=0, duration=10.0, status="passed"),
            StageResult(name="test", exit_code=1, duration=18.0, status="failed"),
        ],
        "test_results": {"total": 100, "passed": 95, "failed": 5},
        "validation_results": {"checks": {"pdf": True}},
        "performance_metrics": {"cpu_time": 25.0},
        "error_summary": {"total_errors": 1},
        "output_statistics": {"files": 3},
    }
    defaults.update(overrides)
    return PipelineReport(**defaults)


class TestSavePipelineReport:
    def test_saves_all_formats(self, tmp_path):
        report = _make_report()
        result = save_pipeline_report(report, tmp_path)
        assert "json" in result
        assert "html" in result
        assert "markdown" in result
        assert result["json"].exists()
        assert result["html"].exists()
        assert result["markdown"].exists()

    def test_json_format_only(self, tmp_path):
        report = _make_report()
        result = save_pipeline_report(report, tmp_path, formats=["json"])
        assert "json" in result
        assert "html" not in result
        assert "markdown" not in result

    def test_html_format_only(self, tmp_path):
        report = _make_report()
        result = save_pipeline_report(report, tmp_path, formats=["html"])
        assert "html" in result
        assert "json" not in result

    def test_markdown_format_only(self, tmp_path):
        report = _make_report()
        result = save_pipeline_report(report, tmp_path, formats=["markdown"])
        assert "markdown" in result
        assert "json" not in result

    def test_json_content_valid(self, tmp_path):
        report = _make_report()
        result = save_pipeline_report(report, tmp_path, formats=["json"])
        data = json.loads(result["json"].read_text())
        assert data["total_duration"] == 30.0
        assert len(data["stages"]) == 3
        assert data["test_results"]["total"] == 100

    def test_creates_output_directory(self, tmp_path):
        report = _make_report()
        out_dir = tmp_path / "nested" / "reports"
        result = save_pipeline_report(report, out_dir, formats=["json"])
        assert result["json"].exists()

    def test_minimal_report(self, tmp_path):
        report = PipelineReport(
            timestamp="2026-01-01T00:00:00",
            total_duration=0.0,
            stages=[],
        )
        result = save_pipeline_report(report, tmp_path, formats=["json"])
        data = json.loads(result["json"].read_text())
        assert data["stages"] == []
        assert data["test_results"] is None

    def test_html_contains_structure(self, tmp_path):
        report = _make_report()
        result = save_pipeline_report(report, tmp_path, formats=["html"])
        html = result["html"].read_text()
        assert "<html" in html or "<div" in html or "Pipeline" in html

    def test_markdown_contains_report_header(self, tmp_path):
        report = _make_report()
        result = save_pipeline_report(report, tmp_path, formats=["markdown"])
        md = result["markdown"].read_text()
        assert "Pipeline" in md or "#" in md


class TestGeneratePipelineReport:
    def test_basic(self, tmp_path):
        stage_results = [
            {"name": "setup", "exit_code": 0, "duration": 1.0},
            {"name": "build", "exit_code": 1, "duration": 5.0},
        ]
        report = generate_pipeline_report(stage_results, 6.0, tmp_path)
        assert report.total_duration == 6.0
        assert len(report.stages) == 2
        assert report.stages[0].status == "passed"
        assert report.stages[1].status == "failed"

    def test_with_project_name_and_log(self, tmp_path):
        log_dir = tmp_path / "projects" / "myproj" / "output" / "logs"
        log_dir.mkdir(parents=True)
        (log_dir / "pipeline.log").write_text("log content")
        report = generate_pipeline_report(
            [{"name": "s1", "exit_code": 0, "duration": 1.0}],
            1.0,
            tmp_path,
            project_name="myproj",
            output_statistics={"files": 1},
        )
        assert report.output_statistics is not None
        assert report.output_statistics["log_file"]["exists"] is True
        assert report.output_statistics["log_file"]["size"] > 0

    def test_with_project_dir_override(self, tmp_path):
        custom_dir = tmp_path / "custom_loc" / "myproj"
        log_dir = custom_dir / "output" / "logs"
        log_dir.mkdir(parents=True)
        (log_dir / "pipeline.log").write_text("log")
        report = generate_pipeline_report(
            [{"name": "s1", "exit_code": 0, "duration": 1.0}],
            1.0,
            tmp_path,
            project_name="myproj",
            project_dir=custom_dir,
            output_statistics={"files": 1},
        )
        assert report.output_statistics["log_file"]["exists"] is True

    def test_missing_name_defaults(self, tmp_path):
        report = generate_pipeline_report([{"exit_code": 0, "duration": 1.0}], 1.0, tmp_path)
        assert report.stages[0].name == "unknown"

    def test_no_output_statistics(self, tmp_path):
        report = generate_pipeline_report(
            [{"name": "s1", "exit_code": 0, "duration": 1.0}],
            1.0,
            tmp_path,
            project_name="proj",
            output_statistics=None,
        )
        assert report.output_statistics is None
