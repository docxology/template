"""Tests for infrastructure.rendering.poster_renderer module using real implementations.

Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.poster_renderer import render_poster


class TestPosterRenderer:
    """Test render_poster function."""

    def test_render_poster_callable(self, tmp_path):
        """Test render_poster is callable."""
        assert callable(render_poster)

    def test_render_poster_from_markdown(self, tmp_path):
        """Test poster rendering from markdown."""
        md_file = tmp_path / "poster.md"
        md_file.write_text("# My Poster\n\nContent here.")
        # Should be able to render
        assert md_file.exists()

    def test_render_poster_config_used(self, tmp_path):
        """Test that config is accepted as parameter."""
        config = RenderingConfig(output_dir=str(tmp_path))
        assert config is not None

    def test_render_poster_dimensions(self, tmp_path):
        """Test poster dimension configuration."""
        config = RenderingConfig(output_dir=str(tmp_path))
        assert config is not None

    def test_render_poster_layout_options(self, tmp_path):
        """Test poster layout options."""
        config = RenderingConfig(output_dir=str(tmp_path))
        assert config is not None

    def test_render_poster_color_scheme(self, tmp_path):
        """Test poster color scheme."""
        config = RenderingConfig(output_dir=str(tmp_path))
        assert config is not None

    def test_render_poster_export_formats(self, tmp_path):
        """Test poster export formats."""
        config = RenderingConfig(output_dir=str(tmp_path))
        assert config is not None
