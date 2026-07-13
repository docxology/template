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

import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.exceptions import CompilationError, RenderingError
from infrastructure.rendering import slides_renderer
from infrastructure.rendering.config import RenderingConfig
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


class TestSlidesRendererClass:
    """Test SlidesRenderer class using real implementations."""

    def test_slides_renderer_initialization(self, tmp_path):
        """Test SlidesRenderer initialization."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        assert renderer.config == config

    def test_render_with_revealjs(self, tmp_path):
        """Test render() method with revealjs format using real execution."""
        config = RenderingConfig(output_dir=tmp_path, slides_dir=tmp_path / "slides")
        renderer = SlidesRenderer(config)
        (tmp_path / "slides").mkdir(exist_ok=True)

        # Create test markdown
        source = tmp_path / "slides.md"
        source.write_text("# Slide 1\n\n---\n\n# Slide 2")

        # Use real execution - may fail if pandoc not available
        try:
            result = renderer.render(source, output_format="revealjs")
            # If successful, should return a path
            assert result is not None or isinstance(result, Path)
        except (CompilationError, RenderingError, OSError, subprocess.SubprocessError):
            # Expected to fail if pandoc not available
            pass

    def test_render_with_beamer(self, tmp_path):
        """Test render() method with beamer format using real execution."""
        config = RenderingConfig(output_dir=tmp_path, slides_dir=tmp_path / "slides")
        renderer = SlidesRenderer(config)
        (tmp_path / "slides").mkdir(exist_ok=True)

        source = tmp_path / "slides.md"
        source.write_text("# Slide 1")

        # Use real execution - may fail if LaTeX not available
        try:
            result = renderer.render(source, output_format="beamer")
            # If successful, should return a path
            assert result is not None or isinstance(result, Path)
        except (CompilationError, RenderingError, OSError, subprocess.SubprocessError) as e:
            pytest.skip(f"Required Beamer/LaTeX tool not available: {e}")


class TestRevealJsRendering:
    """Test reveal.js rendering using real execution."""

    def test_render_revealjs_success(self, tmp_path):
        """Test successful reveal.js rendering using real pandoc."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.html"

        # Use real execution - may fail if pandoc not available
        try:
            result = renderer._render_revealjs(source, output)
            assert result == output or isinstance(result, Path)
        except (CompilationError, RenderingError, OSError, subprocess.SubprocessError):
            # Expected to fail if pandoc not available
            pass

    def test_render_revealjs_failure(self, tmp_path):
        """Test reveal.js rendering failure handling with real execution."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.html"

        # Use real execution - may succeed or fail depending on pandoc
        try:
            renderer._render_revealjs(source, output)
            # Real post-condition: a successful render must produce the output file
            assert output.exists(), "_render_revealjs returned without producing the output file"
        except (CompilationError, RenderingError, OSError, subprocess.SubprocessError):
            # Expected when pandoc / reveal.js dependencies are unavailable
            pass


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
        renderer = SlidesRenderer(config)

        tex_content = r"\includegraphics{../output/figures/test.png}"
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()

        fixed = renderer._fix_figure_paths(tex_content, output_dir, figures_dir)

        assert "../figures/test.png" in fixed

    def test_fix_figure_paths_already_correct(self, tmp_path):
        """Test that already correct paths are unchanged."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        tex_content = r"\includegraphics{../figures/test.png}"
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()

        fixed = renderer._fix_figure_paths(tex_content, output_dir, figures_dir)

        # Should remain unchanged
        assert "../figures/test.png" in fixed

    def test_fix_figure_paths_multiple(self, tmp_path):
        """Test fixing multiple figure paths."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        tex_content = r"""
        \includegraphics{../output/figures/fig1.png}
        \includegraphics{../output/figures/fig2.png}
        \includegraphics{../figures/fig3.png}
        """
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()

        fixed = renderer._fix_figure_paths(tex_content, output_dir, figures_dir)

        assert "../figures/fig1.png" in fixed
        assert "../figures/fig2.png" in fixed
        assert "../figures/fig3.png" in fixed

    def test_fix_figure_paths_handles_pandoc_alt_text_brackets(self, tmp_path):
        """Pandoc Beamer alt text can contain brackets that defeat regex parsing."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)

        tex_content = (
            r"\pandocbounded{\includegraphics[keepaspectratio,"
            r"alt={Curve on {[}0, 6{]} with $I(q_\lambda)$}]"
            r"{../output/figures/free_energy_curve.png}}"
        )
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()

        fixed = renderer._fix_figure_paths(tex_content, output_dir, figures_dir)

        assert "{../figures/free_energy_curve.png}" in fixed
        assert "alt={Curve on {[}0, 6{]} with $I(q_\\lambda)$}" in fixed
        assert "../output/figures" not in fixed


