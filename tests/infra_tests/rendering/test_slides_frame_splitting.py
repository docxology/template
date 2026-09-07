"""Frame-splitting behaviour tests for ``SlidesRenderer``.

Exercises :func:`infrastructure.rendering.slides_renderer.split_long_slide_frames`
against verbatim/lstlisting bodies, wrapped equations, wrapped frame titles,
longtables, and explicit TeX groups, plus the source-heading slide-level logic.
"""

from __future__ import annotations

import shutil

import pytest

from infrastructure.rendering import slides_renderer
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer

from ._helpers import _require_beamer_toolchain


class TestSlidesRendererClass:
    """Test SlidesRenderer class using real implementations."""

    def test_split_long_slide_frames_isolates_unbreakable_figure(self):
        tex = (
            r"\begin{frame}[allowframebreaks]{Dense}" + "\n"
            "Before the figure.\n\n"
            r"\begin{figure}" + "\n"
            r"\includegraphics{plot.png}" + "\n"
            r"\caption{A dense caption.}" + "\n"
            r"\end{figure}" + "\n\n"
            "After the figure.\n"
            r"\end{frame}" + "\n"
        )

        updated, changed = slides_renderer.split_long_slide_frames(tex)

        assert changed == 1
        assert updated.count(r"\begin{frame}") == 3
        assert r"\framebreak" not in updated
        assert updated.index(r"Before the figure.") < updated.index(r"\end{frame}")
        assert updated.index(r"\end{figure}") < updated.rindex(r"\end{frame}")
        assert updated.index(r"\end{figure}") < updated.index(r"After the figure.")
        assert updated.index(r"After the figure.") < updated.rindex(r"\end{frame}")

    def test_split_long_slide_frames_isolates_verbatim_and_lstlisting(self):
        """verbatim/lstlisting bodies must never receive an internal framebreak."""
        for env in ("verbatim", "lstlisting"):
            tex = (
                r"\begin{frame}[allowframebreaks]{Code}" + "\n"
                "Intro text before the code block.\n\n"
                r"\begin{" + env + "}" + "\n"
                "x = 1\n"
                "y = 2\n"
                r"\end{" + env + "}" + "\n\n"
                "Closing prose after the block.\n"
                r"\end{frame}" + "\n"
            )

            updated, changed = slides_renderer.split_long_slide_frames(tex)

            assert changed == 1
            # The environment is isolated into its own frame: no framebreak
            # marker inside the body, and intro/env/closing each end up in
            # distinct frames.
            body_start = updated.index(r"\begin{" + env + "}")
            body_end = updated.index(r"\end{" + env + "}")
            assert r"\framebreak" not in updated[body_start:body_end]
            intro_frame_end = updated.index(r"\end{frame}", updated.index("Intro text"))
            assert body_start > intro_frame_end
            assert updated.index("Closing prose") > body_end

    def test_split_long_slide_frames_breaks_top_level_paragraphs_only(self):
        tex = (
            r"\begin{frame}[allowframebreaks]{Dense}" + "\n" + ("A long top-level paragraph. " * 80) + "\n\n"
            r"\begin{itemize}" + "\n"
            r"\item " + ("A long list item. " * 120) + "\n"
            r"\end{itemize}" + "\n"
            r"\end{frame}" + "\n"
        )

        updated, changed = slides_renderer.split_long_slide_frames(tex)

        assert changed == 1
        assert updated.count(r"\begin{frame}") >= 2
        assert r"\framebreak" not in updated
        list_start = updated.index(r"\begin{itemize}")
        list_end = updated.index(r"\end{itemize}")
        assert r"\framebreak" not in updated[list_start:list_end]

    def test_split_long_slide_frames_leaves_non_breakable_frame_unchanged(self):
        tex = (
            r"\begin{frame}{Dense}" + "\n" + ("A long paragraph. " * 200) + "\n"
            r"\end{frame}" + "\n"
        )

        updated, changed = slides_renderer.split_long_slide_frames(tex)

        assert changed == 0
        assert updated == tex

    def test_split_long_slide_frames_pops_wrapped_equation_environment(self):
        tex = (
            r"\begin{frame}[allowframebreaks]{Equation}" + "\n"
            "Context before the equation.\n\n"
            r"\begin{equation}\protect\phantomsection\label{eq:test}{" + "\n"
            r"q(s) = \mathrm{softmax}(x(s))." + "\n"
            r"}\end{equation}"
            + "\n\n"
            + ("A continuation line that must remain visible.\n" * 50)
            + r"\end{frame}"
            + "\n"
        )

        updated, changed = slides_renderer.split_long_slide_frames(tex)

        assert changed == 1
        assert updated.count(r"\begin{frame}") >= 2
        assert r"\framebreak" not in updated
        assert r"\end{equation}" in updated
        assert "A continuation line" in updated.rsplit(r"\begin{frame}", 1)[1]

    def test_split_long_slide_frames_matches_wrapped_frame_titles(self):
        tex = (
            r"\begin{frame}[allowframebreaks]{A title that wraps" + "\n"
            r"across source lines}" + "\n" + ("A long paragraph. " * 120) + "\n\n"
            "A second paragraph.\n"
            r"\end{frame}" + "\n"
        )

        updated, changed = slides_renderer.split_long_slide_frames(tex)

        assert changed == 1
        assert updated.count(r"\begin{frame}") == 2
        assert r"\framebreak" not in updated

    def test_split_long_slide_frames_preserves_nested_markup_in_wrapped_titles(self):
        tex = (
            r"\begin{frame}[fragile,allowframebreaks]{The \texttt{secure\_run.sh}" + "\n"
            r"Orchestrator}" + "\n" + ("A long paragraph. " * 120) + "\n\n"
            "A second paragraph.\n"
            r"\end{frame}" + "\n"
        )

        updated, changed = slides_renderer.split_long_slide_frames(tex)

        complete_title = "{The " + r"\texttt{secure\_run.sh}" + "\nOrchestrator}"
        assert changed == 1
        assert updated.count(r"\begin{frame}") == 2
        assert updated.count(complete_title) == 2
        assert r"\framebreak" not in updated

    def test_split_long_slide_frames_never_breaks_longtable_alignment(self):
        tex = r"""\begin{frame}[allowframebreaks]{Table}
Context before the table.

{\def\LTcaptype{none}
\begin{longtable}[]{@{}ll@{}}
\toprule\noalign{}
\begin{minipage}[b]{\linewidth}A\end{minipage} & \begin{minipage}[b]{\linewidth}B\end{minipage} \\
\midrule\noalign{}
\endhead
A & B \\
\end{longtable}
}

Context after the table.
\end{frame}
"""

        updated, _ = slides_renderer.split_long_slide_frames(tex)

        table_start = updated.index(r"\begin{longtable}")
        table_end = updated.index(r"\end{longtable}")
        assert r"\framebreak" not in updated[table_start:table_end]

    def test_split_long_slide_frames_preserves_explicit_tex_group_around_table(self):
        """A Pandoc table font group must remain inside one continuation frame."""
        tex = r"""\begin{frame}[fragile,allowframebreaks]{Grouped table}
\begingroup\footnotesize

\begin{longtable}[]{@{}ll@{}}
\toprule\noalign{}
A & B \\
\midrule\noalign{}
\endhead
one & two \\
\bottomrule\noalign{}
\end{longtable}

\endgroup
Content after the grouped table.
\end{frame}
"""

        updated, changed = slides_renderer.split_long_slide_frames(tex)

        grouped = updated[updated.index(r"\begingroup") : updated.index(r"\endgroup")]
        assert changed == 1
        assert updated.count(r"\begin{frame}") == 2
        assert r"\begin{longtable}" in grouped
        assert r"\begin{frame}" not in grouped
        assert r"\end{frame}" not in grouped
        assert r"\framebreak" not in grouped

    def test_slide_level_follows_deepest_source_heading(self, tmp_path):
        shallow = tmp_path / "shallow.md"
        shallow.write_text("# Title\n\n## Section\n\nText.\n", encoding="utf-8")
        deep = tmp_path / "deep.md"
        deep.write_text(
            "# Title\n\n## Results\n\n### Sweep\n\n#### Axis\n\nText.\n",
            encoding="utf-8",
        )

        assert SlidesRenderer._slide_level_for_source(shallow) == 2
        assert SlidesRenderer._slide_level_for_source(deep) == 4

    def test_slide_level_caps_pathological_heading_depth(self, tmp_path):
        source = tmp_path / "deep.md"
        source.write_text("###### Detail\n\nText.\n", encoding="utf-8")

        assert SlidesRenderer._slide_level_for_source(source) == 4

    def test_slides_renderer_initialization(self, tmp_path):
        """Test SlidesRenderer initialization."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        assert renderer.config == config

    @pytest.mark.slow
    def test_render_with_revealjs(self, tmp_path):
        """Test render() method with revealjs format using real execution."""
        config = RenderingConfig(output_dir=tmp_path, slides_dir=tmp_path / "slides")
        renderer = SlidesRenderer(config)
        (tmp_path / "slides").mkdir(exist_ok=True)

        # Create test markdown
        source = tmp_path / "slides.md"
        source.write_text("# Slide 1\n\n---\n\n# Slide 2")

        if not shutil.which("pandoc"):
            pytest.skip("Pandoc not installed")

        result = renderer.render(source, output_format="revealjs")
        assert result.is_file()
        assert "Slide 1" in result.read_text(encoding="utf-8")

    @pytest.mark.slow
    def test_render_with_beamer(self, tmp_path):
        """Test render() method with beamer format using real execution."""
        config = RenderingConfig(output_dir=tmp_path, slides_dir=tmp_path / "slides")
        renderer = SlidesRenderer(config)
        (tmp_path / "slides").mkdir(exist_ok=True)

        source = tmp_path / "slides.md"
        source.write_text("# Slide 1")

        compiler = _require_beamer_toolchain()
        config.latex_compiler = compiler
        result = renderer.render(source, output_format="beamer")
        assert result.is_file()
        assert result.stat().st_size > 1_000
