"""Pipeline report assembly and saved-format tests (formerly part of test_pipeline_reporter.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.reporting.pipeline_html import generate_html_report
from infrastructure.reporting.pipeline_io import save_pipeline_report
from infrastructure.reporting.pipeline_markdown import _generate_pipeline_markdown
from infrastructure.reporting.pipeline_report_model import generate_pipeline_report

from ._pipeline_reporter_helpers import _stage_results


def test_generate_pipeline_report_status_and_fields(tmp_path: Path) -> None:
    test_results = {"summary": {"total_tests": 10, "total_passed": 9, "project_coverage": 92.1}}
    validation_results = {"checks": {"pdf_validation": True}}

    report = generate_pipeline_report(
        stage_results=_stage_results(),
        total_duration=7.0,
        repo_root=tmp_path,
        test_results=test_results,
        validation_results=validation_results,
        performance_metrics={"peak_memory_mb": 123.4},
        error_summary={"total_errors": 1},
        output_statistics={"pdf_files": 2, "figures": 3, "data_files": 1},
    )

    assert report.total_duration == pytest.approx(7.0)
    assert [s.status for s in report.stages] == ["passed", "failed", "passed"]
    assert report.test_results == test_results
    assert report.validation_results == validation_results
    assert report.error_summary == {"total_errors": 1}


def test_save_pipeline_report_creates_all_formats(tmp_path: Path) -> None:
    report = generate_pipeline_report(stage_results=_stage_results(), total_duration=7.0, repo_root=tmp_path)
    saved = save_pipeline_report(report, tmp_path, formats=["json", "markdown", "html"])

    json_path = saved["json"]
    md_path = saved["markdown"]
    html_path = saved["html"]

    assert json_path.exists() and md_path.exists() and html_path.exists()

    data = json.loads(json_path.read_text())
    assert data["total_duration"] == 7.0
    assert data["stages"][0]["name"] == "setup"

    md_content = md_path.read_text()
    assert "Pipeline Execution Report" in md_content
    assert "| setup | ✅ passed" in md_content

    html_content = html_path.read_text()
    assert "Pipeline Execution Report" in html_content
    assert "analysis" in html_content


def test_generate_reports_format_duration_and_success_rate() -> None:
    report = generate_pipeline_report(stage_results=_stage_results(), total_duration=7.0, repo_root=Path("."))

    md_content = _generate_pipeline_markdown(report)
    assert "Success Rate" in md_content
    assert "Stages Passed" in md_content

    html_content = generate_html_report(report)
    assert "<table>" in html_content
    assert "Stages Executed" in html_content


def test_save_pipeline_report_respects_formats(tmp_path: Path) -> None:
    report = generate_pipeline_report(stage_results=_stage_results(), total_duration=3.0, repo_root=tmp_path)
    saved = save_pipeline_report(report, tmp_path, formats=["json"])
    assert "json" in saved and saved["json"].exists()
    assert not (tmp_path / "pipeline_report.md").exists()
    assert not (tmp_path / "pipeline_report.html").exists()


def test_generate_pipeline_report_empty_stages(tmp_path: Path) -> None:
    """Test report generation with empty stage list."""
    report = generate_pipeline_report(stage_results=[], total_duration=0.0, repo_root=tmp_path)
    assert len(report.stages) == 0
    assert report.total_duration == 0.0


def test_generate_pipeline_report_missing_fields(tmp_path: Path) -> None:
    """Test report generation with missing optional fields in stage results."""
    stage_results = [
        {"name": "setup"},  # Missing exit_code and duration
        {"name": "tests", "exit_code": 0},  # Missing duration
    ]
    report = generate_pipeline_report(stage_results=stage_results, total_duration=5.0, repo_root=tmp_path)
    assert len(report.stages) == 2
    assert report.stages[0].name == "setup"
    assert report.stages[0].exit_code == 1  # Default for missing exit_code
    assert report.stages[0].duration == 0.0  # Default for missing duration


def test_generate_pipeline_report_default_formats(tmp_path: Path) -> None:
    """Test save_pipeline_report uses default formats when None."""
    report = generate_pipeline_report(stage_results=_stage_results(), total_duration=5.0, repo_root=tmp_path)
    saved = save_pipeline_report(report, tmp_path, formats=None)
    assert "json" in saved
    assert "markdown" in saved
    assert "html" in saved


def test_stage_result_dataclass_fields() -> None:
    """Test StageResult dataclass with all fields."""
    from infrastructure.core.runtime.checkpoint import StageResult

    stage = StageResult(
        name="test",
        exit_code=0,
        duration=1.5,
        status="passed",
    )
    assert stage.name == "test"
    assert stage.exit_code == 0
    assert stage.duration == 1.5
    assert stage.status == "passed"


def test_pipeline_report_dataclass_fields() -> None:
    """Test PipelineReport dataclass with all fields."""
    from infrastructure.reporting.pipeline_report_model import PipelineReport
    from infrastructure.core.runtime.checkpoint import StageResult as ReportingStageResult

    report = PipelineReport(
        timestamp="2025-01-01T00:00:00",
        total_duration=5.0,
        stages=[ReportingStageResult(name="test", exit_code=0, duration=1.0, status="passed")],
        test_results={"summary": {"total_tests": 10}},
        validation_results={"checks": {"pdf": True}},
        performance_metrics={"duration": 5.0},
        error_summary={"total_errors": 0},
        output_statistics={"pdf_files": 1},
    )
    assert report.timestamp == "2025-01-01T00:00:00"
    assert report.total_duration == 5.0
    assert len(report.stages) == 1
    assert report.test_results is not None
    assert report.validation_results is not None


def test_save_pipeline_report_raises_oserror_on_unwritable_dir(tmp_path: Path) -> None:
    """save_pipeline_report raises OSError when the output directory is not writable."""
    import stat

    report = generate_pipeline_report(
        stage_results=[{"name": "setup", "exit_code": 0, "duration": 0.1}],
        total_duration=0.1,
        repo_root=tmp_path,
    )

    # Create a read-only directory so writes will fail
    output_dir = tmp_path / "readonly_output"
    output_dir.mkdir()
    output_dir.chmod(stat.S_IREAD | stat.S_IEXEC)

    try:
        with pytest.raises(OSError):
            save_pipeline_report(report, output_dir, formats=["json"])
    finally:
        # Restore permissions so pytest cleanup can delete the directory
        output_dir.chmod(stat.S_IRWXU)
