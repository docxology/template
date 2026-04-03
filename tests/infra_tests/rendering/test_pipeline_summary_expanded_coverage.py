"""Tests for infrastructure.rendering._pipeline_summary — expanded coverage."""


from infrastructure.rendering._pipeline_summary import (
    _check_citations_used,
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
)


class TestCheckCitationsUsed:
    def test_no_citations(self, tmp_path):
        (tmp_path / "intro.md").write_text("# Introduction\n\nNo citations here.")
        assert _check_citations_used(tmp_path) is False

    def test_cite_command(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"As shown in \cite{smith2020}.")
        assert _check_citations_used(tmp_path) is True

    def test_citep_command(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"Results \citep{jones2021} indicate.")
        assert _check_citations_used(tmp_path) is True

    def test_citet_command(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"\citet{doe2022} showed that.")
        assert _check_citations_used(tmp_path) is True

    def test_citeauthor_command(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"\citeauthor{lee2019} found.")
        assert _check_citations_used(tmp_path) is True

    def test_citeyear_command(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"In \citeyear{wang2018}.")
        assert _check_citations_used(tmp_path) is True

    def test_at_citation(self, tmp_path):
        (tmp_path / "paper.md").write_text("See @smith2020 for details.")
        assert _check_citations_used(tmp_path) is True

    def test_supplemental_dir(self, tmp_path):
        sup = tmp_path / "supplemental"
        sup.mkdir()
        (tmp_path / "main.md").write_text("No citations.")
        (sup / "S01.md").write_text(r"See \cite{ref2020} for details.")
        assert _check_citations_used(tmp_path) is True

    def test_empty_dir(self, tmp_path):
        assert _check_citations_used(tmp_path) is False

    def test_unreadable_file(self, tmp_path):
        # Write a file with invalid encoding bytes
        (tmp_path / "bad.md").write_bytes(b"\x80\x81\x82 not utf8")
        # Should not crash, returns False gracefully
        result = _check_citations_used(tmp_path)
        # Might be True or False depending on encoding fallback, just shouldn't crash
        assert isinstance(result, bool)


class TestGenerateRenderingSummary:
    def test_empty_project(self, tmp_path, monkeypatch):
        import infrastructure.rendering._pipeline_summary as mod
        monkeypatch.setattr(mod, "__file__", str(tmp_path / "infrastructure" / "rendering" / "_pipeline_summary.py"))
        # Need to make the repo_root resolution work
        # repo_root = Path(__file__).parent.parent.parent → tmp_path
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        proj = tmp_path / "projects" / "test" / "output"
        proj.mkdir(parents=True)

        # Monkeypatch the module's __file__ so repo_root resolves to tmp_path
        result = generate_rendering_summary("test")
        assert result["project"] == "test"
        assert result["individual_pdfs"] == []
        assert result["combined_pdf"] is None

    def test_with_pdfs(self, tmp_path, monkeypatch):
        import infrastructure.rendering._pipeline_summary as mod
        # Create the directory structure
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        fake_file = infra_dir / "_pipeline_summary.py"
        fake_file.write_text("")
        monkeypatch.setattr(mod, "__file__", str(fake_file))

        pdf_dir = tmp_path / "projects" / "myproj" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "section1.pdf").write_bytes(b"A" * 2048)
        (pdf_dir / "myproj_combined.pdf").write_bytes(b"B" * 4096)

        result = generate_rendering_summary("myproj")
        assert len(result["individual_pdfs"]) == 1
        assert result["combined_pdf"] is not None
        assert result["total_size_kb"] > 0


class TestLogRenderingSummary:
    def test_full_summary(self):
        summary = {
            "project": "test",
            "individual_pdfs": [{"name": "s1.pdf", "size_kb": 100.0}],
            "combined_pdf": {"name": "combined.pdf", "size_kb": 500.0, "path": "/tmp/combined.pdf"},
            "combined_html": {"name": "index.html", "size_kb": 50.0, "path": "/tmp/index.html"},
            "web_outputs": [{"name": "page.html", "size_kb": 20.0}],
            "slides": [{"name": "talk.pdf", "size_kb": 200.0}],
            "total_size_kb": 870.0,
        }
        # Should not raise
        log_rendering_summary(summary)

    def test_minimal_summary(self):
        summary = {
            "project": "test",
            "individual_pdfs": [],
            "combined_pdf": None,
            "combined_html": None,
            "web_outputs": [],
            "slides": [],
            "total_size_kb": 0,
        }
        log_rendering_summary(summary)


