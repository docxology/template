"""No-mock tests for pipeline summary generation, formatting, and post-run reporting.

Exercises real code paths in:

* ``infrastructure.core.pipeline.summary`` — ``PipelineSummaryGenerator``,
  ``generate_pipeline_summary``.
* ``infrastructure.core.pipeline.summary_helpers`` — ``format_stage_result``,
  ``stage_result_to_dict``, ``get_final_log_path``, ``find_base_output_dir``,
  ``extract_project_name_from_path``.
* ``infrastructure.core.pipeline.summary_formatters`` — ``format_text_summary``,
  ``format_json_summary``, ``format_html_summary``.
* ``infrastructure.core.pipeline.summary_models`` — ``PipelineSummary.executed_stages``.
* ``infrastructure.core.pipeline.post_run_reporting`` —
  ``write_pipeline_post_run_reports`` with and without a pipeline log file.
"""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.files.inventory import FileInventoryManager
from infrastructure.core.pipeline.post_run_reporting import write_pipeline_post_run_reports
from infrastructure.core.pipeline.summary import (
    PipelineSummaryGenerator,
    generate_pipeline_summary,
)
from infrastructure.core.pipeline.summary_formatters import (
    format_html_summary,
    format_json_summary,
    format_text_summary,
)
from infrastructure.core.pipeline.summary_helpers import (
    extract_project_name_from_path,
    find_base_output_dir,
    format_stage_result,
    get_final_log_path,
    stage_result_to_dict,
)
from infrastructure.core.pipeline.summary_models import PipelineSummary
from infrastructure.core.pipeline.types import PipelineStageResult


def _result(
    name: str,
    *,
    stage_num: int = 1,
    success: bool = True,
    duration: float = 1.0,
    exit_code: int = 0,
    error_message: str = "",
) -> PipelineStageResult:
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=name,
        success=success,
        duration=duration,
        exit_code=exit_code,
        error_message=error_message,
    )


