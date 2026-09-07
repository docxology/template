"""Real-rendering-path tests for ``SlidesRenderer``.

Focuses on regressions in the Beamer rendering path — in particular
:func:`test_long_section_renders_via_allowframebreaks`, which verifies the
``_beamer_allowframebreaks.lua`` filter prevents the ``Overfull \\vbox …
Error 256`` failure mode that previously left a 15-byte stub PDF on disk —
plus the direct ``_render_revealjs`` / ``_render_beamer_with_paths`` paths.

Follows the No Mocks Policy — tests invoke the real Pandoc + xelatex
pipeline via ``SlidesRenderer.render`` and inspect the resulting PDF and
``.log`` files on disk.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest
from pypdf import PdfReader

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer

from ._helpers import _require_beamer_toolchain


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
