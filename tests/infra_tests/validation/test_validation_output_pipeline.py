"""Tests for infrastructure/validation/output/pipeline.py.

Covers validate_pdfs, validate_manuscript_output_markdown, verify_outputs_exist,
generate_validation_report, and execute_validation_pipeline.
Follows No Mocks Policy — real files and monkeypatch for repo-root isolation only.
"""

from __future__ import annotations

import json

from infrastructure.core.pipeline.artifacts import ArtifactManifest, ArtifactManifestEntry, compute_sha256
import infrastructure.validation.output.pipeline as mod
from infrastructure.validation.output.pipeline import (
    generate_validation_report,
    validate_manuscript_output_markdown,
    validate_pdfs,
    verify_outputs_exist,
)


def _minimal_structural_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\nstartxref\n0\n%%EOF\n"


class TestValidatePdfs:
    """Test validate_pdfs() with real file structures."""

    def test_returns_false_for_missing_pdf_dir(self) -> None:
        result = validate_pdfs("_nonexistent_project_xyz_abc")
        assert result is False

    def test_valid_pdfs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "section1.pdf").write_bytes(_minimal_structural_pdf())
        (pdf_dir / "section2.pdf").write_bytes(_minimal_structural_pdf())

        assert mod.validate_pdfs("test") is True

    def test_valid_pdfs_resolves_wip_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects_in_progress" / "draft" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "draft_combined.pdf").write_bytes(_minimal_structural_pdf())

        assert mod.validate_pdfs("draft") is True

    def test_no_pdf_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        assert mod.validate_pdfs("test") is False

    def test_empty_pdf_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        assert mod.validate_pdfs("test") is False

    def test_empty_pdf_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "empty.pdf").write_bytes(b"")
        assert mod.validate_pdfs("test") is False

    def test_mixed_valid_and_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "valid.pdf").write_bytes(_minimal_structural_pdf())
        (pdf_dir / "empty.pdf").write_bytes(b"")
        assert mod.validate_pdfs("test") is False


