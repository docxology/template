"""Tests for infrastructure/validation/output/pipeline.py.

Covers: generate_validation_report, verify_outputs_exist,
execute_validation_pipeline, and edge cases.

No mocks used -- all tests use real files and data structures.
"""

from __future__ import annotations


import infrastructure.validation.output.pipeline as mod


class TestGenerateValidationReport:
    """Test generate_validation_report."""

    def test_all_passed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects" / "test" / "output" / "reports"
        output_dir.mkdir(parents=True)

        check_results = [
            ("PDF validation", True),
            ("Markdown validation", True),
            ("Output structure", True),
        ]
        result = mod.generate_validation_report(
            check_results, [], {}, "test"
        )
        assert result["summary"]["all_passed"] is True
        assert result["summary"]["failed"] == 0

    def test_pdf_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects" / "test" / "output" / "reports"
        output_dir.mkdir(parents=True)

        check_results = [
            ("PDF validation", False),
            ("Markdown validation", True),
        ]
        result = mod.generate_validation_report(
            check_results, [], {}, "test"
        )
        assert result["summary"]["failed"] == 1
        assert len(result["recommendations"]) > 0
        assert result["recommendations"][0]["priority"] == "high"

    def test_markdown_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects" / "test" / "output" / "reports"
        output_dir.mkdir(parents=True)

        check_results = [("Markdown validation", False)]
        result = mod.generate_validation_report(
            check_results, [], {}, "test"
        )
        assert len(result["recommendations"]) > 0
        assert result["recommendations"][0]["priority"] == "medium"

    def test_output_structure_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects" / "test" / "output" / "reports"
        output_dir.mkdir(parents=True)

        check_results = [("Output structure", False)]
        result = mod.generate_validation_report(
            check_results, [], {}, "test"
        )
        assert len(result["recommendations"]) > 0
        assert result["recommendations"][0]["priority"] == "high"

    def test_figure_issues(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects" / "test" / "output" / "reports"
        output_dir.mkdir(parents=True)

        check_results = [("PDF validation", True)]
        figure_issues = ["Missing figure: fig1.png", "Unused figure: fig2.png"]
        result = mod.generate_validation_report(
            check_results, figure_issues, {}, "test"
        )
        assert result["summary"]["figure_issues_count"] == 2
        assert len(result["recommendations"]) > 0

    def test_with_output_statistics(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        output_dir = tmp_path / "projects" / "test" / "output" / "reports"
        output_dir.mkdir(parents=True)

        stats = {"pdf": {"files": 3, "size_mb": 1.5}}
        result = mod.generate_validation_report(
            [("PDF validation", True)], [], stats, "test"
        )
        assert result["output_statistics"]["pdf"]["files"] == 3


class TestVerifyOutputsExist:
    """Test verify_outputs_exist."""

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


class TestExecuteValidationPipeline:
    """Test execute_validation_pipeline."""

    def test_no_pdfs_no_manuscript(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        # Create minimal project structure
        project_dir = tmp_path / "projects" / "test"
        (project_dir / "output").mkdir(parents=True)

        result = mod.execute_validation_pipeline("test")
        # Should complete with some result
        assert isinstance(result, int)

    def test_with_valid_pdfs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF-1.4 content")
        # Create manuscript dir
        ms_dir = project_dir / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Intro\n\nContent.")

        result = mod.execute_validation_pipeline("test")
        assert isinstance(result, int)

    def test_with_figure_registry(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF content")
        # Create figure registry
        fig_dir = project_dir / "output" / "figures"
        fig_dir.mkdir(parents=True)
        import json
        (fig_dir / "figure_registry.json").write_text(json.dumps({"figures": []}))
        # Create manuscript dir
        ms_dir = project_dir / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Intro\n\nContent.")

        result = mod.execute_validation_pipeline("test")
        assert isinstance(result, int)

    def test_with_output_subdirs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF content")
        # Create figures and data dirs with files
        fig_dir = project_dir / "output" / "figures"
        fig_dir.mkdir(parents=True)
        (fig_dir / "fig1.png").write_bytes(b"\x89PNG data")
        data_dir = project_dir / "output" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "results.csv").write_text("a,b\n1,2")
        # Manuscript
        ms_dir = project_dir / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Intro\n\nContent.")

        result = mod.execute_validation_pipeline("test")
        assert isinstance(result, int)
