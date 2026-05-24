"""Tests for infrastructure.validation.output.pipeline — validate_pdfs and validate_manuscript_output_markdown."""


import infrastructure.validation.output.pipeline as mod


def _minimal_structural_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\nstartxref\n0\n%%EOF\n"


class TestValidatePdfs:
    def test_valid_pdfs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "section1.pdf").write_bytes(_minimal_structural_pdf())
        (pdf_dir / "section2.pdf").write_bytes(_minimal_structural_pdf())

        result = mod.validate_pdfs("test")
        assert result is True

    def test_valid_pdfs_resolves_wip_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects_in_progress" / "draft" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "draft_combined.pdf").write_bytes(_minimal_structural_pdf())

        result = mod.validate_pdfs("draft")
        assert result is True

    def test_no_pdf_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        # Don't create the pdf dir
        result = mod.validate_pdfs("test")
        assert result is False

    def test_empty_pdf_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        # No PDF files
        result = mod.validate_pdfs("test")
        assert result is False

    def test_empty_pdf_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "empty.pdf").write_bytes(b"")

        result = mod.validate_pdfs("test")
        assert result is False

    def test_mixed_valid_and_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "valid.pdf").write_bytes(_minimal_structural_pdf())
        (pdf_dir / "empty.pdf").write_bytes(b"")

        result = mod.validate_pdfs("test")
        assert result is False


class TestValidateMarkdown:
    def test_no_manuscript_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        # No manuscript directory - should return True (graceful)
        result = mod.validate_manuscript_output_markdown("test")
        assert result is True

    def test_empty_manuscript_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)
        # No markdown files
        result = mod.validate_manuscript_output_markdown("test")
        assert result is True

    def test_with_markdown_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Introduction\n\nHello world.")
        (ms_dir / "02_methods.md").write_text("# Methods\n\nWe did things.")
        # Also create the output dir for DiagnosticReporter
        (tmp_path / "projects" / "test" / "output").mkdir(parents=True)

        result = mod.validate_manuscript_output_markdown("test")
        assert result is True

    def test_markdown_resolves_wip_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        project = tmp_path / "projects_in_progress" / "draft"
        ms_dir = project / "manuscript"
        ms_dir.mkdir(parents=True)
        (project / "output").mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Introduction\n\nHello world.")

        result = mod.validate_manuscript_output_markdown("draft")
        assert result is True

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

        result = mod.validate_manuscript_output_markdown("test")

        assert result is True
        assert not stale.exists()
