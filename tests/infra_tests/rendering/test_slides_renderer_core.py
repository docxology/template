"""Core behaviour tests for ``SlidesRenderer``.

These tests focus on regressions in the Beamer rendering path that the
broader ``test_slides_renderer_comprehensive.py`` and ``_coverage.py``
suites do not exercise. In particular:

* :func:`test_long_section_renders_via_allowframebreaks` verifies that a
  single long section without h2 sub-headings renders to a non-trivial
  PDF — i.e. the ``_beamer_allowframebreaks.lua`` filter prevents the
  ``Overfull \\vbox … Error 256`` failure mode that previously left a
  15-byte stub PDF on disk.

Follows the No Mocks Policy — the test invokes the real Pandoc + xelatex
pipeline via ``SlidesRenderer.render`` and inspects the resulting PDF
and ``.log`` file on disk.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering import slides_renderer
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering._slides_math_header import write_slides_math_header
from infrastructure.rendering._slides_tex_figures import fix_slides_figure_paths
from infrastructure.rendering.slides_renderer import SlidesRenderer


def _require_beamer_toolchain() -> str:
    """Return the available LaTeX compiler or skip when Beamer tools are absent."""
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    if shutil.which("xelatex"):
        return "xelatex"
    if shutil.which("pdflatex"):
        return "pdflatex"
    else:
        pytest.skip("No LaTeX compiler available")


def _multi_bibliography_slide_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Write one slide whose two citations live in separate bibliography files."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "references.bib").write_text(
        "@article{alpha2020primary,\n"
        "  author={Alpha, Ada},\n"
        "  title={Primary Source},\n"
        "  journal={Journal One},\n"
        "  year={2020}\n"
        "}\n",
        encoding="utf-8",
    )
    (manuscript_dir / "z_supplemental.bib").write_text(
        "@article{omega2021supplement,\n"
        "  author={Omega, Orla},\n"
        "  title={Supplemental Source},\n"
        "  journal={Journal Two},\n"
        "  year={2021}\n"
        "}\n",
        encoding="utf-8",
    )
    source = tmp_path / "multi_bibliography.md"
    source.write_text(
        "# Evidence\n\nBoth sources matter [@alpha2020primary; @omega2021supplement].\n",
        encoding="utf-8",
    )
    return source, manuscript_dir


@pytest.mark.slow
@pytest.mark.requires_latex
def test_long_section_renders_via_allowframebreaks(test_config, tmp_path):
    """A single long section must split across slides and produce a real PDF.

    Before the ``_beamer_allowframebreaks.lua`` filter was wired into
    ``SlidesRenderer._render_beamer_with_paths``, Pandoc wrapped the
    entire section in a single ``\\begin{frame}…\\end{frame}``; xelatex
    overflowed the vbox and aborted with driver code 256, leaving a
    15-byte PDF stub. With the filter in place every h1/h2 frame gets
    ``[allowframebreaks]`` and the content splits cleanly across slides.
    """
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    if test_config.latex_compiler is None:
        pytest.skip("No LaTeX compiler available")

    paragraphs = [f"Paragraph {i}: " + ("lorem ipsum dolor sit amet " * 12) for i in range(1, 151)]
    long_md = tmp_path / "long_section.md"
    long_md.write_text("# A Very Long Section\n\n" + "\n\n".join(paragraphs) + "\n")

    renderer = SlidesRenderer(test_config)
    result = renderer.render(long_md, output_format="beamer")

    assert result.exists(), f"Expected PDF at {result}"
    pdf_bytes = result.stat().st_size
    assert pdf_bytes > 5_000, (
        f"Beamer PDF is {pdf_bytes} bytes — likely the 15-byte xelatex stub. Did the allowframebreaks Lua filter run?"
    )

    log_path = result.with_suffix(".log")
    if log_path.exists():
        log_text = log_path.read_text(errors="ignore")
        assert "Error 256 (driver return code)" not in log_text, (
            "xelatex aborted with driver code 256 — overflowing frame not split."
        )
        assert "(job aborted, no legal \\end found)" not in log_text, "xelatex aborted before reaching \\end{document}."


@pytest.mark.requires_latex
def test_captioned_codelisting_renders_without_beamer_float_errors(test_config, tmp_path):
    """A crossref-style captioned listing must be a numbered non-float block."""
    _require_beamer_toolchain()
    if not shutil.which("pandoc-crossref"):
        pytest.skip("pandoc-crossref not installed")
    source = tmp_path / "captioned_code.md"
    source.write_text(
        "# Captioned code\n\n"
        "See [@lst:deterministic-example].\n\n"
        '```{#lst:deterministic-example .python caption="Deterministic example"}\n'
        "print(1)\n"
        "```\n",
        encoding="utf-8",
    )

    result = SlidesRenderer(test_config).render(source, output_format="beamer", manuscript_dir=tmp_path)

    assert result.is_file()
    assert result.stat().st_size > 5_000
    extracted = "\n".join(page.extract_text() or "" for page in PdfReader(str(result)).pages)
    assert "Listing 1: Deterministic example" in extracted
    assert re.search(r"See\s+(?:lst\.|Listing)\s*1", extracted, flags=re.IGNORECASE)
    assert "lst:deterministic-example" not in extracted
    log_text = result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert "Not in outer par mode" not in log_text
    assert "Undefined control sequence" not in log_text
    assert "undefined references" not in log_text.lower()


def test_slide_bibliography_args_use_sorted_union_and_suppress_references(tmp_path: Path):
    """Both slide writers receive the same deterministic citation arguments."""
    _source, manuscript_dir = _multi_bibliography_slide_fixture(tmp_path)

    args = slides_renderer._slide_bibliography_args(manuscript_dir)

    expected_bibliographies = [
        f"--bibliography={manuscript_dir / 'references.bib'}",
        f"--bibliography={manuscript_dir / 'z_supplemental.bib'}",
    ]
    assert args == [
        "--citeproc",
        *expected_bibliographies,
        "--metadata",
        "suppress-bibliography=true",
    ]
    assert slides_renderer._slide_bibliography_args(None) == []


@pytest.mark.requires_latex
def test_beamer_resolves_citations_from_every_top_level_bibliography(test_config, tmp_path):
    """The real Beamer/Pandoc path resolves supplemental bibliography citations."""
    _require_beamer_toolchain()
    source, manuscript_dir = _multi_bibliography_slide_fixture(tmp_path)

    result = SlidesRenderer(test_config).render(
        source,
        output_format="beamer",
        manuscript_dir=manuscript_dir,
    )

    extracted = "\n".join(page.extract_text() or "" for page in PdfReader(str(result)).pages)
    assert "Alpha" in extracted
    assert "Omega" in extracted
    assert "alpha2020primary?" not in extracted
    assert "omega2021supplement?" not in extracted
    assert "Primary Source" not in extracted
    assert "Supplemental Source" not in extracted


def test_revealjs_resolves_citations_from_every_top_level_bibliography(test_config, tmp_path):
    """The real Reveal.js/Pandoc path resolves the same supplemental citations."""
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    source, manuscript_dir = _multi_bibliography_slide_fixture(tmp_path)

    result = SlidesRenderer(test_config).render(
        source,
        output_format="revealjs",
        manuscript_dir=manuscript_dir,
    )

    html = result.read_text(encoding="utf-8")
    assert "Alpha" in html
    assert "Omega" in html
    assert "[@alpha2020primary" not in html
    assert "@omega2021supplement]" not in html
    assert 'id="refs"' not in html


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


@pytest.mark.slow
class TestRevealJsRendering:
    """Test reveal.js rendering using real execution."""

    def test_render_revealjs_success(self, tmp_path):
        """Test successful reveal.js rendering using real pandoc."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.html"

        if not shutil.which("pandoc"):
            pytest.skip("Pandoc not installed")

        result = renderer._render_revealjs(source, output)
        assert result == output
        assert output.is_file()
        # The opt-in accessible profile owns its valid Reveal theme; archive
        # mode preserves the historical caller-configured theme unchanged.
        rendered = output.read_text(encoding="utf-8")
        assert "theme/metropolis.css" in rendered
        assert "mathjax" not in rendered.casefold()

    def test_render_revealjs_failure(self, tmp_path):
        """Test reveal.js rendering failure handling with real execution."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.html"

        def fail_pandoc(*args, **kwargs):
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["pandoc"],
                stderr="simulated reveal.js failure",
            )

        renderer = SlidesRenderer(config, process_runner=fail_pandoc)
        with pytest.raises(RenderingError, match="Failed to render slides"):
            renderer._render_revealjs(source, output)


@pytest.mark.slow
class TestBeamerRendering:
    """Test Beamer rendering using real execution."""

    def test_render_beamer_with_paths_success(self, tmp_path):
        """Test successful beamer rendering using real execution."""
        compiler = _require_beamer_toolchain()
        config = RenderingConfig(output_dir=tmp_path)
        config.latex_compiler = compiler
        renderer = SlidesRenderer(config)

        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.pdf"

        result = renderer._render_beamer_with_paths(source, output, None, None)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 100

    @pytest.mark.timeout(90)
    def test_render_beamer_with_resource_paths(self, tmp_path):
        """Test beamer rendering with manuscript and figures directories using real execution."""
        compiler = _require_beamer_toolchain()
        config = RenderingConfig(output_dir=tmp_path)
        config.latex_compiler = compiler
        renderer = SlidesRenderer(config)

        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.pdf"
        manuscript_dir = tmp_path / "manuscript"
        figures_dir = tmp_path / "figures"
        manuscript_dir.mkdir()
        figures_dir.mkdir()

        result = renderer._render_beamer_with_paths(source, output, manuscript_dir, figures_dir)
        assert result == output
        assert output.exists()

    def test_render_beamer_pandoc_subprocess_failure(self, tmp_path):
        """Pandoc failures surface as RenderingError with beamer context."""
        config = RenderingConfig(output_dir=tmp_path)

        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.pdf"

        def fail_pandoc(*args, **kwargs):
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["pandoc"],
                stderr="simulated pandoc failure",
            )

        renderer = SlidesRenderer(config, process_runner=fail_pandoc)

        with pytest.raises(RenderingError, match="Failed to render beamer slides"):
            renderer._render_beamer_with_paths(source, output, None, None)


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


class TestSlidesRendererCore:
    """Test core slides renderer functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert slides_renderer.__name__ == "infrastructure.rendering.slides_renderer"

    def test_has_render_functions(self):
        """Test that module has render functions."""
        assert callable(slides_renderer.SlidesRenderer)
        assert callable(slides_renderer.split_long_slide_frames)


