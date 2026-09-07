"""Module-contract and smoke-render tests for ``SlidesRenderer``.

Checks the module surface (imports, exported renderer and pure frame
helpers) and runs the slow end-to-end Beamer / Reveal.js render smoke
tests through the public ``SlidesRenderer.render`` entry point.
"""

from __future__ import annotations

import shutil

import pytest

from infrastructure.rendering import slides_renderer
from infrastructure.rendering.slides_renderer import SlidesRenderer

from ._helpers import _require_beamer_toolchain


class TestSlidesRendererCore:
    """Test core slides renderer functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert slides_renderer.__name__ == "infrastructure.rendering.slides_renderer"

    def test_has_render_functions(self):
        """Test that module has render functions."""
        assert callable(slides_renderer.SlidesRenderer)
        assert callable(slides_renderer.split_long_slide_frames)


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