class TestValidateMarkdown:
    """Test validate_manuscript_output_markdown()."""

    def test_returns_true_for_missing_manuscript_dir(self) -> None:
        assert validate_manuscript_output_markdown("_nonexistent_project_xyz_abc") is True

    def test_no_manuscript_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        assert mod.validate_manuscript_output_markdown("test") is True

    def test_empty_manuscript_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)
        assert mod.validate_manuscript_output_markdown("test") is True

    def test_with_markdown_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Introduction\n\nHello world.")
        (ms_dir / "02_methods.md").write_text("# Methods\n\nWe did things.")
        (tmp_path / "projects" / "test" / "output").mkdir(parents=True)
        assert mod.validate_manuscript_output_markdown("test") is True

    def test_markdown_resolves_wip_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project = tmp_path / "projects_in_progress" / "draft"
        ms_dir = project / "manuscript"
        ms_dir.mkdir(parents=True)
        (project / "output").mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Introduction\n\nHello world.")
        assert mod.validate_manuscript_output_markdown("draft") is True

    def test_clean_markdown_clears_stale_diagnostics(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project = tmp_path / "projects" / "test"
        ms_dir = project / "manuscript"
        report_dir = project / "output" / "reports"
        ms_dir.mkdir(parents=True)
        report_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Introduction\n\nHello world.")
        stale = report_dir / "diagnostics.json"
        stale.write_text(
            '{"project_name":"test","total_events":1,"errors":0,"warnings":1,"events":[]}',
            encoding="utf-8",
        )
        assert mod.validate_manuscript_output_markdown("test") is True
        assert not stale.exists()


class TestVerifyOutputsExist:
    """Test verify_outputs_exist()."""

    def test_returns_tuple_for_nonexistent_project(self) -> None:
        result = verify_outputs_exist("_nonexistent_project_xyz_abc")
        assert isinstance(result, tuple)
        assert len(result) == 2
        valid, details = result
        assert isinstance(valid, bool)
        assert isinstance(details, dict)
        assert valid is False

    def test_valid_structure(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects" / "test" / "output"
        (output_dir / "pdf").mkdir(parents=True)
        (output_dir / "pdf" / "paper.pdf").write_bytes(b"%PDF content")

        structure_valid, details = mod.verify_outputs_exist("test")
        assert isinstance(structure_valid, bool)
        assert "structure" in details

    def test_empty_output(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects" / "test" / "output"
        output_dir.mkdir(parents=True)
        structure_valid, details = mod.verify_outputs_exist("test")
        assert isinstance(structure_valid, bool)

    def test_verify_outputs_resolves_wip_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects_in_progress" / "draft" / "output"
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "draft_combined.pdf").write_bytes(_minimal_structural_pdf())

        structure_valid, details = mod.verify_outputs_exist("draft")
        assert isinstance(structure_valid, bool)
        assert details["structure"]["directory_structure"]["combined_pdf"]["exists"] is True


def test_validate_project_design_includes_autoresearch_when_configured(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
    project = tmp_path / "projects" / "demo"
    (project / "output" / "reports").mkdir(parents=True)
    (project / "autoresearch.yaml").write_text(
        "strict: true\nquality_checks: [unknown_check]\n",
        encoding="utf-8",
    )
    pipeline_dir = tmp_path / "infrastructure" / "core" / "pipeline"
    pipeline_dir.mkdir(parents=True)
    (pipeline_dir / "pipeline.yaml").write_text(
        """
stages:
  - name: Output Validation
    script: 04_validate_output.py
    contract:
      output_artifacts: ["projects/{project}/output/reports/"]
      definition_of_done: "Report written."
      failure_code: "OUTPUT_VALIDATION_FAILED"
""",
        encoding="utf-8",
    )

    result, issues = mod.validate_project_design(project)

    assert result is False
    assert any("AUTORESEARCH.QUALITY_CHECK_UNKNOWN" in issue for issue in issues)
    assert (project / "output" / "reports" / "autoresearch_readiness.json").exists()


class TestGenerateValidationReport:
    """Test generate_validation_report()."""

    def test_generates_report_with_all_passing(self) -> None:
        check_results = [
            ("pdf_validation", True),
            ("markdown_validation", True),
            ("output_exists", True),
        ]
        report = generate_validation_report(
            check_results=check_results,
            figure_issues=[],
            output_statistics={"total_files": 5},
            project_name="_test_project",
        )
        assert report["summary"]["total_checks"] == 3
        assert report["summary"]["passed"] == 3
        assert report["summary"]["failed"] == 0
        assert report["summary"]["all_passed"] is True

    def test_empty_check_results(self) -> None:
        report = generate_validation_report(
            check_results=[],
            figure_issues=[],
            output_statistics={},
            project_name="_test_project",
        )
        assert report["summary"]["total_checks"] == 0
        assert report["summary"]["all_passed"] is True

    def test_all_passed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)
        checks = [
            ("PDF validation", True),
            ("Markdown validation", True),
            ("Output structure", True),
        ]
        result = generate_validation_report(checks, [], {}, project_name="test")
        assert result["summary"]["all_passed"] is True
        assert result["summary"]["passed"] == 3
        assert result["summary"]["failed"] == 0
        assert result["recommendations"] == []

    def test_pdf_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)
        checks = [("PDF validation", False), ("Markdown validation", True)]
        result = generate_validation_report(checks, [], {}, project_name="test")
        assert result["summary"]["failed"] == 1
        recs = result["recommendations"]
        assert any(r["priority"] == "high" and "PDF" in r["issue"] for r in recs)

    def test_markdown_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)
        result = generate_validation_report([("Markdown validation", False)], [], {}, project_name="test")
        recs = result["recommendations"]
        assert any(r["priority"] == "medium" for r in recs)

    def test_output_structure_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)
        result = generate_validation_report([("Output structure", False)], [], {}, project_name="test")
        recs = result["recommendations"]
        assert any(r["priority"] == "high" and "Missing" in r["issue"] for r in recs)

    def test_figure_issues(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)
        figure_issues = ["Missing figure: fig1.png", "Unregistered: fig2.png"]
        result = generate_validation_report([("PDF validation", True)], figure_issues, {}, project_name="test")
        assert result["summary"]["figure_issues_count"] == 2
        recs = result["recommendations"]
        assert any("figure" in r["issue"].lower() for r in recs)

    def test_with_output_statistics(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)
        stats = {"pdf": {"files": 3, "size_mb": 1.5}}
        result = generate_validation_report([("PDF validation", True)], [], stats, project_name="test")
        assert result["output_statistics"]["pdf"]["files"] == 3

    def test_report_contains_checks_dict(self) -> None:
        report = generate_validation_report(
            check_results=[("my_check", True)],
            figure_issues=[],
            output_statistics={},
            project_name="_test_project",
        )
        assert report["checks"]["my_check"] is True

    def test_report_contains_figure_issues(self) -> None:
        issues = ["fig1.png missing", "fig2.png wrong size"]
        report = generate_validation_report(
            check_results=[],
            figure_issues=issues,
            output_statistics={},
            project_name="_test_project",
        )
        assert report["figure_issues"] == issues

    def test_fallback_json_save(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)
        result = generate_validation_report([("PDF validation", True)], [], {}, project_name="test")
        assert "timestamp" in result
        assert "checks" in result
        assert "summary" in result