class TestSlidesMathHeaderInjection:
    """The Beamer renderer writes _slides_math_header.tex when preamble.md
    loads unicode-math, and passes it to Pandoc via -H. When unicode-math
    is absent, no header is written and no -H flag is added.
    """

    def _make_renderer(self, tmp_path):
        config = RenderingConfig(output_dir=tmp_path, slides_dir=tmp_path / "slides")
        (tmp_path / "slides").mkdir(exist_ok=True)
        return SlidesRenderer(config)

    def test_helper_writes_header_when_unicode_math_loaded(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text(
            "```latex\n\\usepackage{unicode-math}\n```\n",
            encoding="utf-8",
        )
        self._make_renderer(tmp_path)
        output_dir = tmp_path / "slides"
        header = write_slides_math_header(manuscript, output_dir)
        assert header is not None
        assert header.name == "_slides_math_header.tex"
        content = header.read_text(encoding="utf-8")
        assert "\\usepackage{unicode-math}" in content
        assert "\\setmathfont{latinmodern-math.otf}" in content

    def test_helper_returns_header_with_citation_fallbacks_when_no_preamble(self, tmp_path):
        """Even when ``preamble.md`` is missing, the helper writes a
        header that defines ``\\providecommand{\\citep}{...}`` fallbacks
        so slides survive natbib commands emitted for the combined PDF.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        assert header.name == "_slides_math_header.tex"
        content = header.read_text(encoding="utf-8")
        assert "\\providecommand{\\citep}" in content
        assert "\\providecommand{\\citet}" in content
        assert "\\providecommand{\\cref}" in content
        assert "\\providecommand{\\Cref}" in content
        # No math snippet expected (no preamble).
        assert "unicode-math" not in content

    def test_header_includes_manuscript_macros_with_unsafe_packages_filtered(self, tmp_path):
        r"""Manuscript macros land in the slide header rewritten as
        \providecommand; unsafe layout packages (geometry) are dropped while
        Beamer-safe ones (amsmath) survive."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text(
            "```latex\n\\usepackage{geometry}\n\\usepackage{amsmath}\n\\newcommand{\\calD}{\\mathcal{D}}\n```\n",
            encoding="utf-8",
        )
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        # Macro rewritten to providecommand and present.
        assert "\\providecommand{\\calD}" in content
        assert "\\newcommand{\\calD}" not in content
        # Safe package kept, layout machinery dropped.
        assert "\\usepackage{amsmath}" in content
        assert "geometry" not in content

    def test_helper_returns_header_with_citation_fallbacks_when_no_unicode_math(self, tmp_path):
        """When ``preamble.md`` exists but doesn't load unicode-math,
        the helper still writes a header for the natbib fallbacks.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text("```latex\n\\usepackage{geometry}\n```\n", encoding="utf-8")
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\providecommand{\\citep}" in content
        assert "unicode-math" not in content

    def test_helper_defines_proposition_and_hypothesis_environments(self, tmp_path):
        """Beamer's document class already defines \\theorem/\\lemma/\\corollary/
        \\definition natively; redeclaring them via \\newtheorem fails with
        "Command ... already defined" (regression: template_formal's
        auto-numbered-formalism manuscript hit exactly this on \\usepackage-free
        beamer compilation). Only the two environments beamer does not ship —
        proposition and hypothesis — should be declared here, and neither
        declaration should attempt to chain onto beamer's own theorem counter.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\newtheorem{proposition}{Proposition}" in content
        assert "\\newtheorem{hypothesis}{Hypothesis}" in content
        assert "\\newtheorem{theorem}" not in content
        assert "\\newtheorem{lemma}" not in content
        assert "\\newtheorem{corollary}" not in content
        assert "\\newtheorem{definition}" not in content

    def test_helper_declares_every_environment_the_extractor_skips(self, tmp_path):
        """The skip-set and the unconditional block must agree.

        ``write_slides_math_header`` drops a manuscript's ``\\newtheorem``
        declarations for environments it believes are "already declared or
        declared below/above". ``axiom`` and ``property`` sat in that set while
        being declared in neither place, so a manuscript using
        ``\\begin{property}`` had the declaration dropped on the way in and
        never restored -- beamer then failed with "Environment property
        undefined", and the render stage discarded the slide deck it had
        already written. Six of Part 1's decks were lost this way.

        This asserts the invariant rather than the two names: every environment
        the extractor refuses to carry over must be one beamer ships natively
        or one this header declares itself.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text(
            "```latex\n\\newtheorem{property}{Property}[section]\n\\newtheorem{axiom}{Axiom}[section]\n```\n",
            encoding="utf-8",
        )
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")

        beamer_native = {"theorem", "lemma", "corollary", "definition", "example", "fact"}
        skipped = beamer_native | {"proposition", "hypothesis", "remark", "axiom", "property"}
        undeclared = [env for env in sorted(skipped - beamer_native) if f"\\newtheorem{{{env}}}" not in content]
        assert not undeclared, (
            "the extractor skips these environments as already handled, but the "
            f"header declares none of them: {undeclared}"
        )

    def test_helper_provides_cleveref_range_fallbacks(self, tmp_path):
        """``\\cref``'s fallback takes one argument and cannot cover
        ``\\crefrange``, which takes two. Without its own fallback beamer
        stopped at "Undefined control sequence" and Part 1's formal-framework
        deck failed to compile.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\providecommand{\\crefrange}[2]" in content
        assert "\\providecommand{\\Crefrange}[2]" in content

    def test_helper_supplies_a_non_floating_algorithm_environment(self, tmp_path):
        """`algorithm` must be replaced, not carried over.

        Loading it under beamer defines the environment but leaves its float
        machinery (\\@float@Hx, \\float@makebox) undefined, so a deck using it
        dies one step later than it would have without the package -- still
        dead, and harder to diagnose. 14 \\begin{algorithm} blocks in one
        manuscript cost a 51-page deck this way.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text(
            "```latex\n\\usepackage{algorithm}\n\\usepackage{algpseudocode}\n```\n",
            encoding="utf-8",
        )
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\usepackage{algpseudocode}" in content
        assert "\\usepackage{algorithm}" not in content, (
            "the float package was carried over; it has no beamer implementation"
        )
        assert "\\newenvironment{algorithm}" in content
        # \providecommand is a no-op for \caption -- the caption package has
        # already defined it, and then refuses it outside a float.
        assert "\\renewcommand{\\caption}" in content

    def test_postprocessor_overrides_generated_codelisting_float(self):
        """The override lands after pandoc-crossref's preamble declaration."""
        tex = r"""\documentclass{beamer}
\newfloat{codelisting}{h}{lop}
\begin{document}
\begin{frame}
\begin{codelisting}
\caption[Short]{Long caption}
code
\end{codelisting}
\end{frame}
\end{document}
"""

        updated, changed = slides_renderer.make_codelisting_slide_safe(tex)

        assert changed == 1
        assert updated.index(r"\newfloat{codelisting}") < updated.index("Beamer-safe codelisting override")
        assert updated.index("Beamer-safe codelisting override") < updated.index(r"\begin{document}")
        assert r"\renewenvironment{codelisting}" in updated
        assert r"\renewcommand{\caption}[2][]" in updated
        assert r"\refstepcounter{codelisting}" in updated
        assert slides_renderer.make_codelisting_slide_safe(updated) == (updated, 0)

    def test_beamer_renames_compiled_pdf_to_output_file(self, tmp_path):
        """When compile_latex writes {stem}_slides.pdf, normalize to output_file."""
        source = tmp_path / "slides.md"
        source.write_text("# Slide 1\n", encoding="utf-8")
        output_file = tmp_path / "slides.pdf"

        def fake_run(cmd, *args, **kwargs):
            tex_path = Path(cmd[cmd.index("-o") + 1])
            tex_path.write_text("\\documentclass{beamer}\\begin{document}foo\\end{document}\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        def fake_compile(tex, out_dir, **kwargs):
            compiled = out_dir / f"{tex.stem}.pdf"
            compiled.write_bytes(b"%PDF-1.4 fake\n")
            return compiled

        renderer = SlidesRenderer(
            RenderingConfig(output_dir=tmp_path),
            process_runner=fake_run,
            latex_compile=fake_compile,
        )

        result = renderer._render_beamer_with_paths(source, output_file, manuscript_dir=None, figures_dir=None)
        assert result == output_file
        assert output_file.exists()
        assert not (tmp_path / "slides_slides.pdf").exists()

    def test_beamer_pandoc_cmd_includes_h_flag_when_math_required(self, tmp_path):
        """End-to-end wiring: pandoc receives -H _slides_math_header.tex."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text("```latex\n\\usepackage{unicode-math}\n```\n", encoding="utf-8")
        source = manuscript / "00_intro.md"
        source.write_text("# Slide 1\n\nHello.\n", encoding="utf-8")

        captured: dict[str, list[str]] = {}

        def fake_run(cmd, *args, **kwargs):
            captured["cmd"] = cmd
            tex_path = Path(cmd[cmd.index("-o") + 1])
            tex_path.write_text("\\documentclass{beamer}\\begin{document}foo\\end{document}\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        def fake_compile(tex, out_dir, **kwargs):
            compiled = out_dir / f"{tex.stem}.pdf"
            compiled.write_bytes(b"%PDF-1.4 fake\n")
            return compiled

        renderer = SlidesRenderer(
            RenderingConfig(output_dir=tmp_path),
            process_runner=fake_run,
            latex_compile=fake_compile,
        )

        output_file = tmp_path / "slides" / "00_intro_slides.pdf"
        result = renderer._render_beamer_with_paths(source, output_file, manuscript_dir=manuscript, figures_dir=None)
        assert result == output_file
        cmd = captured["cmd"]
        assert "-H" in cmd
        h_idx = cmd.index("-H")
        assert cmd[h_idx + 1].endswith("_slides_math_header.tex")
        assert Path(cmd[h_idx + 1]).exists()

    @pytest.mark.parametrize(
        ("slides_profile", "expected_aspect_ratio"),
        [
            ("archive", False),
            ("accessible", True),
        ],
    )
    def test_accessible_beamer_owns_widescreen_canvas_without_changing_archive(
        self,
        tmp_path,
        slides_profile,
        expected_aspect_ratio,
    ):
        """Only the opt-in projection profile requests Beamer's 16:9 canvas."""

        source = tmp_path / "00_intro.md"
        source.write_text("# Slide 1\n\nHello.\n", encoding="utf-8")
        (tmp_path / "slides").mkdir()
        captured: dict[str, list[str]] = {}

        def fake_run(cmd, *args, **kwargs):
            captured["cmd"] = cmd
            tex_path = Path(cmd[cmd.index("-o") + 1])
            tex_path.write_text("\\documentclass{beamer}\\begin{document}foo\\end{document}\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        def fake_compile(tex, out_dir, **kwargs):
            compiled = out_dir / f"{tex.stem}.pdf"
            compiled.write_bytes(b"%PDF-1.4 fake\n")
            return compiled

        renderer = SlidesRenderer(
            RenderingConfig(
                output_dir=tmp_path,
                slides_dir=tmp_path / "slides",
                slides_profile=slides_profile,
            ),
            process_runner=fake_run,
            latex_compile=fake_compile,
        )

        output_file = tmp_path / "slides" / "00_intro_slides.pdf"
        renderer._render_beamer_with_paths(source, output_file, manuscript_dir=None, figures_dir=None)

        aspect_ratio_arg = "--variable=aspectratio:169"
        assert (aspect_ratio_arg in captured["cmd"]) is expected_aspect_ratio

    def test_beamer_pandoc_cmd_includes_h_flag_for_citation_fallbacks(self, tmp_path):
        """The slides math header is now always written so natbib
        citation fallbacks are in scope, even when the preamble doesn't
        load unicode-math. Pandoc therefore always sees ``-H``.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text("```latex\n\\usepackage{geometry}\n```\n", encoding="utf-8")
        source = manuscript / "00_intro.md"
        source.write_text("# Slide 1\n", encoding="utf-8")

        captured: dict[str, list[str]] = {}

        def fake_run(cmd, *args, **kwargs):
            captured["cmd"] = cmd
            tex_path = Path(cmd[cmd.index("-o") + 1])
            tex_path.write_text("\\documentclass{beamer}\\begin{document}foo\\end{document}\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        def fake_compile_return_path(tex, out_dir, **kw):
            compiled = out_dir / f"{tex.stem}.pdf"
            compiled.write_bytes(b"%PDF-1.4 fake\n")
            return compiled

        renderer = SlidesRenderer(
            RenderingConfig(output_dir=tmp_path),
            process_runner=fake_run,
            latex_compile=fake_compile_return_path,
        )

        output_file = tmp_path / "slides" / "00_intro_slides.pdf"
        renderer._render_beamer_with_paths(source, output_file, manuscript_dir=manuscript, figures_dir=None)
        assert "-H" in captured["cmd"]
        h_idx = captured["cmd"].index("-H")
        header_path = Path(captured["cmd"][h_idx + 1])
        assert header_path.name == "_slides_math_header.tex"
        content = header_path.read_text(encoding="utf-8")
        assert "\\providecommand{\\citep}" in content


class TestSlidesRendererModule:
    """Test module-level functionality."""

    def test_module_imports(self):
        """Test module imports correctly."""
        assert slides_renderer.__name__ == "infrastructure.rendering.slides_renderer"

    def test_module_has_functions(self):
        """Test the module exports the renderer and pure frame helpers."""
        assert slides_renderer.SlidesRenderer is SlidesRenderer
        assert callable(slides_renderer.split_long_slide_frames)


class TestSlidesRendererClassFromSlidesRendererComprehensive:
    """Test SlidesRenderer class if it exists."""

    def test_class_exists(self):
        """Test SlidesRenderer exposes the real render contract."""
        assert slides_renderer.SlidesRenderer is SlidesRenderer
        assert callable(SlidesRenderer.render)

    def test_renderer_init(self, test_config):
        """Test renderer initialization with its required configuration."""
        renderer = SlidesRenderer(test_config)
        assert renderer.config is test_config


@pytest.mark.slow
class TestBeamerSlides:
    """Test Beamer slides rendering."""

    def test_render_beamer_exists(self):
        """Test render_beamer function exists."""
        assert callable(SlidesRenderer.render)

    def test_render_beamer(self, tmp_path, test_config):
        """Test rendering Beamer slides using real execution."""
        _require_beamer_toolchain()
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\n---\n\n# Slide 2")

        result = SlidesRenderer(test_config).render(md, output_format="beamer")

        assert result.is_file()
        assert result.stat().st_size > 1_000


@pytest.mark.slow
class TestRevealJsSlides:
    """Test reveal.js slides rendering."""

    def test_render_revealjs_exists(self):
        """Test render_revealjs function exists."""
        assert callable(SlidesRenderer.render)

    def test_render_revealjs(self, tmp_path, test_config):
        """Test rendering reveal.js slides."""
        if not shutil.which("pandoc"):
            pytest.skip("Pandoc not installed")
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\n---\n\n# Slide 2")

        result = SlidesRenderer(test_config).render(md, output_format="revealjs")

        assert result.is_file()
        assert "Slide 1" in result.read_text(encoding="utf-8")
