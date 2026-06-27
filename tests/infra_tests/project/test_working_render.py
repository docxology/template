"""Tests for working-project batch render helpers."""

from __future__ import annotations

from pathlib import Path

import json
import os

from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.project.working_render import (
    ProjectAudit,
    _classify_filesystem_only,
    _combined_pdf_path,
    audit_project,
    check_structure,
    classify_status,
    consolidate_audits,
    failure_category,
    first_failure,
    has_manuscript,
    list_working_projects,
    merge_batch_log_status,
    parse_batch_log_results,
    pipeline_log_failure,
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


def test_has_manuscript_true_when_markdown_present(tmp_path: Path) -> None:
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript" / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    assert has_manuscript(tmp_path) is True


def test_has_manuscript_false_when_dir_missing_or_empty(tmp_path: Path) -> None:
    assert has_manuscript(tmp_path) is False
    (tmp_path / "manuscript").mkdir()
    assert has_manuscript(tmp_path) is False  # dir present but no *.md


def test_classify_filesystem_only_rubric() -> None:
    def audit(**kw: object) -> ProjectAudit:
        base = dict(name="p", status="", pipeline_success=False, duration_sec=0.0)
        base.update(kw)
        return ProjectAudit(**base)  # type: ignore[arg-type]

    assert _classify_filesystem_only(audit(top_pdf="/t.pdf", pdf_validation_ok=True)) == (
        "PASS — full top-level PDF",
        True,
    )
    assert _classify_filesystem_only(audit(top_pdf="/t.pdf")) == (
        "PARTIAL — PDF validation issues",
        False,
    )
    assert _classify_filesystem_only(audit(local_pdf="/l.pdf")) == (
        "PARTIAL — local PDF only",
        False,
    )
    assert _classify_filesystem_only(audit(status="PASS — pipeline")) == (
        "PARTIAL — pipeline passed; top PDF missing",
        False,
    )
    assert _classify_filesystem_only(
        audit(structure_ok=False, structure_notes=["missing tests/"])
    ) == ("FAIL — structure", False)
    assert _classify_filesystem_only(audit()) == ("FAIL — no PDF", False)


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


# ---------------------------------------------------------------------------
# list_working_projects — dotfile and symlink branches
# ---------------------------------------------------------------------------


def test_list_working_projects_skips_dotfiles(tmp_path: Path) -> None:
    """Entries whose names start with '.' must be excluded from the result."""
    working = tmp_path / "projects" / "working"
    working.mkdir(parents=True)
    (working / ".hidden_dir").mkdir()
    (working / "real_project").mkdir()
    result = list_working_projects(tmp_path)
    assert result == ["real_project"]
    assert ".hidden_dir" not in result


def test_list_working_projects_includes_symlinks(tmp_path: Path) -> None:
    """A symlink entry that is not a plain dir must still be included."""
    working = tmp_path / "projects" / "working"
    working.mkdir(parents=True)
    target = tmp_path / "actual_project"
    target.mkdir()
    link = working / "linked_project"
    link.symlink_to(target)
    result = list_working_projects(tmp_path)
    assert "linked_project" in result


# ---------------------------------------------------------------------------
# check_structure — missing both tests/ and manuscript/, and missing only manuscript/
# ---------------------------------------------------------------------------


def test_check_structure_fails_when_both_markers_missing(tmp_path: Path) -> None:
    """ok must be False when both tests/ and manuscript/ are absent."""
    project = tmp_path / "wip"
    project.mkdir()
    ok, notes = check_structure(project)
    assert ok is False
    assert "missing tests/" in notes
    assert "missing manuscript/" in notes


def test_check_structure_fails_when_only_manuscript_missing(tmp_path: Path) -> None:
    """ok must be False when only manuscript/ is absent (tests/ and src/ present)."""
    project = tmp_path / "wip"
    project.mkdir()
    (project / "tests").mkdir()
    (project / "src").mkdir()
    ok, notes = check_structure(project)
    assert ok is False
    assert "missing manuscript/" in notes
    assert "missing tests/" not in notes


# ---------------------------------------------------------------------------
# classify_status — FAIL structure, FAIL pipeline, PARTIAL PDF validation
# ---------------------------------------------------------------------------


def test_classify_status_fail_structure(tmp_path: Path) -> None:
    """structure_ok=False must always produce FAIL — structure."""
    status = classify_status(
        pipeline_success=True,
        top_pdf=None,
        local_pdf=None,
        structure_ok=False,
        pdf_validation_ok=None,
    )
    assert status == "FAIL — structure"


def test_classify_status_fail_pipeline_no_pdfs(tmp_path: Path) -> None:
    """No PDFs and pipeline_success=False must produce FAIL — pipeline."""
    status = classify_status(
        pipeline_success=False,
        top_pdf=None,
        local_pdf=None,
        structure_ok=True,
        pdf_validation_ok=None,
    )
    assert status == "FAIL — pipeline"


def test_classify_status_partial_pdf_validation_issues(tmp_path: Path) -> None:
    """pipeline_success=True, top_pdf present, but pdf_validation_ok=False -> PARTIAL."""
    pdf = tmp_path / "demo_combined.pdf"
    pdf.write_bytes(b"%PDF-1.4 stub")
    status = classify_status(
        pipeline_success=True,
        top_pdf=pdf,
        local_pdf=None,
        structure_ok=True,
        pdf_validation_ok=False,
    )
    assert status == "PARTIAL — PDF validation issues"


# ---------------------------------------------------------------------------
# failure_category — None, 'analysis', 'copy/valid', and unrecognized fallback
# ---------------------------------------------------------------------------


def test_failure_category_none_returns_pipeline() -> None:
    """None input must map to the 'pipeline' category."""
    assert failure_category(None) == "pipeline"


def test_failure_category_analysis_keyword() -> None:
    """Stage names containing 'analysis' map to 'analysis'."""
    assert failure_category("Run Analysis") == "analysis"
    assert failure_category("ANALYSIS step") == "analysis"


def test_failure_category_copy_and_valid_keywords() -> None:
    """Stage names containing 'copy' or 'valid' map to 'copy/validate'."""
    assert failure_category("Copy Outputs") == "copy/validate"
    assert failure_category("Output Validation") == "copy/validate"


def test_failure_category_unrecognized_falls_back_to_pipeline() -> None:
    """An unrecognized stage name must fall through to the 'pipeline' default."""
    assert failure_category("Obscure Stage XYZ") == "pipeline"


# ---------------------------------------------------------------------------
# pipeline_log_failure — None path, missing file, no match, happy path
# ---------------------------------------------------------------------------


def test_pipeline_log_failure_none_path() -> None:
    """A None log_path must return (None, None) immediately."""
    assert pipeline_log_failure(None) == (None, None)


def test_pipeline_log_failure_file_does_not_exist(tmp_path: Path) -> None:
    """A path to a non-existent log file must return (None, None)."""
    assert pipeline_log_failure(tmp_path / "nope.log") == (None, None)


def test_pipeline_log_failure_no_match_returns_none(tmp_path: Path) -> None:
    """A log file with no PIPELINE_STAGE_FAILED pattern must return (None, None)."""
    log = tmp_path / "pipeline.log"
    log.write_text("All good\nStage 1 done\n", encoding="utf-8")
    assert pipeline_log_failure(log) == (None, None)


def test_pipeline_log_failure_extracts_stage_from_matching_line(tmp_path: Path) -> None:
    """A log with the matching pattern must return the extracted stage number and name."""
    log = tmp_path / "pipeline.log"
    log.write_text(
        "Pipeline failed at stage 3: Project Tests\nsome other line\n",
        encoding="utf-8",
    )
    num, name = pipeline_log_failure(log)
    assert num == 3
    assert name == "Project Tests"


# ---------------------------------------------------------------------------
# parse_batch_log_results — non-existent file, header + Result lines, path splitting
# ---------------------------------------------------------------------------


def test_parse_batch_log_results_nonexistent_file(tmp_path: Path) -> None:
    """A non-existent log file must return an empty dict."""
    assert parse_batch_log_results(tmp_path / "no.log") == {}


def test_parse_batch_log_results_parses_result_lines(tmp_path: Path) -> None:
    """Header and Result lines must be parsed into a project-name → status dict."""
    log = tmp_path / "batch.log"
    log.write_text(
        "=== [1/2] alpha (run)\nResult: PASS — full top-level PDF (12.3s)\n"
        "=== [2/2] beta (run)\nResult: FAIL — pipeline (0.5s)\n",
        encoding="utf-8",
    )
    result = parse_batch_log_results(log)
    assert result["alpha"] == "PASS — full top-level PDF"
    assert result["beta"] == "FAIL — pipeline"


def test_parse_batch_log_results_strips_path_component(tmp_path: Path) -> None:
    """Header lines with a '/' in the project part should use the last component."""
    log = tmp_path / "batch.log"
    log.write_text(
        "=== [1/1] working/myproject (run)\nResult: PARTIAL — local PDF only (3.1s)\n",
        encoding="utf-8",
    )
    result = parse_batch_log_results(log)
    assert "myproject" in result
    assert result["myproject"] == "PARTIAL — local PDF only"


# ---------------------------------------------------------------------------
# merge_batch_log_status — primary=None, resume logs
# ---------------------------------------------------------------------------


def test_merge_batch_log_status_no_primary_no_resume(tmp_path: Path) -> None:
    """With no primary log and no resume logs under output/, result is empty."""
    assert merge_batch_log_status(tmp_path, None) == {}


def test_merge_batch_log_status_merges_resume_logs(tmp_path: Path) -> None:
    """Resume logs present under output/ must be merged into the result."""
    output = tmp_path / "output"
    output.mkdir()
    resume_log = output / "_working_render_resume_small.log"
    resume_log.write_text(
        "=== [1/1] alpha (run)\nResult: PASS — full top-level PDF (5.0s)\n",
        encoding="utf-8",
    )
    result = merge_batch_log_status(tmp_path, None)
    assert result.get("alpha") == "PASS — full top-level PDF"


# ---------------------------------------------------------------------------
# consolidate_audits — override path and log_status branch
# ---------------------------------------------------------------------------


def test_consolidate_audits_uses_override_directly(tmp_path: Path) -> None:
    """A project listed in overrides must appear in the result unchanged."""
    working = tmp_path / "projects" / "working"
    working.mkdir(parents=True)
    (working / "alpha").mkdir()
    # Give it minimum structure so it gets discovered
    override_audit = ProjectAudit(
        name="alpha",
        status="PASS — override",
        pipeline_success=True,
        duration_sec=1.0,
    )
    audits = consolidate_audits(tmp_path, None, overrides={"alpha": override_audit})
    alpha = next(a for a in audits if a.name == "alpha")
    assert alpha.status == "PASS — override"


def test_consolidate_audits_log_status_updates_audit(tmp_path: Path) -> None:
    """When a log entry exists for a project, audit.status and pipeline_success are updated."""
    working = tmp_path / "projects" / "working"
    working.mkdir(parents=True)
    (working / "beta").mkdir()

    output = tmp_path / "output"
    output.mkdir()
    log = output / "_working_render_resume_small.log"
    log.write_text(
        "=== [1/1] beta (run)\nResult: PASS — full top-level PDF (7.2s)\n",
        encoding="utf-8",
    )
    # No real top PDF on disk, so the stale-PASS guard will downgrade to PARTIAL
    audits = consolidate_audits(tmp_path, None)
    beta = next(a for a in audits if a.name == "beta")
    # status must have been touched by the log path (PASS then downgraded due to no PDF)
    assert "PARTIAL" in beta.status or "PASS" in beta.status  # log entry was applied


# ---------------------------------------------------------------------------
# audit_project — empty results and failing stage propagation
# ---------------------------------------------------------------------------


def test_audit_project_empty_results_gives_fail(tmp_path: Path) -> None:
    """Empty results list must yield pipeline_success=False."""
    working = tmp_path / "projects" / "working"
    working.mkdir(parents=True)
    proj = working / "proj_a"
    proj.mkdir()
    (proj / "tests").mkdir()
    (proj / "manuscript").mkdir()

    audit = audit_project(tmp_path, "proj_a", results=[], duration_sec=0.5)
    assert audit.pipeline_success is False


def test_audit_project_failing_stage_propagates(tmp_path: Path) -> None:
    """A failed stage result must populate failing_stage and failing_stage_num."""
    working = tmp_path / "projects" / "working"
    working.mkdir(parents=True)
    proj = working / "proj_b"
    proj.mkdir()
    (proj / "tests").mkdir()
    (proj / "manuscript").mkdir()

    results = [
        PipelineStageResult(
            stage_num=3,
            stage_name="Project Tests",
            success=False,
            duration=2.0,
            exit_code=1,
            error_message="coverage too low",
        )
    ]
    audit = audit_project(tmp_path, "proj_b", results=results, duration_sec=2.0)
    assert audit.failing_stage == "Project Tests"
    assert audit.failing_stage_num == 3


# ---------------------------------------------------------------------------
# write_audit_report — log_path entries and pass/partial/fail counts
# ---------------------------------------------------------------------------


def test_write_audit_report_log_path_in_markdown(tmp_path: Path) -> None:
    """Audits with a log_path must appear in the '## Log pointers' section."""
    audits = [
        ProjectAudit(
            name="has_log",
            status="FAIL — pipeline",
            pipeline_success=False,
            duration_sec=1.0,
            log_path="/some/path/pipeline.log",
        ),
        ProjectAudit(
            name="no_log",
            status="PASS — full top-level PDF",
            pipeline_success=True,
            duration_sec=2.0,
        ),
    ]
    _, md_path = write_audit_report(tmp_path, audits)
    content = md_path.read_text(encoding="utf-8")
    assert "has_log" in content
    assert "/some/path/pipeline.log" in content
    # no_log has no log_path, so it must NOT appear under Log pointers
    assert "no_log" not in content.split("## Log pointers")[1]


def test_write_audit_report_counts_in_json(tmp_path: Path) -> None:
    """JSON payload must tally pass_count, partial_count, and fail_count correctly."""
    audits = [
        ProjectAudit(name="p1", status="PASS — full top-level PDF", pipeline_success=True, duration_sec=1.0),
        ProjectAudit(name="p2", status="PARTIAL — local PDF only", pipeline_success=False, duration_sec=2.0),
        ProjectAudit(name="p3", status="PARTIAL — PDF validation issues", pipeline_success=True, duration_sec=1.5),
        ProjectAudit(name="p4", status="FAIL — pipeline", pipeline_success=False, duration_sec=0.5),
        ProjectAudit(name="p5", status="FAIL — structure", pipeline_success=False, duration_sec=0.1),
    ]
    json_path, _ = write_audit_report(tmp_path, audits)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["pass_count"] == 1
    assert data["partial_count"] == 2
    assert data["fail_count"] == 2
    assert data["project_count"] == 5