class TestExecuteValidationPipeline:
    """Test execute_validation_pipeline()."""

    def test_no_pdfs_no_manuscript(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project_dir = tmp_path / "projects" / "test"
        (project_dir / "output").mkdir(parents=True)
        result = mod.execute_validation_pipeline("test")
        assert isinstance(result, int)

    def test_with_valid_pdfs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF-1.4 content")
        ms_dir = project_dir / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Intro\n\nContent.")
        assert isinstance(mod.execute_validation_pipeline("test"), int)

    def test_with_figure_registry(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF content")
        fig_dir = project_dir / "output" / "figures"
        fig_dir.mkdir(parents=True)
        (fig_dir / "figure_registry.json").write_text(json.dumps({"figures": []}))
        ms_dir = project_dir / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Intro\n\nContent.")
        assert isinstance(mod.execute_validation_pipeline("test"), int)

    def test_with_output_subdirs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF content")
        fig_dir = project_dir / "output" / "figures"
        fig_dir.mkdir(parents=True)
        (fig_dir / "fig1.png").write_bytes(b"\x89PNG data")
        data_dir = project_dir / "output" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "results.csv").write_text("a,b\n1,2")
        ms_dir = project_dir / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Intro\n\nContent.")
        assert isinstance(mod.execute_validation_pipeline("test"), int)

    def test_prefers_current_project_manifest_over_stale_stage_snapshots(self, tmp_path):
        project_dir = tmp_path / "projects" / "test"
        artifact = project_dir / "output" / "data" / "result.json"
        artifact.parent.mkdir(parents=True)
        artifact.write_text('{"ok": true}\n')
        manifest_path = project_dir / "output" / "reports" / "artifact_manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest = ArtifactManifest(
            entries=(
                ArtifactManifestEntry(
                    path="output/data/result.json",
                    size_bytes=artifact.stat().st_size,
                    sha256=compute_sha256(artifact),
                    stage_num=1,
                    stage_name="project contract",
                    contract_match=True,
                ),
            )
        )
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
        stale_stage = project_dir / "output" / ".pipeline" / "artifacts" / "stage-99-stale.json"
        stale_stage.parent.mkdir(parents=True)
        stale_stage.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "path": "output/data/result.json",
                            "size_bytes": artifact.stat().st_size,
                            "sha256": "0" * 64,
                            "stage_num": 99,
                            "stage_name": "stale snapshot",
                            "contract_match": True,
                        }
                    ],
                    "issues": [],
                }
            ),
            encoding="utf-8",
        )

        selected = mod._current_project_manifest_if_valid(project_dir / "output", project_dir)

        assert selected is not None
        assert selected.entries[0].stage_name == "project contract"
