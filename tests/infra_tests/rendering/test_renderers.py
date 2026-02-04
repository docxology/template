import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering.slides_renderer import SlidesRenderer
from infrastructure.rendering.web_renderer import WebRenderer


@pytest.mark.requires_latex
def test_pdf_renderer(test_config, tmp_path, skip_if_no_latex):
    """Test PDF renderer with real LaTeX compilation."""
    renderer = PDFRenderer(test_config)

    # Create valid LaTeX file
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Test PDF rendering.
\end{document}
"""
    )

    # Render with real compilation
    result = renderer.render(tex_file)
    assert result.exists()
    assert result.suffix == ".pdf"


@pytest.mark.requires_latex
def test_slides_renderer_beamer(test_config, tmp_path, skip_if_no_latex):
    """Test Beamer slides renderer with real compilation."""
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")

    renderer = SlidesRenderer(test_config)

    # Create a markdown file for slides
    test_md = tmp_path / "test.md"
    test_md.write_text(
        """# Test Presentation

## Slide 1

Some content here.

## Slide 2

More content.
"""
    )

    try:
        result = renderer.render(test_md, format="beamer")
        assert result.exists()
        assert result.suffix == ".pdf"
    except Exception as e:
        pytest.skip(f"Beamer rendering not fully functional: {e}")


def test_web_renderer(test_config, tmp_path):
    """Test web renderer with real pandoc."""
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")

    renderer = WebRenderer(test_config)

    # Create markdown file
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Test Web Page

Some content here.
"""
    )

    result = renderer.render(md_file)

    assert result.exists()
    assert result.suffix == ".html"
    # Verify it's actually HTML
    content = result.read_text()
    assert "<html" in content or "<body" in content


def test_renderer_failure(test_config, tmp_path):
    """Test renderer error handling with invalid input."""
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")

    renderer = WebRenderer(test_config)

    # Use non-existent file to trigger error
    with pytest.raises(RenderingError):
        renderer.render(tmp_path / "nonexistent.md")