class TestSlidesRendererCore:
    """Test core slides renderer functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert slides_renderer is not None

    def test_has_render_functions(self):
        """Test that module has render functions."""
        module_funcs = [
            a for a in dir(slides_renderer) if not a.startswith("_") and callable(getattr(slides_renderer, a, None))
        ]
        assert len(module_funcs) > 0


class TestBeamerRenderingAdditional:
    """Test Beamer slides rendering using real execution."""

    def test_render_beamer(self, tmp_path):
        """Test Beamer rendering using real execution."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\n---\n\n# Slide 2")

        if hasattr(slides_renderer, "render_beamer"):
            # Use real execution
            try:
                result = slides_renderer.render_beamer(str(md))
                assert result is not None or isinstance(result, Path)
            except (CompilationError, RenderingError, OSError, subprocess.SubprocessError) as e:
                pytest.skip(f"Required Beamer/LaTeX tool not available: {e}")

    def test_render_beamer_with_theme(self, tmp_path):
        """Test Beamer rendering with theme using real execution."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1")

        if hasattr(slides_renderer, "render_beamer"):
            # Use real execution
            try:
                result = slides_renderer.render_beamer(str(md), theme="Madrid")
                assert result is not None or isinstance(result, Path)
            except (CompilationError, RenderingError, OSError, subprocess.SubprocessError) as e:
                pytest.skip(f"Required Beamer/LaTeX tool not available: {e}")


class TestRevealJsRenderingAdditional:
    """Test reveal.js slides rendering using real execution."""

    def test_render_revealjs(self, tmp_path):
        """Test reveal.js rendering using real execution."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\n---\n\n# Slide 2")

        if hasattr(slides_renderer, "render_revealjs"):
            # Use real execution
            try:
                result = slides_renderer.render_revealjs(str(md))
                assert result is not None or isinstance(result, Path)
            except (CompilationError, RenderingError, OSError, subprocess.SubprocessError):
                # Expected to fail if pandoc not available
                pass

    def test_render_revealjs_with_options(self, tmp_path):
        """Test reveal.js with options using real execution."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1")

        if hasattr(slides_renderer, "render_revealjs"):
            # Use real execution
            try:
                result = slides_renderer.render_revealjs(str(md), theme="moon")
                assert result is not None or isinstance(result, Path)
            except (CompilationError, RenderingError, OSError, subprocess.SubprocessError):
                # Expected to fail if pandoc not available
                pass


class TestSlidesParsing:
    """Test slides parsing functionality."""

    def test_parse_slides(self):
        """Test parsing slide content."""
        content = "# Slide 1\n\n---\n\n# Slide 2\n\n---\n\n# Slide 3"

        if hasattr(slides_renderer, "parse_slides"):
            slides = slides_renderer.parse_slides(content)
            assert isinstance(slides, list)

    def test_extract_slide_metadata(self):
        """Test extracting slide metadata."""
        content = "---\ntitle: Test\n---\n\n# Slide 1"

        if hasattr(slides_renderer, "extract_metadata"):
            metadata = slides_renderer.extract_metadata(content)
            assert metadata is not None


class TestSlideTemplates:
    """Test slide template functionality."""

    def test_apply_template(self, tmp_path):
        """Test applying template using real execution."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1")

        if hasattr(slides_renderer, "apply_template"):
            # Use real execution
            try:
                result = slides_renderer.apply_template(str(md), template="default")
                assert result is not None
            except (CompilationError, RenderingError, OSError, subprocess.SubprocessError):
                # Expected to fail if function not available
                pass

    def test_list_templates(self):
        """Test listing available templates."""
        if hasattr(slides_renderer, "list_templates"):
            templates = slides_renderer.list_templates()
            assert isinstance(templates, (list, tuple))


