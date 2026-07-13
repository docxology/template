"""Tests for PDF renderer bibliography and figure path fixes using real implementations.

This module tests the critical fixes for:
1. Bibliography processing (bibtex execution)
2. Figure path resolution with Unicode support
3. Citation resolution in final PDF

Follows No Mocks Policy - all tests use real data and real execution.
"""

import shutil
import unicodedata

import pytest


from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering._pdf_latex_pipeline import process_bibliography
from infrastructure.rendering._pdf_figure_paths import fix_figure_paths


class TestBibliographyProcessing:
    """Test bibliography processing functionality."""

    @pytest.mark.skipif(shutil.which("bibtex") is None, reason="bibtex not installed")
    def test_process_bibliography_success(self, tmp_path):
        """Test successful bibliography processing with real bibtex.

        Local-only coverage: CI installs pandoc but not TeX Live, so this
        skips on GitHub runners and is enforced on developer machines.
        """
        # Create necessary files
        tex_file = tmp_path / "test.tex"
        aux_file = tmp_path / "pdf" / "test.aux"
        bib_file = tmp_path / "references.bib"

        tex_file.write_text("\\documentclass{article}\n\\begin{document}\n\\end{document}")
        (tmp_path / "pdf").mkdir(exist_ok=True)
        aux_file.write_text("some aux content")
        bib_file.write_text("@article{test,\n  title={Test}\n}")

        result = process_bibliography(tex_file, tmp_path / "pdf", [bib_file])
        assert isinstance(result, bool)
        # The bib file must have been copied next to the aux file either way.
        assert (tmp_path / "pdf" / "references.bib").exists()

    def test_process_bibliography_missing_bib_file(self, tmp_path):
        """Test bibliography processing with missing bib file."""
        tex_file = tmp_path / "test.tex"
        bib_file = tmp_path / "missing.bib"

        result = process_bibliography(tex_file, tmp_path / "pdf", [bib_file])
        assert result is False

    def test_process_bibliography_empty_paths(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        (tmp_path / "pdf").mkdir(exist_ok=True)
        assert process_bibliography(tex_file, tmp_path / "pdf", []) is False

    def test_process_bibliography_copies_all_bib_files(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("% stub\n")
        (pdf_dir / "test.aux").write_text("\\bibdata{references,extra}\n")
        bib_a = tmp_path / "references.bib"
        bib_b = tmp_path / "extra.bib"
        bib_a.write_text("@article{a,title={A},year={2024}}\n")
        bib_b.write_text("@article{b,title={B},year={2024}}\n")
        process_bibliography(tex_file, pdf_dir, [bib_a, bib_b])
        assert (pdf_dir / "references.bib").exists()
        assert (pdf_dir / "extra.bib").exists()

    def test_process_bibliography_missing_aux_file(self, tmp_path):
        """Test bibliography processing with missing auxiliary file."""
        tex_file = tmp_path / "test.tex"
        bib_file = tmp_path / "references.bib"

        tex_file.write_text("test")
        bib_file.write_text("@article{test, title={Test}}")
        (tmp_path / "pdf").mkdir(exist_ok=True)

        result = process_bibliography(tex_file, tmp_path / "pdf", [bib_file])
        assert result is False

    def test_process_bibliography_bibtex_warning(self, tmp_path):
        """Test bibliography processing handles bibtex warnings gracefully."""
        tex_file = tmp_path / "test.tex"
        aux_file = tmp_path / "pdf" / "test.aux"
        bib_file = tmp_path / "references.bib"

        tex_file.write_text("test")
        (tmp_path / "pdf").mkdir(exist_ok=True)
        aux_file.write_text("aux content")
        bib_file.write_text("@article{test, title={Test}}")

        result = process_bibliography(tex_file, tmp_path / "pdf", [bib_file])
        assert isinstance(result, bool)
        assert (tmp_path / "pdf" / "references.bib").exists()


class TestFigurePathResolution:
    """Test figure path resolution with Unicode support."""

    def test_fix_figure_paths_basic(self, tmp_path):
        """Test basic figure path fixing."""
        # Create figure directory and file
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "test.png").write_text("fake image")

        # Test LaTeX content with figure reference
        tex_content = r"""
        \includegraphics[width=0.8\textwidth]{../output/figures/test.png}
        """

        fixed = fix_figure_paths(tex_content, tmp_path / "manuscript", tmp_path / "output" / "pdf")

        assert "../figures/test.png" in fixed
        assert "../output/figures/test.png" not in fixed

    def test_fix_figure_paths_with_options(self, tmp_path):
        """Test figure path fixing preserves options."""
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "test.png").write_text("fake")

        tex_content = r"\includegraphics[width=0.9\textwidth]{../output/figures/test.png}"

        fixed = fix_figure_paths(tex_content, tmp_path / "manuscript", tmp_path / "output" / "pdf")

        assert "[width=0.9\\textwidth]" in fixed
        assert "../figures/test.png" in fixed

    def test_fix_figure_paths_unicode_filename(self, tmp_path):
        """Test figure path fixing with Unicode characters in filename."""
        # Create figure with Unicode filename
        (tmp_path / "output" / "figures").mkdir(parents=True)
        unicode_filename = "figure_ñ_test.png"  # Filename with ñ
        (tmp_path / "output" / "figures" / unicode_filename).write_text("fake")

        tex_content = f"\\includegraphics{{../output/figures/{unicode_filename}}}"

        fixed = fix_figure_paths(tex_content, tmp_path / "manuscript", tmp_path / "output" / "pdf")

        # Should normalize and fix the path
        assert "../figures/" in fixed
        assert unicode_filename in fixed or unicodedata.normalize("NFC", unicode_filename) in fixed

    def test_fix_figure_paths_missing_figure(self, tmp_path):
        """Test figure path fixing handles missing figures gracefully."""
        (tmp_path / "output" / "figures").mkdir(parents=True)

        tex_content = r"\includegraphics{../output/figures/missing.png}"

        fixed = fix_figure_paths(tex_content, tmp_path / "manuscript", tmp_path / "output" / "pdf")

        # Should still fix the path even if file missing
        assert "../figures/missing.png" in fixed

    def test_fix_figure_paths_already_correct(self, tmp_path):
        """Test figure paths that are already correct."""
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "test.png").write_text("fake")

        # Already in correct format
        tex_content = r"\includegraphics{../figures/test.png}"

        fixed = fix_figure_paths(tex_content, tmp_path / "manuscript", tmp_path / "output" / "pdf")

        # Should remain unchanged
        assert fixed == tex_content

    def test_fix_multiple_figure_paths(self, tmp_path):
        """Test fixing multiple figure paths in content."""
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "fig1.png").write_text("fake")
        (tmp_path / "output" / "figures" / "fig2.pdf").write_text("fake")

        tex_content = r"""
        \includegraphics{../output/figures/fig1.png}

        Some text here.

        \includegraphics[width=0.5\textwidth]{../output/figures/fig2.pdf}
        """

        fixed = fix_figure_paths(tex_content, tmp_path / "manuscript", tmp_path / "output" / "pdf")

        # Both paths should be fixed
        assert fixed.count("../figures/") == 2
        assert "../output/figures" not in fixed


