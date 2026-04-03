"""Tests for infrastructure.core.pipeline.summary_formatters — comprehensive coverage."""

import json
from pathlib import Path

from infrastructure.core.files.inventory import FileInventoryManager, FileInventoryEntry
from infrastructure.core.pipeline.summary_formatters import (
    format_text_summary,
    format_json_summary,
    format_html_summary,
)
from infrastructure.core.pipeline.summary_models import PipelineSummary
from infrastructure.core.pipeline.types import PipelineStageResult


def _make_result(num, name, success=True, duration=1.0, exit_code=0, error=""):
    return PipelineStageResult(
        stage_num=num,
        stage_name=name,
        success=success,
        duration=duration,
        exit_code=exit_code,
        error_message=error,
    )


def _make_summary(**overrides):
    results = overrides.pop("stage_results", [
        _make_result(1, "Setup", duration=0.5),
        _make_result(2, "Build", duration=2.0),
        _make_result(3, "Test", duration=5.0),
    ])
    defaults = {
        "total_duration": sum(r.duration for r in results),
        "stage_results": results,
        "slowest_stage": max(results, key=lambda r: r.duration) if results else None,
        "fastest_stage": min(results, key=lambda r: r.duration) if results else None,
        "failed_stages": [r for r in results if not r.success],
        "inventory": [],
        "log_file": None,
        "skip_infra": False,
    }
    defaults.update(overrides)
    return PipelineSummary(**defaults)


class TestFormatTextSummary:
    def test_all_success(self):
        summary = _make_summary()
        mgr = FileInventoryManager()
        result = format_text_summary(summary, mgr)
        assert "All stages completed successfully" in result
        assert "Setup" in result
        assert "Build" in result
        assert "Test" in result

    def test_with_failures(self):
        results = [
            _make_result(1, "Setup", duration=0.5),
            _make_result(2, "Build", success=False, duration=2.0, exit_code=1, error="compile error"),
        ]
        summary = _make_summary(stage_results=results)
        mgr = FileInventoryManager()
        result = format_text_summary(summary, mgr)
        assert "failures" in result.lower()
        assert "Build" in result

    def test_with_log_file(self):
        summary = _make_summary(log_file=Path("/tmp/pipeline.log"))
        mgr = FileInventoryManager()
        result = format_text_summary(summary, mgr)
        assert "pipeline.log" in result

    def test_with_inventory(self, tmp_path):
        entry = FileInventoryEntry(
            path=tmp_path / "output" / "pdf" / "paper.pdf",
            size=1024,
            category="pdf",
            modified=1000.0,
        )
        summary = _make_summary(inventory=[entry])
        mgr = FileInventoryManager()
        result = format_text_summary(summary, mgr)
        assert "paper.pdf" in result

    def test_empty_stages(self):
        summary = _make_summary(
            stage_results=[],
            slowest_stage=None,
            fastest_stage=None,
        )
        mgr = FileInventoryManager()
        result = format_text_summary(summary, mgr)
        assert "PIPELINE SUMMARY" in result


class TestFormatJsonSummary:
    def test_basic(self):
        summary = _make_summary()
        result = format_json_summary(summary)
        data = json.loads(result)
        assert "total_duration" in data
        assert "stages" in data
        assert len(data["stages"]) == 3
        assert "performance" in data

    def test_with_log_file(self):
        summary = _make_summary(log_file=Path("/tmp/test.log"))
        result = format_json_summary(summary)
        data = json.loads(result)
        assert "log_file" in data

    def test_with_failures(self):
        results = [
            _make_result(1, "Build", success=False, exit_code=1, error="fail"),
        ]
        summary = _make_summary(stage_results=results)
        result = format_json_summary(summary)
        data = json.loads(result)
        assert len(data["performance"]["failed_stages"]) == 1


class TestFormatHtmlSummary:
    def test_basic(self):
        summary = _make_summary()
        mgr = FileInventoryManager()
        result = format_html_summary(summary, mgr)
        assert "<div" in result
        assert "Pipeline Summary" in result
        assert "Setup" in result

    def test_with_failures(self):
        results = [
            _make_result(1, "Build", success=False, exit_code=1, error="compile fail"),
        ]
        summary = _make_summary(stage_results=results)
        mgr = FileInventoryManager()
        result = format_html_summary(summary, mgr)
        assert "error" in result.lower()
        assert "compile fail" in result

    def test_with_log_file(self):
        summary = _make_summary(log_file=Path("/tmp/pipeline.log"))
        mgr = FileInventoryManager()
        result = format_html_summary(summary, mgr)
        assert "pipeline.log" in result

    def test_with_inventory(self, tmp_path):
        entry = FileInventoryEntry(
            path=tmp_path / "output" / "pdf" / "paper.pdf",
            size=2048,
            category="pdf",
            modified=1000.0,
        )
        summary = _make_summary(inventory=[entry])
        mgr = FileInventoryManager()
        result = format_html_summary(summary, mgr)
        assert "Generated Files" in result
