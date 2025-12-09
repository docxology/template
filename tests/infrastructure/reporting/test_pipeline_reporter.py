from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.reporting.pipeline_reporter import (
    generate_html_report,
    generate_markdown_report,
    generate_error_markdown,
    generate_error_summary,
    generate_performance_report,
    generate_validation_markdown,
    generate_validation_report,
    generate_pipeline_report,
    generate_test_report,
    save_pipeline_report,
)


def _stage_results() -> list[dict[str, object]]:
    return [
        {"name": "setup", "exit_code": 0, "duration": 1.2},
        {"name": "tests", "exit_code": 1, "duration": 2.8},
        {"name": "analysis", "exit_code": 0, "duration": 3.0},
    ]


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

    md_content = generate_markdown_report(report)
    assert "Success Rate" in md_content
    assert "Stages Passed" in md_content

    html_content = generate_html_report(report)
    assert "<table>" in html_content
    assert "Stages Executed" in html_content


def test_generate_markdown_report_includes_sections() -> None:
    report = generate_pipeline_report(
        stage_results=_stage_results(),
        total_duration=9.5,
        repo_root=Path("."),
        test_results={"summary": {"total_tests": 5, "total_passed": 4, "total_failed": 1, "total_skipped": 0, "infrastructure_coverage": 61.48, "project_coverage": 99.88}},
        validation_results={"checks": {"pdf": True}},
        performance_metrics={"duration": 9.5},
        error_summary={"total_errors": 2},
        output_statistics={"pdf_files": 2, "figures": 1, "data_files": 3},
    )

    md_content = generate_markdown_report(report)
    assert "Test Results" in md_content
    assert "Validation Results" in md_content
    assert "Performance Metrics" in md_content
    assert "Error Summary" in md_content
    assert "Output Statistics" in md_content
    assert "Infrastructure Coverage" in md_content
    assert "Project Coverage" in md_content


def test_generate_html_report_includes_test_coverage() -> None:
    report = generate_pipeline_report(
        stage_results=_stage_results(),
        total_duration=5.0,
        repo_root=Path("."),
        test_results={"summary": {"total_tests": 3, "total_passed": 3, "total_failed": 0, "total_skipped": 0, "infrastructure_coverage": 70.0, "project_coverage": 99.0}},
    )

    html = generate_html_report(report)
    assert "Pipeline Execution Report" in html
    assert "Infrastructure Coverage" in html
    assert "Project Coverage" in html


def test_generate_validation_report_and_markdown(tmp_path: Path) -> None:
    validation_results = {"checks": {"pdf_validation": True, "markdown_validation": False}}
    saved = generate_validation_report(validation_results, tmp_path)

    assert (tmp_path / "validation_report.json").exists()
    assert (tmp_path / "validation_report.md").exists()

    md = generate_validation_markdown(validation_results)
    assert "pdf_validation" in md
    assert "markdown_validation" in md


def test_generate_performance_and_test_reports(tmp_path: Path) -> None:
    perf = {"total_duration": 12.3, "peak_memory_mb": 256}
    path = generate_performance_report(perf, tmp_path)
    assert path.exists()

    test_path = generate_test_report({"summary": {}}, tmp_path)
    assert test_path.name == "test_results.json"


def test_generate_error_summary_and_markdown_truncation(tmp_path: Path) -> None:
    errors = [{"type": "stage_failure", "message": f"fail {i}", "file": f"f{i}.py", "suggestions": ["fix"]} for i in range(12)]
    summary = generate_error_summary(errors, tmp_path)
    assert summary["total_errors"] == 12
    assert summary["errors_by_type"]["stage_failure"] == 12
    assert (tmp_path / "error_summary.json").exists()
    assert (tmp_path / "error_summary.md").exists()

    md = generate_error_markdown(summary)
    assert "Error Summary" in md
    assert "... and 2 more errors" in md


def test_save_pipeline_report_respects_formats(tmp_path: Path) -> None:
    report = generate_pipeline_report(stage_results=_stage_results(), total_duration=3.0, repo_root=tmp_path)
    saved = save_pipeline_report(report, tmp_path, formats=["json"])
    assert "json" in saved and saved["json"].exists()
    assert not (tmp_path / "pipeline_report.md").exists()
    assert not (tmp_path / "pipeline_report.html").exists()


def test_generate_pipeline_report_empty_stages(tmp_path: Path) -> None:
    """Test report generation with empty stage list."""
    report = generate_pipeline_report(
        stage_results=[],
        total_duration=0.0,
        repo_root=tmp_path
    )
    assert len(report.stages) == 0
    assert report.total_duration == 0.0


