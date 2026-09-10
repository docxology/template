"""Pipeline summary generation tests split from test_summary_reporting.py.

Exercises real code paths in:

* ``infrastructure.core.pipeline.summary`` — ``PipelineSummaryGenerator``,
  ``generate_pipeline_summary``.
"""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.pipeline.summary import (
    PipelineSummaryGenerator,
    generate_pipeline_summary,
)
from ._summary_reporting_helpers import _make_output_dir, _result


class TestPipelineSummaryGenerator:
    """Tests for ``PipelineSummaryGenerator.generate_summary``."""

    def test_generate_summary_with_successful_stages(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path, {"pdf/report.pdf": "PDF content"})
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("tests", stage_num=2, success=True, duration=3.0),
            _result("analysis", stage_num=4, success=True, duration=5.0),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=9.0,
            output_dir=output_dir,
        )
        assert summary.total_duration == 9.0
        assert summary.slowest_stage is not None
        assert summary.slowest_stage.stage_name == "analysis"
        assert summary.fastest_stage is not None
        # Stage 1 is excluded from fastest (setup)
        assert summary.fastest_stage.stage_name == "tests"
        assert summary.failed_stages == []
        assert len(summary.inventory) == 1

    def test_generate_summary_with_failed_stages(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("render", stage_num=7, success=False, duration=2.0, exit_code=1),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=3.0,
            output_dir=output_dir,
        )
        assert len(summary.failed_stages) == 1
        assert summary.failed_stages[0].stage_name == "render"
        # slowest_stage only considers successful stages — setup is the sole success
        assert summary.slowest_stage is not None
        assert summary.slowest_stage.stage_name == "setup"
        # fastest_stage excludes stage 1 (setup), so None when only setup succeeded
        assert summary.fastest_stage is None

    def test_generate_summary_with_log_file_and_skip_infra(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        log_file = tmp_path / "projects" / "demo" / "output" / "logs" / "pipeline.log"
        log_file.parent.mkdir(parents=True)
        log_file.write_text("log line", encoding="utf-8")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            log_file=log_file,
            skip_infra=True,
        )
        assert summary.log_file == log_file
        assert summary.skip_infra is True

    def test_generate_summary_empty_results(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=[],
            total_duration=0.0,
            output_dir=output_dir,
        )
        assert summary.slowest_stage is None
        assert summary.fastest_stage is None
        assert summary.failed_stages == []
        assert summary.inventory == []

    def test_slowest_excludes_failed(self, tmp_path: Path) -> None:
        """``_find_slowest_stage`` only considers successful stages."""
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("fast_ok", stage_num=1, success=True, duration=1.0),
            _result("slow_fail", stage_num=2, success=False, duration=100.0, exit_code=1),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=101.0,
            output_dir=output_dir,
        )
        # slowest should be the successful stage, not the long failed one
        assert summary.slowest_stage is not None
        assert summary.slowest_stage.stage_name == "fast_ok"


class TestGeneratePipelineSummary:
    """Tests for the ``generate_pipeline_summary`` convenience function."""

    def test_text_output(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        text = generate_pipeline_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            output_format="text",
        )
        assert "PIPELINE SUMMARY" in text
        assert "All stages completed successfully!" in text
        assert "Stage 1: setup" in text

    def test_json_output(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=3.0),
        ]
        text = generate_pipeline_summary(
            stage_results=results,
            total_duration=5.0,
            output_dir=output_dir,
            output_format="json",
        )
        data = json.loads(text)
        assert data["total_duration"] == 5.0
        assert len(data["stages"]) == 2
        assert data["stages"][0]["stage_name"] == "setup"
        assert data["performance"]["slowest_stage"]["stage_name"] == "tests"
        # fastest_stage excludes stage 1 (setup), so tests is the fastest
        assert data["performance"]["fastest_stage"]["stage_name"] == "tests"

    def test_html_output(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path, {"pdf/report.pdf": "PDF"})
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        html = generate_pipeline_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            output_format="html",
        )
        assert "<div class='pipeline-summary'>" in html
        assert "<h2>Pipeline Summary</h2>" in html
        assert "All stages completed successfully!" in html

    def test_text_output_with_failures(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("render", stage_num=7, success=False, duration=2.0, exit_code=1),
        ]
        text = generate_pipeline_summary(
            stage_results=results,
            total_duration=3.0,
            output_dir=output_dir,
            output_format="text",
        )
        assert "Pipeline completed with failures: render" in text
        assert "FAILED" in text

    def test_json_output_with_log_file(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        log_file = tmp_path / "projects" / "demo" / "output" / "logs" / "pipeline.log"
        log_file.parent.mkdir(parents=True)
        log_file.write_text("log", encoding="utf-8")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        text = generate_pipeline_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            log_file=log_file,
            output_format="json",
        )
        data = json.loads(text)
        assert data["log_file"] == str(log_file)
        assert "log_file_final" in data

    def test_html_output_with_failed_stage_and_error(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("render", stage_num=7, success=False, duration=2.0, exit_code=1, error_message="boom"),
        ]
        html = generate_pipeline_summary(
            stage_results=results,
            total_duration=3.0,
            output_dir=output_dir,
            output_format="html",
        )
        assert "Pipeline completed with failures: render" in html
        assert "Error: boom" in html
