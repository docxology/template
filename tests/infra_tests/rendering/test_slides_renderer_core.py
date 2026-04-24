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

import pytest

from infrastructure.rendering.slides_renderer import SlidesRenderer


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

    paragraphs = [
        f"Paragraph {i}: " + ("lorem ipsum dolor sit amet " * 12)
        for i in range(1, 151)
    ]
    long_md = tmp_path / "long_section.md"
    long_md.write_text("# A Very Long Section\n\n" + "\n\n".join(paragraphs) + "\n")

    renderer = SlidesRenderer(test_config)
    result = renderer.render(long_md, output_format="beamer")

    assert result.exists(), f"Expected PDF at {result}"
    pdf_bytes = result.stat().st_size
    assert pdf_bytes > 5_000, (
        f"Beamer PDF is {pdf_bytes} bytes — likely the 15-byte xelatex stub. "
        f"Did the allowframebreaks Lua filter run?"
    )

    log_path = result.with_suffix(".log")
    if log_path.exists():
        log_text = log_path.read_text(errors="ignore")
        assert "Error 256 (driver return code)" not in log_text, (
            "xelatex aborted with driver code 256 — overflowing frame not split."
        )
        assert "(job aborted, no legal \\end found)" not in log_text, (
            "xelatex aborted before reaching \\end{document}."
        )
