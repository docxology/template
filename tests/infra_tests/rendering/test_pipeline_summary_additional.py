"""Additional tests for infrastructure/rendering/_pipeline_summary.py.

Targets the branches below the 60% gate: warning aggregation, skipped
outputs, empty-stage summaries, strict LaTeX warning policy, and
verify_pdf_outputs with real PDFs and real directory structures.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from infrastructure.rendering._pipeline_summary import (
    _latex_log_files,
    _manuscript_dir_for_verify,
    _strict_latex_warning_policy_enabled,
    _verify_latex_warning_policy,
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
)


def _make_pdf(path: Path, pages: int = 1, text: str = "test") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    for i in range(pages):
        # Write enough text per page to produce a file above the 0.01 MB
        # (10.24 KB) threshold used by verify_pdf_outputs
        for j in range(500):
            pdf.drawString(72, 720 - j, f"{text} p{i+1} L{j} " * 5)
        pdf.showPage()
    pdf.save()


def _make_valid_combined_pdf(path: Path, text: str = "combined manuscript") -> None:
    """Create a PDF large enough to pass the >0.01 MB size check in verify_pdf_outputs."""
    _make_pdf(path, pages=12, text=text)


class TestStrictLatexWarningPolicy:
    """Test the opt-in strict LaTeX warning policy branches."""

    def test_policy_disabled_by_default(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text("rendering: {}\n", encoding="utf-8")
        assert _strict_latex_warning_policy_enabled(tmp_path, manuscript) is False

    def test_policy_enabled_in_source_config(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "docs" / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "config.yaml").write_text(
            "rendering:\n  fail_on_latex_warnings: true\n",
            encoding="utf-8",
        )
        assert _strict_latex_warning_policy_enabled(tmp_path, manuscript) is True

    def test_policy_enabled_in_injected_config(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "docs" / "manuscript"
        injected = tmp_path / "output" / "manuscript"
        manuscript.mkdir(parents=True)
        injected.mkdir(parents=True)
        (manuscript / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
        (injected / "config.yaml").write_text(
            "rendering:\n  fail_on_latex_warnings: true\n",
            encoding="utf-8",
        )
        (injected / "01_intro.md").write_text("# Injected\n", encoding="utf-8")
        assert _strict_latex_warning_policy_enabled(tmp_path, injected) is True

    def test_policy_malformed_yaml_is_ignored(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            "rendering: [invalid\n",
            encoding="utf-8",
        )
        assert _strict_latex_warning_policy_enabled(tmp_path, manuscript) is False

    def test_policy_non_dict_rendering_is_ignored(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            "rendering: \"not a dict\"\n",
            encoding="utf-8",
        )
        assert _strict_latex_warning_policy_enabled(tmp_path, manuscript) is False

    def test_policy_non_dict_config_is_ignored(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            "- list\n- not a dict\n",
            encoding="utf-8",
        )
        assert _strict_latex_warning_policy_enabled(tmp_path, manuscript) is False

    def test_policy_missing_config_file(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        assert _strict_latex_warning_policy_enabled(tmp_path, manuscript) is False

    def test_verify_policy_passes_when_disabled(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        assert _verify_latex_warning_policy(tmp_path, manuscript) is True

    def test_verify_policy_fails_when_no_logs(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            "rendering:\n  fail_on_latex_warnings: true\n",
            encoding="utf-8",
        )
        assert _verify_latex_warning_policy(tmp_path, manuscript) is False

    def test_verify_policy_passes_with_clean_logs(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            "rendering:\n  fail_on_latex_warnings: true\n",
            encoding="utf-8",
        )
        pdf_dir = tmp_path / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "_combined_manuscript.log").write_text(
            "This is pdfTeX, Version 3.141592653\nOutput written on combined.pdf\n",
            encoding="utf-8",
        )
        assert _verify_latex_warning_policy(tmp_path, manuscript) is True

    def test_verify_policy_fails_with_warnings_in_log(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            "rendering:\n  fail_on_latex_warnings: true\n",
            encoding="utf-8",
        )
        pdf_dir = tmp_path / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "_combined_manuscript.log").write_text(
            "LaTeX Warning: Reference `fig:missing' on page 1 undefined\n",
            encoding="utf-8",
        )
        assert _verify_latex_warning_policy(tmp_path, manuscript) is False

    def test_latex_log_files_finds_slide_logs(self, tmp_path: Path) -> None:
        pdf_dir = tmp_path / "output" / "pdf"
        slides_dir = tmp_path / "output" / "slides"
        pdf_dir.mkdir(parents=True)
        slides_dir.mkdir(parents=True)
        pdf_log = pdf_dir / "_combined_manuscript.log"
        slide_log1 = slides_dir / "intro_slides.log"
        slide_log2 = slides_dir / "results_slides.log"
        for p in [pdf_log, slide_log1, slide_log2]:
            p.write_text("log content\n", encoding="utf-8")
        logs = _latex_log_files(tmp_path)
        assert pdf_log in logs
        assert slide_log1 in logs
        assert slide_log2 in logs

    def test_latex_log_files_empty_when_no_logs(self, tmp_path: Path) -> None:
        assert _latex_log_files(tmp_path) == []


class TestGenerateRenderingSummaryWithRealFiles:
    """Test generate_rendering_summary with real output directory structures."""

    def test_summary_with_real_pdfs(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        output = project_root / "output"
        pdf_dir = output / "pdf"
        pdf_dir.mkdir(parents=True)
        _make_pdf(pdf_dir / "test_proj_combined.pdf", text="combined")
        _make_pdf(pdf_dir / "01_intro.pdf", text="intro")

        summary = generate_rendering_summary("templates/test_proj", repo_root=tmp_path)

        assert summary["combined_pdf"] is not None
        assert summary["combined_pdf"]["name"] == "test_proj_combined.pdf"
        assert summary["combined_pdf"]["size_kb"] > 0
        assert len(summary["individual_pdfs"]) == 1
        assert summary["individual_pdfs"][0]["name"] == "01_intro.pdf"
        assert summary["total_size_kb"] > 0

    def test_summary_with_real_web_outputs(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        output = project_root / "output"
        web_dir = output / "web"
        web_dir.mkdir(parents=True)
        (web_dir / "index.html").write_text("<html><body>combined</body></html>", encoding="utf-8")
        (web_dir / "page1.html").write_text("<html>page1</html>", encoding="utf-8")

        summary = generate_rendering_summary("templates/test_proj", repo_root=tmp_path)

        assert summary["combined_html"] is not None
        assert summary["combined_html"]["name"] == "index.html"
        assert len(summary["web_outputs"]) == 1
        assert summary["web_outputs"][0]["name"] == "page1.html"

    def test_summary_with_real_slides(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        output = project_root / "output"
        slides_dir = output / "slides"
        slides_dir.mkdir(parents=True)
        _make_pdf(slides_dir / "intro_slides.pdf", text="slides")

        summary = generate_rendering_summary("templates/test_proj", repo_root=tmp_path)

        assert len(summary["slides"]) == 1
        assert summary["slides"][0]["name"] == "intro_slides.pdf"

    def test_summary_empty_output_dir(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        (project_root / "output").mkdir(parents=True)

        summary = generate_rendering_summary("templates/test_proj", repo_root=tmp_path)

        assert summary["individual_pdfs"] == []
        assert summary["combined_pdf"] is None
        assert summary["combined_html"] is None
        assert summary["web_outputs"] == []
        assert summary["slides"] == []
        assert summary["total_size_kb"] == 0

    def test_summary_no_output_dir(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        project_root.mkdir(parents=True)

        summary = generate_rendering_summary("templates/test_proj", repo_root=tmp_path)

        assert summary["individual_pdfs"] == []
        assert summary["total_size_kb"] == 0


class TestVerifyPdfOutputs:
    """Test verify_pdf_outputs with real PDF files and directory structures."""

    def test_returns_true_with_valid_combined_pdf(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "00_abstract.md").write_text("# Abstract\n", encoding="utf-8")
        pdf_dir = project_root / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        _make_valid_combined_pdf(pdf_dir / "test_proj_combined.pdf")

        assert verify_pdf_outputs("templates/test_proj", repo_root=tmp_path) is True

    def test_returns_false_when_no_pdfs(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "00_abstract.md").write_text("# Abstract\n", encoding="utf-8")
        pdf_dir = project_root / "output" / "pdf"
        pdf_dir.mkdir(parents=True)

        assert verify_pdf_outputs("templates/test_proj", repo_root=tmp_path) is False

    def test_returns_false_when_combined_pdf_missing(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "00_abstract.md").write_text("# Abstract\n", encoding="utf-8")
        pdf_dir = project_root / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        _make_pdf(pdf_dir / "01_intro.pdf", text="intro")

        assert verify_pdf_outputs("templates/test_proj", repo_root=tmp_path) is False

    def test_returns_false_for_tiny_pdf(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "00_abstract.md").write_text("# Abstract\n", encoding="utf-8")
        pdf_dir = project_root / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        # Create a tiny file (< 0.1 KB) that looks like a failed compilation
        (pdf_dir / "test_proj_combined.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        assert verify_pdf_outputs("templates/test_proj", repo_root=tmp_path) is False

    def test_citations_detected_without_bib_warns(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "00_abstract.md").write_text(
            r"See \cite{smith2020} for details.",
            encoding="utf-8",
        )
        pdf_dir = project_root / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        _make_valid_combined_pdf(pdf_dir / "test_proj_combined.pdf")

        # Should still return True (valid PDF), just log a warning about missing bib
        assert verify_pdf_outputs("templates/test_proj", repo_root=tmp_path) is True

    def test_bibliography_found(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "00_abstract.md").write_text("# Abstract\n", encoding="utf-8")
        (manuscript / "references.bib").write_text(
            "@article{smith2020, title={Test}, author={Smith}, year={2020}}\n",
            encoding="utf-8",
        )
        pdf_dir = project_root / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        _make_valid_combined_pdf(pdf_dir / "test_proj_combined.pdf")

        assert verify_pdf_outputs("templates/test_proj", repo_root=tmp_path) is True

    def test_failed_compilation_with_log_file(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "00_abstract.md").write_text("# Abstract\n", encoding="utf-8")
        pdf_dir = project_root / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        # Tiny PDF (< 0.1 KB) = failed compilation
        (pdf_dir / "test_proj_combined.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        # Log file exists
        (pdf_dir / "test_proj_combined.log").write_text(
            "LaTeX Error: Something went wrong\n",
            encoding="utf-8",
        )

        assert verify_pdf_outputs("templates/test_proj", repo_root=tmp_path) is False

    def test_failed_compilation_with_alt_log_file(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "templates" / "test_proj"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "00_abstract.md").write_text("# Abstract\n", encoding="utf-8")
        pdf_dir = project_root / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        # Tiny PDF (< 0.1 KB) = failed compilation
        (pdf_dir / "test_proj_combined.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        # Alternate log file naming (underscore prefix)
        (pdf_dir / "_test_proj_combined.log").write_text(
            "LaTeX Error: Something went wrong\n",
            encoding="utf-8",
        )

        assert verify_pdf_outputs("templates/test_proj", repo_root=tmp_path) is False


class TestManuscriptDirForVerify:
    """Test the manuscript directory resolution logic."""

    def test_prefers_injected_when_populated(self, tmp_path: Path) -> None:
        source = tmp_path / "docs" / "manuscript"
        injected = tmp_path / "output" / "manuscript"
        source.mkdir(parents=True)
        injected.mkdir(parents=True)
        (source / "01_intro.md").write_text("# Source\n", encoding="utf-8")
        (injected / "01_intro.md").write_text("# Injected\n", encoding="utf-8")

        result = _manuscript_dir_for_verify(tmp_path)
        assert result == injected

    def test_falls_back_to_source_when_injected_empty(self, tmp_path: Path) -> None:
        source = tmp_path / "docs" / "manuscript"
        injected = tmp_path / "output" / "manuscript"
        source.mkdir(parents=True)
        injected.mkdir(parents=True)
        (source / "01_intro.md").write_text("# Source\n", encoding="utf-8")

        result = _manuscript_dir_for_verify(tmp_path)
        assert result == source

    def test_falls_back_to_source_when_injected_missing(self, tmp_path: Path) -> None:
        source = tmp_path / "docs" / "manuscript"
        source.mkdir(parents=True)
        (source / "01_intro.md").write_text("# Source\n", encoding="utf-8")

        result = _manuscript_dir_for_verify(tmp_path)
        assert result == source


class TestLogRenderingSummaryFullPaths:
    """Exercise log_rendering_summary with full path strings."""

    def test_log_summary_with_path_strings(self) -> None:
        summary = {
            "project": "test_proj",
            "combined_pdf": {
                "name": "combined.pdf",
                "size_kb": 512.0,
                "path": "/some/abs/path/combined.pdf",
            },
            "combined_html": {
                "name": "index.html",
                "size_kb": 64.0,
                "path": "/some/abs/path/index.html",
            },
            "individual_pdfs": [{"name": "01.pdf", "size_kb": 128.0}],
            "web_outputs": [{"name": "page1.html", "size_kb": 32.0}],
            "slides": [{"name": "slides.pdf", "size_kb": 256.0}],
            "total_size_kb": 992.0,
        }
        log_rendering_summary(summary)  # should not raise