def _make_output_dir(tmp_path: Path, files: dict[str, str] | None = None) -> Path:
    """Create an ``output/`` directory tree with optional files.

    ``files`` maps ``category/filename`` → content. Categories are standard
    output subdirectories (``pdf``, ``data``, ``reports``, etc.).
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    if files:
        for rel, content in files.items():
            path = output_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    return output_dir


# ===========================================================================
# summary_helpers — format_stage_result
# ===========================================================================


class TestFormatStageResult:
    """Tests for ``format_stage_result``."""

    def test_successful_stage(self) -> None:
        result = _result("setup", stage_num=1, success=True, duration=2.5)
        formatted = format_stage_result(result, total_duration=10.0, skip_infra=False)
        assert "✓ Stage 1: setup" in formatted
        assert "2.5s" in formatted
        assert "25.0%" in formatted

    def test_bottleneck_stage(self) -> None:
        """A stage taking >10s gets the bottleneck marker."""
        result = _result("analysis", stage_num=4, success=True, duration=15.0)
        formatted = format_stage_result(result, total_duration=30.0, skip_infra=False)
        assert "⚠ bottleneck" in formatted
        assert "✓ Stage 4: analysis" in formatted

    def test_failed_stage(self) -> None:
        result = _result("render", stage_num=7, success=False, duration=5.0, exit_code=1)
        formatted = format_stage_result(result, total_duration=20.0, skip_infra=False)
        assert "✗ Stage 7: render" in formatted
        assert "FAILED" in formatted
        assert "5.0s" in formatted

    def test_skipped_stage(self) -> None:
        """A stage that is not successful but has exit_code 0 is 'skipped'."""
        result = _result("llm_review", stage_num=9, success=False, duration=0.0, exit_code=0)
        formatted = format_stage_result(result, total_duration=10.0, skip_infra=False)
        assert "⊘ Stage 9: llm_review (skipped)" in formatted

    def test_zero_total_duration_no_division_error(self) -> None:
        """When total_duration is 0, percentage falls back to 0 without ZeroDivisionError."""
        result = _result("setup", stage_num=1, success=True, duration=1.0)
        formatted = format_stage_result(result, total_duration=0.0, skip_infra=False)
        assert "✓ Stage 1: setup" in formatted
        assert "0.0%" in formatted


# ===========================================================================
# summary_helpers — stage_result_to_dict
# ===========================================================================


class TestStageResultToDict:
    """Tests for ``stage_result_to_dict``."""

    def test_converts_valid_result(self) -> None:
        result = _result("setup", stage_num=1, success=True, duration=2.5, error_message="ok")
        d = stage_result_to_dict(result)
        assert d is not None
        assert d["stage_num"] == 1
        assert d["stage_name"] == "setup"
        assert d["success"] is True
        assert d["duration"] == 2.5
        assert d["exit_code"] == 0
        assert d["error_message"] == "ok"
        assert "duration_formatted" in d

    def test_none_returns_none(self) -> None:
        assert stage_result_to_dict(None) is None


# ===========================================================================
# summary_helpers — get_final_log_path
# ===========================================================================


class TestGetFinalLogPath:
    """Tests for ``get_final_log_path``."""

    def test_projects_output_path_shortened(self) -> None:
        log_file = Path("projects/my_project/output/logs/pipeline.log")
        final = get_final_log_path(log_file)
        assert str(final) == "output/logs/pipeline.log"

    def test_non_projects_path_unchanged(self) -> None:
        log_file = Path("output/logs/pipeline.log")
        final = get_final_log_path(log_file)
        assert final == log_file

    def test_absolute_path_with_projects_and_output(self) -> None:
        log_file = Path("/repo/projects/proj/output/logs/pipeline.log")
        final = get_final_log_path(log_file)
        assert str(final) == "output/logs/pipeline.log"

    def test_path_without_output_unchanged(self) -> None:
        log_file = Path("projects/my_project/manuscript/config.yaml")
        final = get_final_log_path(log_file)
        assert final == log_file


# ===========================================================================
# summary_helpers — find_base_output_dir
# ===========================================================================


class TestFindBaseOutputDir:
    """Tests for ``find_base_output_dir``."""

    def test_empty_inventory_returns_none(self, tmp_path: Path) -> None:
        assert find_base_output_dir([]) is None

    def test_single_entry_returns_parent(self, tmp_path: Path) -> None:
        from infrastructure.core.files.inventory_entry import FileInventoryEntry

        file_path = tmp_path / "output" / "pdf" / "report.pdf"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("x", encoding="utf-8")
        entry = FileInventoryEntry(path=file_path, size=1, category="pdf", modified=0.0)
        result = find_base_output_dir([entry])
        assert result == file_path.parent

    def test_multiple_entries_find_common_parent(self, tmp_path: Path) -> None:
        from infrastructure.core.files.inventory_entry import FileInventoryEntry

        pdf_dir = tmp_path / "output" / "pdf"
        data_dir = tmp_path / "output" / "data"
        pdf_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        pdf_file = pdf_dir / "report.pdf"
        data_file = data_dir / "results.csv"
        pdf_file.write_text("pdf", encoding="utf-8")
        data_file.write_text("csv", encoding="utf-8")
        entries = [
            FileInventoryEntry(path=pdf_file, size=3, category="pdf", modified=0.0),
            FileInventoryEntry(path=data_file, size=3, category="data", modified=0.0),
        ]
        result = find_base_output_dir(entries)
        assert result == tmp_path / "output"


# ===========================================================================
# summary_helpers — extract_project_name_from_path
# ===========================================================================


class TestExtractProjectNameFromPath:
    """Tests for ``extract_project_name_from_path``."""

    def test_standard_projects_output_path(self) -> None:
        path = Path("projects/my_project/output/pdf/report.pdf")
        assert extract_project_name_from_path(path) == "my_project"

    def test_nested_template_project_path(self) -> None:
        path = Path("projects/templates/template_code_project/output/data/results.csv")
        assert extract_project_name_from_path(path) == "templates"

    def test_no_projects_keyword(self) -> None:
        path = Path("output/pdf/report.pdf")
        assert extract_project_name_from_path(path) is None

    def test_no_output_keyword(self) -> None:
        path = Path("projects/my_project/manuscript/config.yaml")
        assert extract_project_name_from_path(path) is None


# ===========================================================================
# summary_models — PipelineSummary.executed_stages
# ===========================================================================


class TestPipelineSummaryExecutedStages:
    """Tests for ``PipelineSummary.executed_stages`` property."""

    def test_executed_stages_excludes_skipped(self) -> None:
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("skipped_stage", stage_num=2, success=False, duration=0.0, exit_code=0),
            _result("tests", stage_num=3, success=True, duration=2.0),
        ]
        summary = PipelineSummary(
            total_duration=3.0,
            stage_results=results,
            slowest_stage=results[2],
            fastest_stage=results[0],
            failed_stages=[],
            inventory=[],
        )
        executed = summary.executed_stages
        assert len(executed) == 2
        assert executed[0].stage_name == "setup"
        assert executed[1].stage_name == "tests"

    def test_executed_stages_all_executed(self) -> None:
        results = [
            _result("a", stage_num=1, success=True, duration=1.0),
            _result("b", stage_num=2, success=True, duration=2.0),
        ]
        summary = PipelineSummary(
            total_duration=3.0,
            stage_results=results,
            slowest_stage=results[1],
            fastest_stage=results[0],
            failed_stages=[],
            inventory=[],
        )
        assert len(summary.executed_stages) == 2

    def test_executed_stages_empty_when_all_skipped(self) -> None:
        results = [
            _result("a", stage_num=1, success=False, duration=0.0, exit_code=0),
        ]
        summary = PipelineSummary(
            total_duration=0.0,
            stage_results=results,
            slowest_stage=None,
            fastest_stage=None,
            failed_stages=[],
            inventory=[],
        )
        assert summary.executed_stages == []


# ===========================================================================
# summary — PipelineSummaryGenerator.generate_summary
# ===========================================================================


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


# ===========================================================================
# summary — generate_pipeline_summary (convenience function)
# ===========================================================================


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


# ===========================================================================
# summary_formatters — format_text_summary detailed assertions
# ===========================================================================


class TestFormatTextSummary:
    """Detailed tests for ``format_text_summary``."""

    def test_text_summary_includes_log_file_section(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        log_file = Path("projects/demo/output/logs/pipeline.log")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            log_file=log_file,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        assert "Full pipeline log:" in text
        assert str(log_file) in text
        assert "Pipeline Log:" in text
        assert "Current:" in text

    def test_text_summary_includes_final_log_path_note(self, tmp_path: Path) -> None:
        """When log path changes after copy, a 'Final' note is added."""
        output_dir = _make_output_dir(tmp_path)
        log_file = Path("projects/demo/output/logs/pipeline.log")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            log_file=log_file,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        assert "Will be available at:" in text
        assert "output/logs/pipeline.log" in text

    def test_text_summary_no_log_file(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        assert "Pipeline Log:" not in text

    def test_text_summary_with_inventory_and_project_name(self, tmp_path: Path) -> None:
        """Inventory with a ``projects/<name>/output/`` base_dir surfaces the project name note."""
        # Create real files under projects/.../output for project_name extraction
        project_output = tmp_path / "projects" / "demo" / "output"
        project_output.mkdir(parents=True)
        (project_output / "pdf").mkdir(parents=True)
        (project_output / "pdf" / "report.pdf").write_text("PDF", encoding="utf-8")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=project_output,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        # The note about project output should appear
        assert "Files are also available in projects/demo/output/" in text or "Files will be copied" in text

    def test_text_summary_performance_metrics(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=8.0),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=10.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        assert "Performance Metrics:" in text
        assert "Total Execution Time: 10.0s" in text
        assert "Average Stage Time:" in text
        assert "Slowest Stage:" in text
        assert "Stage 2 - tests" in text
        assert "Fastest Stage:" in text


# ===========================================================================
# summary_formatters — format_json_summary detailed assertions
# ===========================================================================


class TestFormatJsonSummary:
    """Detailed tests for ``format_json_summary``."""

    def test_json_summary_structure(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path, {"data/results.csv": "a,b\n1,2"})
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=3.0),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=5.0,
            output_dir=output_dir,
        )
        text = format_json_summary(summary)
        data = json.loads(text)
        assert data["total_duration"] == 5.0
        assert "total_duration_formatted" in data
        assert len(data["stages"]) == 2
        assert data["stages"][0]["stage_name"] == "setup"
        assert data["stages"][1]["stage_name"] == "tests"
        assert data["performance"]["slowest_stage"]["stage_name"] == "tests"
        # fastest_stage excludes stage 1 (setup), so tests is the fastest
        assert data["performance"]["fastest_stage"]["stage_name"] == "tests"
        assert data["performance"]["failed_stages"] == []
        assert data["files"]["count"] == 1
        assert data["files"]["inventory"][0]["category"] == "data"

    def test_json_summary_no_log_file(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
        )
        text = format_json_summary(summary)
        data = json.loads(text)
        assert "log_file" not in data
        assert "log_file_final" not in data

    def test_json_summary_with_failed_stages(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("render", stage_num=7, success=False, duration=2.0, exit_code=1, error_message="err"),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=3.0,
            output_dir=output_dir,
        )
        text = format_json_summary(summary)
        data = json.loads(text)
        assert len(data["performance"]["failed_stages"]) == 1
        assert data["performance"]["failed_stages"][0]["stage_name"] == "render"
        assert data["performance"]["slowest_stage"]["stage_name"] == "setup"


# ===========================================================================
# summary_formatters — format_html_summary detailed assertions
# ===========================================================================


class TestFormatHtmlSummary:
    """Detailed tests for ``format_html_summary``."""

    def test_html_summary_basic_structure(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "<div class='pipeline-summary'>" in html
        assert "</div>" in html
        assert "All stages completed successfully!" in html

    def test_html_summary_with_failures(self, tmp_path: Path) -> None:
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
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "Pipeline completed with failures: render" in html
        assert "class='error'" in html

    def test_html_summary_with_log_file(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        log_file = Path("projects/demo/output/logs/pipeline.log")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            log_file=log_file,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "Log file:" in html
        assert str(log_file) in html
        assert "Will be available at:" in html

    def test_html_summary_performance_metrics(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=8.0),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=10.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "Total Execution Time: 10.0s" in html
        assert "Average Stage Time:" in html
        assert "Slowest Stage:" in html
        assert "Fastest Stage:" in html

    def test_html_summary_with_inventory(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path, {"pdf/report.pdf": "PDF content"})
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "Generated Files" in html


# ===========================================================================
# post_run_reporting — write_pipeline_post_run_reports
# ===========================================================================


class TestWritePipelinePostRunReports:
    """Tests for ``write_pipeline_post_run_reports``."""

    def test_creates_reports_dir_and_json_report(self, tmp_path: Path) -> None:
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [_result("setup"), _result("tests")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        assert reports_dir.is_dir()
        json_reports = list(reports_dir.glob("pipeline_report*.json"))
        assert json_reports, "expected JSON pipeline report"

    def test_creates_html_and_markdown_reports(self, tmp_path: Path) -> None:
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [_result("setup"), _result("tests")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        html_reports = list(reports_dir.glob("pipeline_report*.html"))
        md_reports = list(reports_dir.glob("pipeline_report*.md"))
        assert html_reports, "expected HTML pipeline report"
        assert md_reports, "expected Markdown pipeline report"

    def test_with_pipeline_log_file(self, tmp_path: Path) -> None:
        """A non-empty pipeline log triggers log summary generation."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        logs_dir = output_dir / "logs"
        logs_dir.mkdir(parents=True)
        log_file = logs_dir / "pipeline.log"
        log_file.write_text(
            "\n".join(
                [
                    "INFO setup started",
                    "WARNING deprecated config",
                    "ERROR something failed",
                    "DEBUG detail",
                ]
            ),
            encoding="utf-8",
        )
        results = [_result("setup")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        log_summary = reports_dir / "log_summary.txt"
        assert log_summary.is_file()
        content = log_summary.read_text(encoding="utf-8")
        assert "LOG ANALYSIS" in content
        assert "Total Lines: 4" in content
        assert "WARNING" in content
        assert "ERROR" in content

    def test_empty_log_file_still_generates_summary(self, tmp_path: Path) -> None:
        """An empty pipeline log still produces a log summary (the guard is existence, not size)."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        logs_dir = output_dir / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "pipeline.log").write_text("", encoding="utf-8")
        results = [_result("setup")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        log_summary = reports_dir / "log_summary.txt"
        # The log_summary is generated because the file exists; content has 0 lines
        assert log_summary.is_file()
        content = log_summary.read_text(encoding="utf-8")
        assert "LOG ANALYSIS" in content
        assert "Total Lines: 0" in content

    def test_no_log_file(self, tmp_path: Path) -> None:
        """Missing pipeline log does not crash; reports are still generated."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [_result("setup")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        assert reports_dir.is_dir()
        # JSON report should still be generated
        json_reports = list(reports_dir.glob("pipeline_report*.json"))
        assert json_reports

    def test_json_report_content_has_stages(self, tmp_path: Path) -> None:
        """The generated JSON report contains the stage data."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=5.0),
        ]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=True,
        )

        reports_dir = output_dir / "reports"
        json_file = reports_dir / "pipeline_report.json"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["total_duration"] == 7.0
        assert len(data["stages"]) == 2
        assert data["stages"][0]["name"] == "setup"
        assert data["stages"][1]["name"] == "tests"

    def test_with_failed_stage(self, tmp_path: Path) -> None:
        """Reports are still generated when a stage fails."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("render", stage_num=7, success=False, duration=2.0, exit_code=1),
        ]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        json_file = reports_dir / "pipeline_report.json"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["total_duration"] == 3.0
        assert len(data["stages"]) == 2
        assert data["stages"][1]["exit_code"] == 1
