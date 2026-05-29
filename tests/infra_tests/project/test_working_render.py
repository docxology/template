"""Tests for working-project batch render helpers."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.project.working_render import (
    ProjectAudit,
    _combined_pdf_path,
    check_structure,
    classify_status,
    failure_category,
    first_failure,
    list_working_projects,
    stage_summaries,
    write_audit_report,
)


def test_classify_status_pass_with_top_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "demo_combined.pdf"
    pdf.write_bytes(b"%PDF-1.4 minimal")
    status = classify_status(
        pipeline_success=True,
        top_pdf=pdf,
        local_pdf=None,
        structure_ok=True,
        pdf_validation_ok=True,
    )
    assert status == "PASS — full top-level PDF"


def test_classify_status_partial_local_only(tmp_path: Path) -> None:
    local = tmp_path / "local_combined.pdf"
    local.write_bytes(b"%PDF-1.4 minimal")
    status = classify_status(
        pipeline_success=False,
        top_pdf=None,
        local_pdf=local,
        structure_ok=True,
        pdf_validation_ok=None,
    )
    assert status == "PARTIAL — local PDF only"


def test_check_structure_requires_tests_and_manuscript(tmp_path: Path) -> None:
    project = tmp_path / "wip"
    project.mkdir()
    (project / "tests").mkdir()
    (project / "manuscript").mkdir()
    ok, notes = check_structure(project)
    assert ok is True
    assert notes == ["missing src/"]


def test_combined_pdf_path_uses_shared_locator(tmp_path: Path) -> None:
    name = "demo"
    output_dir = tmp_path / "output" / name
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "demo_combined.pdf").write_bytes(b"%PDF-demo")

    found = _combined_pdf_path(output_dir, name)
    assert found == pdf_dir / "demo_combined.pdf"


def test_first_failure_returns_first_bad_stage() -> None:
    results = [
        PipelineStageResult(
            stage_num=1,
            stage_name="Setup",
            success=True,
            duration=0.1,
            exit_code=0,
            error_message="",
        ),
        PipelineStageResult(
            stage_num=2,
            stage_name="Project Tests",
            success=False,
            duration=1.0,
            exit_code=1,
            error_message="cov fail",
        ),
    ]
    num, name, msg = first_failure(results)
    assert num == 2
    assert name == "Project Tests"
    assert msg == "cov fail"


def test_failure_category_maps_tests() -> None:
    assert failure_category("Project Tests") == "tests"
    assert failure_category("PDF Rendering") == "render"


def test_stage_summaries_serializes_results() -> None:
    results = [
        PipelineStageResult(
            stage_num=1,
            stage_name="Setup",
            success=True,
            duration=1.234,
            exit_code=0,
            error_message="",
        ),
    ]
    rows = stage_summaries(results)
    assert rows[0]["stage_name"] == "Setup"
    assert rows[0]["duration_sec"] == 1.23


def test_write_audit_report_writes_json_and_markdown(tmp_path: Path) -> None:
    audits = [
        ProjectAudit(
            name="demo",
            status="PASS — full top-level PDF",
            pipeline_success=True,
            duration_sec=12.3,
            top_pdf="/tmp/demo_combined.pdf",
        ),
    ]
    json_path, md_path = write_audit_report(tmp_path, audits)
    assert json_path.exists()
    assert md_path.exists()
    assert "demo" in md_path.read_text(encoding="utf-8")


def test_list_working_projects_empty_when_missing(tmp_path: Path) -> None:
    assert list_working_projects(tmp_path) == []
