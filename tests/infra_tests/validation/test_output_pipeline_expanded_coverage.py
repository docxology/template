"""Tests for infrastructure.validation.output.pipeline — validate_pdfs and validate_markdown."""


import infrastructure.validation.output.pipeline as mod


class TestValidatePdfs:
    def test_valid_pdfs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "section1.pdf").write_bytes(b"%PDF-1.4 valid content here")
        (pdf_dir / "section2.pdf").write_bytes(b"%PDF-1.4 another valid pdf")

        result = mod.validate_pdfs("test")
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
        (pdf_dir / "valid.pdf").write_bytes(b"%PDF content")
        (pdf_dir / "empty.pdf").write_bytes(b"")

        result = mod.validate_pdfs("test")
        assert result is False


class TestValidateMarkdown:
    def test_no_manuscript_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        # No manuscript directory - should return True (graceful)
        result = mod.validate_markdown("test")
        assert result is True

    def test_empty_manuscript_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)
        # No markdown files
        result = mod.validate_markdown("test")
        assert result is True

    def test_with_markdown_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "01_intro.md").write_text("# Introduction\n\nHello world.")
        (ms_dir / "02_methods.md").write_text("# Methods\n\nWe did things.")
        # Also create the output dir for DiagnosticReporter
        (tmp_path / "projects" / "test" / "output").mkdir(parents=True)

        result = mod.validate_markdown("test")
        assert result is True
