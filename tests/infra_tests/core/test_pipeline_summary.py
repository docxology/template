"""Tests for pipeline summary generation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path


from infrastructure.core.files.inventory import FileInventoryEntry, FileInventoryManager
from infrastructure.core.pipeline import PipelineStageResult
from infrastructure.core.pipeline.summary_models import PipelineSummary as PipelineSummaryDirect  # noqa: F401
from infrastructure.core.pipeline.summary_formatters import (
    format_html_summary,
    format_json_summary,
    format_text_summary,
)
from infrastructure.core.pipeline.summary import (
    PipelineSummary,
    PipelineSummaryGenerator,
    generate_pipeline_summary,
)
from infrastructure.core.pipeline.summary_helpers import (
    extract_project_name_from_path,
    find_base_output_dir,
    format_stage_result,
    get_final_log_path,
    stage_result_to_dict,
)


class TestPipelineSummary:
    """Test PipelineSummary dataclass."""

    def test_summary_creation(self):
        """Test summary creation."""
        stage_results = [
            PipelineStageResult(1, "Stage 1", True, 5.0),
            PipelineStageResult(2, "Stage 2", True, 10.0),
        ]

        inventory = [
            FileInventoryEntry(Path("/tmp/file1.pdf"), 1024, "pdf", 1234567890),
        ]

        summary = PipelineSummary(
            total_duration=15.0,
            stage_results=stage_results,
            slowest_stage=stage_results[1],
            fastest_stage=stage_results[0],
            failed_stages=[],
            inventory=inventory,
            log_file=Path("/tmp/pipeline.log"),
            skip_infra=False,
        )

        assert summary.total_duration == 15.0
        assert len(summary.stage_results) == 2
        assert summary.slowest_stage == stage_results[1]
        assert summary.fastest_stage == stage_results[0]
        assert summary.failed_stages == []
        assert len(summary.inventory) == 1
        assert summary.log_file == Path("/tmp/pipeline.log")
        assert summary.skip_infra is False


class TestPipelineSummaryGenerator:
    """Test PipelineSummaryGenerator class."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = PipelineSummaryGenerator()
        assert hasattr(generator, "file_inventory_manager")
        assert hasattr(generator, "generate_summary")

    def test_generate_summary_complete(self):
        """Test generating complete summary."""
        stage_results = [
            PipelineStageResult(1, "Setup", True, 2.0),
            PipelineStageResult(2, "Tests", True, 15.0),
            PipelineStageResult(3, "Analysis", True, 8.0),
            PipelineStageResult(4, "Render", False, 5.0, exit_code=1, error_message="Failed"),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"
            output_dir.mkdir()
            log_file = Path(tmp_dir) / "log.txt"
            log_file.write_text("Test log content")

            generator = PipelineSummaryGenerator()
            summary = generator.generate_summary(
                stage_results=stage_results,
                total_duration=30.0,
                output_dir=output_dir,
                log_file=log_file,
                skip_infra=False,
            )

            assert summary.total_duration == 30.0
            assert len(summary.stage_results) == 4
            assert summary.slowest_stage.stage_name == "Tests"  # 15.0s
            assert summary.fastest_stage.stage_name == "Analysis"  # 8.0s (fastest among stages 2-4)
            assert len(summary.failed_stages) == 1
            assert summary.failed_stages[0].stage_name == "Render"
            assert summary.log_file.exists()  # Should be the temp log file we created
            assert summary.skip_infra is False

    def test_generate_summary_no_successful_stages(self):
        """Test summary generation when no stages succeeded."""
        stage_results = [
            PipelineStageResult(1, "Stage 1", False, 5.0, exit_code=1),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"
            output_dir.mkdir()

            generator = PipelineSummaryGenerator()
            summary = generator.generate_summary(stage_results=stage_results, total_duration=5.0, output_dir=output_dir)

            assert summary.slowest_stage is None
            assert summary.fastest_stage is None
            assert len(summary.failed_stages) == 1

    def test_find_slowest_stage(self):
        """Test finding the slowest stage."""
        results = [
            PipelineStageResult(1, "Fast", True, 2.0),
            PipelineStageResult(2, "Slow", True, 10.0),
            PipelineStageResult(3, "Medium", True, 5.0),
        ]

        generator = PipelineSummaryGenerator()
        slowest = generator._find_slowest_stage(results)

        assert slowest is not None
        assert slowest.stage_name == "Slow"
        assert slowest.duration == 10.0

    def test_find_fastest_stage(self):
        """Test finding the fastest stage (excluding stage 1)."""
        results = [
            PipelineStageResult(1, "Setup", True, 1.0),  # Excluded from fastest
            PipelineStageResult(2, "Fast", True, 2.0),
            PipelineStageResult(3, "Slow", True, 10.0),
        ]

        generator = PipelineSummaryGenerator()
        fastest = generator._find_fastest_stage(results)

        assert fastest is not None
        assert fastest.stage_name == "Fast"
        assert fastest.duration == 2.0

    def test_find_fastest_stage_no_valid_stages(self):
        """Test fastest stage when no valid stages exist."""
        results = [
            PipelineStageResult(1, "Setup", True, 1.0),  # Only setup stage
        ]

        generator = PipelineSummaryGenerator()
        fastest = generator._find_fastest_stage(results)

        assert fastest is None

    def test_format_stage_result_success(self):
        """Test formatting successful stage result."""
        result = PipelineStageResult(1, "Test Stage", True, 5.2)
        total_duration = 20.0

        formatted = format_stage_result(result, total_duration, False)

        assert "✓ Stage 1: Test Stage (5.2s, 26.0%)" in formatted

    def test_format_stage_result_failure(self):
        """Test formatting failed stage result."""
        result = PipelineStageResult(2, "Failed Stage", False, 3.1, exit_code=1)
        total_duration = 20.0

        formatted = format_stage_result(result, total_duration, False)

        assert "✗ Stage 2: Failed Stage (3.1s) FAILED" in formatted

    def test_format_stage_result_skipped(self):
        """Test formatting skipped stage result."""
        result = PipelineStageResult(3, "Skipped", False, 0.0, exit_code=0)
        total_duration = 20.0

        formatted = format_stage_result(result, total_duration, True)

        assert "⊘ Stage 3: Skipped (skipped)" in formatted

    def test_format_text_summary(self):
        """Test formatting summary as text."""
        stage_results = [
            PipelineStageResult(1, "Setup", True, 2.0),
            PipelineStageResult(2, "Tests", True, 15.0),
        ]

        summary = PipelineSummary(
            total_duration=17.0,
            stage_results=stage_results,
            slowest_stage=stage_results[1],
            fastest_stage=stage_results[0],
            failed_stages=[],
            inventory=[],
            log_file=Path("/tmp/log.txt"),
        )

        generator = PipelineSummaryGenerator()
        text = generator.format_summary(summary, "text")

        assert "PIPELINE SUMMARY" in text
        assert "All stages completed successfully!" in text
        assert "Total Execution Time: 17.0s" in text
        assert "Average Stage Time: 8.5s" in text
        assert "Slowest Stage: Stage 2 - Tests" in text
        assert "Fastest Stage: Stage 1 - Setup" in text
        assert "Current: /tmp/log.txt" in text

    def test_format_json_summary(self):
        """Test formatting summary as JSON."""
        stage_results = [
            PipelineStageResult(1, "Setup", True, 2.0),
        ]

        summary = PipelineSummary(
            total_duration=2.0,
            stage_results=stage_results,
            slowest_stage=stage_results[0],
            fastest_stage=None,
            failed_stages=[],
            inventory=[],
        )

        generator = PipelineSummaryGenerator()
        json_str = generator.format_summary(summary, "json")

        data = json.loads(json_str)
        assert data["total_duration"] == 2.0
        assert len(data["stages"]) == 1
        assert data["stages"][0]["stage_name"] == "Setup"
        assert data["stages"][0]["success"] is True

    def test_format_html_summary(self):
        """Test formatting summary as HTML."""
        stage_results = [
            PipelineStageResult(1, "Setup", True, 2.0),
        ]

        summary = PipelineSummary(
            total_duration=2.0,
            stage_results=stage_results,
            slowest_stage=stage_results[0],
            fastest_stage=None,
            failed_stages=[],
            inventory=[],
        )

        generator = PipelineSummaryGenerator()
        html = generator.format_summary(summary, "html")

        assert "<div class='pipeline-summary'>" in html
        assert "<h2>Pipeline Summary</h2>" in html
        assert "All stages completed successfully!" in html
        assert "</div>" in html

    def test_get_final_log_path(self):
        """Test getting final log file path."""
        # Test project log path - use explicit test path that won't resolve to real filesystem
        log_file = Path("/test/projects/myproject/output/logs/pipeline.log")
        final_path = get_final_log_path(log_file)
        assert str(final_path) == "output/logs/pipeline.log"

        # Test non-project path
        log_file = Path("/tmp/log.txt")
        final_path = get_final_log_path(log_file)
        assert final_path == log_file

    def test_find_base_output_dir(self):
        """Test finding base output directory from inventory."""
        inventory = [
            FileInventoryEntry(Path("output/pdf/file.pdf"), 1024, "pdf", 0),
            FileInventoryEntry(Path("output/figures/plot.png"), 2048, "figures", 0),
        ]

        base_dir = find_base_output_dir(inventory)
        assert base_dir == Path("output")

    def test_extract_project_name_from_path(self):
        """Test extracting project name from output path."""
        test_cases = [
            (Path("projects/myproject/output/"), "myproject"),
            (Path("output/"), None),
            (Path("/tmp/output/"), None),
        ]

        for path, expected in test_cases:
            result = extract_project_name_from_path(path)
            assert result == expected

    def test_stage_result_to_dict(self):
        """Test converting stage result to dictionary."""
        result = PipelineStageResult(1, "Test", True, 5.2)
        dict_result = stage_result_to_dict(result)

        assert dict_result["stage_num"] == 1
        assert dict_result["stage_name"] == "Test"
        assert dict_result["success"] is True
        assert dict_result["duration"] == 5.2

        # Test None input
        assert stage_result_to_dict(None) is None


class TestConvenienceFunction:
    """Test convenience function."""

    def test_generate_pipeline_summary_function(self):
        """Test generate_pipeline_summary convenience function."""
        # Create real pipeline stage results (not checkpoint StageResult)
        stage_results = [
            PipelineStageResult(stage_num=1, stage_name="Setup", success=True, duration=2.0),
            PipelineStageResult(stage_num=2, stage_name="Tests", success=True, duration=5.0),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "pipeline.log"
            log_file.write_text("Pipeline execution log")

            result = generate_pipeline_summary(stage_results, 7.0, log_file)

            # Should return a formatted summary string
            assert isinstance(result, str)
            assert "PIPELINE SUMMARY" in result
            assert "Total Execution Time: 7.0s" in result


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
    results = overrides.pop(
        "stage_results",
        [
            _make_result(1, "Setup", duration=0.5),
            _make_result(2, "Build", duration=2.0),
            _make_result(3, "Test", duration=5.0),
        ],
    )
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
    return PipelineSummaryDirect(**defaults)


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