class TestVerifyPdfOutputs:
    def test_no_pdf_dir(self, tmp_path, monkeypatch):
        import infrastructure.rendering._pipeline_summary as mod
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        fake_file = infra_dir / "_pipeline_summary.py"
        fake_file.write_text("")
        monkeypatch.setattr(mod, "__file__", str(fake_file))

        result = verify_pdf_outputs("test")
        assert result is False

    def test_no_pdf_files(self, tmp_path, monkeypatch):
        import infrastructure.rendering._pipeline_summary as mod
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        fake_file = infra_dir / "_pipeline_summary.py"
        fake_file.write_text("")
        monkeypatch.setattr(mod, "__file__", str(fake_file))

        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)

        result = verify_pdf_outputs("test")
        assert result is False

    def test_valid_combined_pdf(self, tmp_path, monkeypatch):
        import infrastructure.rendering._pipeline_summary as mod
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        fake_file = infra_dir / "_pipeline_summary.py"
        fake_file.write_text("")
        monkeypatch.setattr(mod, "__file__", str(fake_file))

        pdf_dir = tmp_path / "projects" / "myproj" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        ms_dir = tmp_path / "projects" / "myproj" / "manuscript"
        ms_dir.mkdir(parents=True)

        # Create valid combined PDF (> 0.01 MB = 10240 bytes)
        (pdf_dir / "myproj_combined.pdf").write_bytes(b"A" * 15000)
        (pdf_dir / "section1.pdf").write_bytes(b"B" * 15000)

        result = verify_pdf_outputs("myproj")
        assert result is True

    def test_failed_compilation(self, tmp_path, monkeypatch):
        import infrastructure.rendering._pipeline_summary as mod
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        fake_file = infra_dir / "_pipeline_summary.py"
        fake_file.write_text("")
        monkeypatch.setattr(mod, "__file__", str(fake_file))

        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)

        # Tiny PDF (< 0.1 KB = failed compilation)
        (pdf_dir / "test_combined.pdf").write_bytes(b"A" * 15000)
        (pdf_dir / "section.pdf").write_bytes(b"X")  # Failed compilation

        result = verify_pdf_outputs("test")
        assert result is False

    def test_no_combined_pdf(self, tmp_path, monkeypatch):
        import infrastructure.rendering._pipeline_summary as mod
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        fake_file = infra_dir / "_pipeline_summary.py"
        fake_file.write_text("")
        monkeypatch.setattr(mod, "__file__", str(fake_file))

        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)

        (pdf_dir / "section1.pdf").write_bytes(b"A" * 15000)
        # No combined PDF

        result = verify_pdf_outputs("test")
        assert result is False

    def test_with_bib_file(self, tmp_path, monkeypatch):
        import infrastructure.rendering._pipeline_summary as mod
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        fake_file = infra_dir / "_pipeline_summary.py"
        fake_file.write_text("")
        monkeypatch.setattr(mod, "__file__", str(fake_file))

        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)
        (ms_dir / "references.bib").write_text("@article{ref, title={T}}")

        (pdf_dir / "test_combined.pdf").write_bytes(b"A" * 15000)

        result = verify_pdf_outputs("test")
        assert result is True

    def test_small_but_not_failed_pdf(self, tmp_path, monkeypatch):
        """PDF > 0.1 KB but < 0.01 MB - warning, not failure."""
        import infrastructure.rendering._pipeline_summary as mod
        infra_dir = tmp_path / "infrastructure" / "rendering"
        infra_dir.mkdir(parents=True)
        fake_file = infra_dir / "_pipeline_summary.py"
        fake_file.write_text("")
        monkeypatch.setattr(mod, "__file__", str(fake_file))

        pdf_dir = tmp_path / "projects" / "test" / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        ms_dir = tmp_path / "projects" / "test" / "manuscript"
        ms_dir.mkdir(parents=True)

        # Combined PDF is valid
        (pdf_dir / "test_combined.pdf").write_bytes(b"A" * 15000)
        # Section PDF is small but not tiny (100 < x < 10240 bytes)
        (pdf_dir / "section.pdf").write_bytes(b"B" * 500)

        result = verify_pdf_outputs("test")
        # valid_pdfs = 1 (combined), failed = 0, so True
        assert result is True
