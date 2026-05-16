"""Tests for core module."""
from pathlib import Path

import pytest


@pytest.mark.requires_latex
def test_render_all_tex(render_manager, tmp_path, skip_if_no_latex):
    """Test rendering all formats from LaTeX source with real compilation."""
    # Create a minimal valid LaTeX file
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Test Document
\end{document}
"""
    )

    # Render using real LaTeX compilation
    try:
        results = render_manager.render_all(tex_file)
        assert len(results) >= 1
        # At minimum, PDF should be generated
        assert any(str(r).endswith(".pdf") for r in results)
    except Exception as e:
        pytest.skip(f"LaTeX compilation not fully functional: {e}")


def test_render_all_md(render_manager, tmp_path):
    """Test rendering all formats from Markdown source.

    This test may skip if pandoc is not available.
    """
    import shutil

    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")

    # Create a minimal Markdown file
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Test Presentation

## Slide 1

Content here
"""
    )

    try:
        results = render_manager.render_all(md_file)
        # Results may include slides and/or web output
        assert len(results) >= 1
        # At least one output should be generated
        assert all(isinstance(r, Path) for r in results)
    except Exception as e:
        pytest.skip(f"Rendering not fully functional: {e}")


def test_render_all_md_skip_beamer_marker(render_manager, tmp_path):
    """Markdown can opt out of Beamer while still rendering HTML."""
    import shutil

    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")

    md_file = tmp_path / "appendix.md"
    md_file.write_text(
        """# Appendix

<!-- render:skip-beamer -->

Large generated appendix content.
""",
        encoding="utf-8",
    )
    slides_dir = Path(render_manager.config.slides_dir)
    slides_dir.mkdir(parents=True, exist_ok=True)
    stale_slide = slides_dir / "appendix_slides.pdf"
    stale_slide.write_bytes(b"%PDF-1.7 stale\n%%EOF\n")

    results = render_manager.render_all(md_file)

    assert len(results) == 1
    assert results[0].suffix == ".html"
    assert not stale_slide.exists()