def test_generate_pipeline_report_missing_fields(tmp_path: Path) -> None:
    """Test report generation with missing optional fields in stage results."""
    stage_results = [
        {"name": "setup"},  # Missing exit_code and duration
        {"name": "tests", "exit_code": 0},  # Missing duration
    ]
    report = generate_pipeline_report(
        stage_results=stage_results,
        total_duration=5.0,
        repo_root=tmp_path
    )
    assert len(report.stages) == 2
    assert report.stages[0].name == "setup"
    assert report.stages[0].exit_code == 1  # Default for missing exit_code
    assert report.stages[0].duration == 0.0  # Default for missing duration


def test_generate_pipeline_report_default_formats(tmp_path: Path) -> None:
    """Test save_pipeline_report uses default formats when None."""
    report = generate_pipeline_report(
        stage_results=_stage_results(),
        total_duration=5.0,
        repo_root=tmp_path
    )
    saved = save_pipeline_report(report, tmp_path, formats=None)
    assert "json" in saved
    assert "markdown" in saved
    assert "html" in saved


def test_generate_markdown_report_empty_sections() -> None:
    """Test markdown report generation with no optional sections."""
    report = generate_pipeline_report(
        stage_results=[{"name": "setup", "exit_code": 0, "duration": 1.0}],
        total_duration=1.0,
        repo_root=Path(".")
    )
    md_content = generate_markdown_report(report)
    assert "Pipeline Execution Report" in md_content
    assert "Summary" in md_content
    assert "Stage Results" in md_content
    # Should not have optional sections
    assert "Test Results" not in md_content
    assert "Error Summary" not in md_content


def test_generate_html_report_all_stages_passed() -> None:
    """Test HTML report with all stages passed."""
    report = generate_pipeline_report(
        stage_results=[
            {"name": "setup", "exit_code": 0, "duration": 1.0},
            {"name": "tests", "exit_code": 0, "duration": 2.0},
        ],
        total_duration=3.0,
        repo_root=Path(".")
    )
    html = generate_html_report(report)
    assert "100.0%" in html  # Success rate
    assert "status-passed" in html


def test_generate_validation_markdown_empty_checks() -> None:
    """Test validation markdown with empty checks."""
    results = {"checks": {}}
    md = generate_validation_markdown(results)
    assert "Validation Report" in md
    assert "Validation Checks" in md


def test_generate_error_summary_empty_errors(tmp_path: Path) -> None:
    """Test error summary with no errors."""
    summary = generate_error_summary([], tmp_path)
    assert summary["total_errors"] == 0
    assert summary["errors_by_type"] == {}
    assert (tmp_path / "error_summary.json").exists()
    assert (tmp_path / "error_summary.md").exists()


def test_generate_error_markdown_no_errors() -> None:
    """Test error markdown generation with no errors."""
    summary = {"total_errors": 0, "errors_by_type": {}, "errors": []}
    md = generate_error_markdown(summary)
    assert "Error Summary" in md
    assert "**Total Errors:** 0" in md


def test_generate_error_markdown_with_suggestions() -> None:
    """Test error markdown includes suggestions when present."""
    summary = {
        "total_errors": 1,
        "errors_by_type": {"test_failure": 1},
        "errors": [{
            "type": "test_failure",
            "message": "Test failed",
            "suggestions": ["Fix assertion", "Check data"]
        }]
    }
    md = generate_error_markdown(summary)
    assert "Fix assertion" in md
    assert "Check data" in md


def test_stage_result_dataclass_fields() -> None:
    """Test StageResult dataclass with all fields."""
    from infrastructure.reporting.pipeline_reporter import StageResult
    
    stage = StageResult(
        name="test",
        exit_code=0,
        duration=1.5,
        status="passed",
        output_files=["file1.pdf"],
        errors=["error1"],
        warnings=["warning1"]
    )
    assert stage.name == "test"
    assert stage.exit_code == 0
    assert stage.duration == 1.5
    assert stage.status == "passed"
    assert stage.output_files == ["file1.pdf"]
    assert stage.errors == ["error1"]
    assert stage.warnings == ["warning1"]


def test_pipeline_report_dataclass_fields() -> None:
    """Test PipelineReport dataclass with all fields."""
    from infrastructure.reporting.pipeline_reporter import PipelineReport, StageResult
    
    report = PipelineReport(
        timestamp="2025-01-01T00:00:00",
        total_duration=5.0,
        stages=[StageResult(name="test", exit_code=0, duration=1.0, status="passed")],
        test_results={"summary": {"total_tests": 10}},
        validation_results={"checks": {"pdf": True}},
        performance_metrics={"duration": 5.0},
        error_summary={"total_errors": 0},
        output_statistics={"pdf_files": 1}
    )
    assert report.timestamp == "2025-01-01T00:00:00"
    assert report.total_duration == 5.0
    assert len(report.stages) == 1
    assert report.test_results is not None
    assert report.validation_results is not None