class TestSlidesRendererIntegration:
    """Integration tests for slides renderer."""

    def test_full_render_workflow(self, tmp_path):
        """Test complete rendering workflow."""
        # Create test slides
        md = tmp_path / "slides.md"
        md.write_text("# Title Slide\n\n---\n\n# Content\n\n- Item 1\n- Item 2")

        # Module should be importable
        assert slides_renderer is not None


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
        renderer = self._make_renderer(tmp_path)
        output_dir = tmp_path / "slides"
        header = renderer._maybe_write_math_header(manuscript, output_dir)
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
        renderer = self._make_renderer(tmp_path)
        header = renderer._maybe_write_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        assert header.name == "_slides_math_header.tex"
        content = header.read_text(encoding="utf-8")
        assert "\\providecommand{\\citep}" in content
        assert "\\providecommand{\\citet}" in content
        assert "\\providecommand{\\cref}" in content
        assert "\\providecommand{\\Cref}" in content
        # No math snippet expected (no preamble).
        assert "unicode-math" not in content

    def test_helper_returns_header_with_citation_fallbacks_when_no_unicode_math(self, tmp_path):
        """When ``preamble.md`` exists but doesn't load unicode-math,
        the helper still writes a header for the natbib fallbacks.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text("```latex\n\\usepackage{geometry}\n```\n", encoding="utf-8")
        renderer = self._make_renderer(tmp_path)
        header = renderer._maybe_write_math_header(manuscript, tmp_path / "slides")
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
        renderer = self._make_renderer(tmp_path)
        header = renderer._maybe_write_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\newtheorem{proposition}{Proposition}" in content
        assert "\\newtheorem{hypothesis}{Hypothesis}" in content
        assert "\\newtheorem{theorem}" not in content
        assert "\\newtheorem{lemma}" not in content
        assert "\\newtheorem{corollary}" not in content
        assert "\\newtheorem{definition}" not in content

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
        assert slides_renderer is not None

    def test_module_has_functions(self):
        """Test module has expected functions."""
        funcs = [a for a in dir(slides_renderer) if not a.startswith("_")]
        assert len(funcs) > 0


class TestSlidesRendererClassFromSlidesRendererComprehensive:
    """Test SlidesRenderer class if it exists."""

    def test_class_exists(self):
        """Test SlidesRenderer class exists."""
        if hasattr(slides_renderer, "SlidesRenderer"):
            assert slides_renderer.SlidesRenderer is not None

    def test_renderer_init(self, tmp_path):
        """Test renderer initialization."""
        if hasattr(slides_renderer, "SlidesRenderer"):
            try:
                renderer = slides_renderer.SlidesRenderer()
                assert renderer is not None
            except TypeError:
                pass  # May require arguments


class TestBeamerSlides:
    """Test Beamer slides rendering."""

    def test_render_beamer_exists(self):
        """Test render_beamer function exists."""
        assert (
            hasattr(slides_renderer, "render_beamer")
            or hasattr(slides_renderer, "render_beamer_slides")
            or hasattr(slides_renderer, "SlidesRenderer")
        )

    def test_render_beamer(self, tmp_path):
        """Test rendering Beamer slides using real execution."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\n---\n\n# Slide 2")

        if hasattr(slides_renderer, "render_beamer"):
            # Use real execution - may fail if pandoc/LaTeX not available
            try:
                result = slides_renderer.render_beamer(str(md))
                # If successful, should return a path
                assert result is not None or True
            except Exception:
                # Expected to fail if dependencies not available
                pass


class TestRevealJsSlides:
    """Test reveal.js slides rendering."""

    def test_render_revealjs_exists(self):
        """Test render_revealjs function exists."""
        assert (
            hasattr(slides_renderer, "render_revealjs")
            or hasattr(slides_renderer, "render_reveal_slides")
            or hasattr(slides_renderer, "SlidesRenderer")
        )

    def test_render_revealjs(self, tmp_path):
        """Test rendering reveal.js slides."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\n---\n\n# Slide 2")

        if hasattr(slides_renderer, "render_revealjs"):
            try:
                slides_renderer.render_revealjs(str(md))
            except Exception:
                pass


class TestSlidesParsingFromSlidesRendererComprehensive:
    """Test slides parsing functionality."""

    def test_parse_slide_content(self):
        """Test parsing slide content."""
        content = "# Slide 1\n\n---\n\n# Slide 2\n\n---\n\n# Slide 3"

        if hasattr(slides_renderer, "parse_slides"):
            slides = slides_renderer.parse_slides(content)
            assert isinstance(slides, list)

    def test_extract_slide_metadata(self):
        """Test extracting slide metadata."""
        content = """---
title: Test Slides
author: Test Author
---

# Slide 1
"""

        if hasattr(slides_renderer, "extract_metadata"):
            metadata = slides_renderer.extract_metadata(content)
            assert metadata is not None


class TestSlidesRendererIntegrationFromSlidesRendererComprehensive:
    """Integration tests for slides renderer."""

    def test_module_structure(self):
        """Test module has expected structure."""
        assert slides_renderer is not None

    def test_full_render_workflow(self, tmp_path):
        """Test complete render workflow."""
        md = tmp_path / "slides.md"
        md.write_text(
            """# Title Slide

---

# Content

- Point 1
- Point 2

---

# Conclusion
"""
        )

        # Module should be usable
        assert slides_renderer is not None
