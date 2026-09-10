"""Stage-result helper and model tests split from test_summary_reporting.py.

Exercises real code paths in:

* ``infrastructure.core.pipeline.summary_helpers`` — ``format_stage_result``,
  ``stage_result_to_dict``, ``get_final_log_path``, ``find_base_output_dir``,
  ``extract_project_name_from_path``.
* ``infrastructure.core.pipeline.summary_models`` — ``PipelineSummary.executed_stages``.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline.summary_helpers import (
    extract_project_name_from_path,
    find_base_output_dir,
    format_stage_result,
    get_final_log_path,
    stage_result_to_dict,
)
from infrastructure.core.pipeline.summary_models import PipelineSummary
from ._summary_reporting_helpers import _result


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