class TestCitationProcessing:
    """Test citation processing in rendering pipeline."""

    @pytest.mark.timeout(90)
    @pytest.mark.skipif(
        shutil.which("pandoc") is None or shutil.which("xelatex") is None,
        reason="pandoc/xelatex not installed",
    )
    def test_render_combined_includes_bibliography(self, tmp_path):
        """Test that render_combined includes bibliography processing.

        Local-only coverage: CI installs pandoc but not TeX Live (xelatex),
        so this skips on GitHub runners and is enforced on developer machines.
        """
        config = RenderingConfig(
            manuscript_dir=str(tmp_path / "manuscript"),
            output_dir=str(tmp_path / "output"),
            pdf_dir=str(tmp_path / "output" / "pdf"),
            pandoc_path="pandoc",
        )
        renderer = PDFRenderer(config)

        # Create necessary files
        (tmp_path / "manuscript").mkdir(parents=True)
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "pdf").mkdir(parents=True)

        md_file = tmp_path / "manuscript" / "test.md"
        md_file.write_text("# Test\n\nSome content with \\cite{test}")

        bib_file = tmp_path / "manuscript" / "references.bib"
        bib_file.write_text("@article{test, title={Test}, year={2024}}")

        # Real execution: tools are present (skipif above), so demand a real PDF.
        result = renderer.render_combined([md_file], tmp_path / "manuscript")
        assert result.exists(), f"render_combined returned {result} but no file exists"
        assert result.suffix == ".pdf"
        assert result.stat().st_size > 0


class TestIntegration:
    """Integration tests for bibliography and figure fixes."""

    def test_latex_content_with_citations_and_figures(self, tmp_path):
        """Test fixing LaTeX content with both citations and figures."""
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "results.png").write_text("fake")

        # Realistic LaTeX with both citations and figures
        tex_content = r"""
        \documentclass{article}
        \usepackage{graphicx}
        \bibliographystyle{plain}

        \begin{document}

        According to recent work \cite{smith2020}, we can see in Figure \ref{fig:results}:

        \begin{figure}[h]
        \centering
        \includegraphics[width=0.8\textwidth]{../output/figures/results.png}
        \caption{Our results}
        \label{fig:results}
        \end{figure}

        \bibliography{references}
        \end{document}
        """

        fixed = fix_figure_paths(tex_content, tmp_path / "manuscript", tmp_path / "output" / "pdf")

        # Figure path should be fixed
        assert "../figures/results.png" in fixed
        # Citations should remain unchanged (handled by bibtex)
        assert r"\cite{smith2020}" in fixed
        assert r"\bibliography{references}" in fixed
