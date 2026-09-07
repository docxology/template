"""Figure-path and accessible-projection LaTeX tests for slide rendering.

Exercises :func:`infrastructure.rendering._slides_tex_figures.fix_slides_figure_paths`
and :func:`normalize_accessible_projection_latex` against real Pandoc Beamer
output shapes and the real LaTeX toolchain.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest
from pypdf import PdfReader

from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering._slides_tex_figures import fix_slides_figure_paths, normalize_accessible_projection_latex
from infrastructure.rendering.slides_renderer import SlidesRenderer


class TestFigurePathFixing:
    """Test figure path fixing using real implementations."""

    def test_fix_figure_paths_basic(self, tmp_path):
        """Test basic figure path fixing."""
        config = RenderingConfig(output_dir=tmp_path)
        SlidesRenderer(config)

        tex_content = r"\includegraphics{../output/figures/test.png}"
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()

        fixed = fix_slides_figure_paths(tex_content, output_dir, figures_dir)

        assert "../figures/test.png" in fixed

    def test_fix_figure_paths_already_correct(self, tmp_path):
        """Test that already correct paths are unchanged."""
        config = RenderingConfig(output_dir=tmp_path)
        SlidesRenderer(config)

        tex_content = r"\includegraphics{../figures/test.png}"
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()

        fixed = fix_slides_figure_paths(tex_content, output_dir, figures_dir)

        # Should remain unchanged
        assert "../figures/test.png" in fixed

    def test_fix_figure_paths_multiple(self, tmp_path):
        """Test fixing multiple figure paths."""
        config = RenderingConfig(output_dir=tmp_path)
        SlidesRenderer(config)

        tex_content = r"""
        \includegraphics{../output/figures/fig1.png}
        \includegraphics{../output/figures/fig2.png}
        \includegraphics{../figures/fig3.png}
        """
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()

        fixed = fix_slides_figure_paths(tex_content, output_dir, figures_dir)

        assert "../figures/fig1.png" in fixed
        assert "../figures/fig2.png" in fixed
        assert "../figures/fig3.png" in fixed

    def test_fix_figure_paths_handles_pandoc_alt_text_brackets(self, tmp_path):
        """Pandoc Beamer alt text can contain brackets that defeat regex parsing."""
        config = RenderingConfig(output_dir=tmp_path)
        SlidesRenderer(config)

        tex_content = (
            r"\pandocbounded{\includegraphics[keepaspectratio,"
            r"alt={Curve on {[}0, 6{]} with $I(q_\lambda)$}]"
            r"{../output/figures/free_energy_curve.png}}"
        )
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()

        fixed = fix_slides_figure_paths(tex_content, output_dir, figures_dir)

        assert "{../figures/free_energy_curve.png}" in fixed
        assert "alt={Curve on {[}0, 6{]} with $I(q_\\lambda)$}" in fixed
        assert "../output/figures" not in fixed

    def test_accessible_figure_latex_preserves_ratio_and_removes_empty_caption(self):
        tex = (
            r"\begin{figure}\includegraphics[width=0.98\linewidth,height=0.7\textheight,"
            r"alt={Curve on {[}0, 6{]}}]{figure.png}\caption{}\label{fig:curve}\end{figure}"
        )

        updated, graphics, captions = normalize_accessible_projection_latex(tex)

        assert "keepaspectratio,width=0.98\\linewidth,height=0.7\\textheight" in updated
        assert r"\caption{}" not in updated
        assert r"\refstepcounter{figure}\label{fig:curve}" in updated
        assert r"\label{fig:curve}" in updated
        assert graphics == 1
        assert captions == 1

    def test_accessible_bare_and_linked_projection_images_preserve_aspect_ratio(self):
        tex = (
            r"\includegraphics[width=0.98\linewidth,height=0.7\textheight]{plain.png}"
            "\n"
            r"\href{full.png}{\includegraphics[width=0.98\linewidth,height=0.7\textheight]{linked.png}}"
            "\n"
            r"\begin{figure}"
            r"\href{left-full.png}{\includegraphics[width=0.45\linewidth,height=0.7\textheight]{left.png}}"
            r"\href{right-full.png}{\includegraphics[width=0.45\linewidth,height=0.7\textheight]{right.png}}"
            r"\end{figure}"
        )

        updated, graphics, captions = normalize_accessible_projection_latex(tex)

        assert updated.count("keepaspectratio") == 4
        assert graphics == 4
        assert captions == 0

    def test_accessible_figure_latex_is_idempotent_and_leaves_unbounded_images_alone(self):
        tex = (
            r"\includegraphics[keepaspectratio,width=0.9\linewidth,height=0.5\textheight]{bounded.png}"
            "\n"
            r"\includegraphics[width=0.5\linewidth]{width-only.png}"
        )

        updated, graphics, captions = normalize_accessible_projection_latex(tex)

        assert updated == tex
        assert graphics == 0
        assert captions == 0

    def test_accessible_projection_normalization_is_scoped_and_brace_aware(self):
        tex = (
            r"\begin{figure}"
            r"\includegraphics[width=0.98\linewidth,height=0.7\textheight,"
            r"keepaspectratio=false,alt={Panel, keepaspectratio, evidence}]{figure.png}"
            r"\caption{}\label{fig:curve}"
            r"\begin{algorithm}\caption{}\label{alg:nested}\end{algorithm}"
            "% \\caption{} \\includegraphics[width=1in,height=1in]{comment.png}\n"
            r"\begin{verbatim}\caption{}\includegraphics[width=1in,height=1in]{code.png}\end{verbatim}"
            r"\verb|\includegraphics[width=1in,height=1in]{inline.png}|"
            r"\caption{Literal \texttt{\caption{}} and "
            r"\includegraphics[width=1in,height=1in]{caption.png}}"
            r"\custom{\caption{}}"
            r"\end{figure}"
            r"\begin{longtable}{ll}\caption{}\label{tbl:values}A&B\end{longtable}"
            r"\begin{algorithm}\caption{}\label{alg:outside}\end{algorithm}"
        )

        updated, graphics, captions = normalize_accessible_projection_latex(tex)
        second, second_graphics, second_captions = normalize_accessible_projection_latex(updated)

        assert "keepaspectratio,width=0.98\\linewidth,height=0.7\\textheight" in updated
        assert "alt={Panel, keepaspectratio, evidence}" in updated
        assert "keepaspectratio=false" not in updated
        assert r"\label{fig:curve}" in updated
        assert r"\label{tbl:values}" in updated
        assert updated.count(r"\refstepcounter{figure}") == 1
        assert r"\refstepcounter{table}" not in updated
        assert updated.count(r"\caption{}") == 6
        assert r"\label{alg:nested}" in updated
        assert r"\label{alg:outside}" in updated
        assert "comment.png" in updated
        assert "code.png" in updated
        assert "inline.png" in updated
        assert "caption.png" in updated
        assert graphics == 1
        assert captions == 2
        assert second == updated
        assert second_graphics == 0
        assert second_captions == 0

    @pytest.mark.requires_latex
    def test_empty_caption_replacement_preserves_float_and_longtable_numbering(self, tmp_path):
        compiler = next((name for name in ("pdflatex", "xelatex", "lualatex") if shutil.which(name)), None)
        if compiler is None:
            pytest.skip("No LaTeX compiler available")
        source = (
            r"\documentclass{article}"
            r"\usepackage{longtable}"
            r"\begin{document}"
            r"\begin{figure}\caption{}\label{fig:first}A\end{figure}"
            r"Figure \ref{fig:first}. "
            r"\begin{longtable}{l}\caption{}\label{tbl:long}Value\\\end{longtable}"
            r"Long \ref{tbl:long}. "
            r"\begin{table}\caption{}\label{tbl:next}B\end{table}"
            r"Next \ref{tbl:next}."
            r"\end{document}"
        )
        normalized, _graphics, captions = normalize_accessible_projection_latex(source)
        tex_path = tmp_path / "numbering.tex"
        tex_path.write_text(normalized, encoding="utf-8")

        for _pass in range(2):
            subprocess.run(
                [compiler, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
                cwd=tmp_path,
                check=True,
                capture_output=True,
                text=True,
            )

        extracted = " ".join(page.extract_text() or "" for page in PdfReader(str(tex_path.with_suffix(".pdf"))).pages)
        assert captions == 3
        assert re.search(r"Figure\s+1", extracted)
        assert re.search(r"Long\s+1", extracted)
        assert re.search(r"Next\s+2", extracted)
