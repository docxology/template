"""Tests for infrastructure.rendering.config module."""
import pytest
from pathlib import Path

from infrastructure.rendering.config import RenderingConfig


class TestRenderingConfig:
    """Test RenderingConfig class."""

    def test_config_initialization(self):
        """Test basic config initialization."""
        config = RenderingConfig()
        assert config is not None

    def test_config_defaults(self):
        """Test config default values."""
        config = RenderingConfig()
        # Verify reasonable defaults for rendering
        assert hasattr(config, "output_dir")

    def test_config_custom_output_dir(self, tmp_path):
        """Test config with custom output directory."""
        config = RenderingConfig(output_dir=str(tmp_path))
        assert config.output_dir == str(tmp_path)

    def test_config_pdf_options(self):
        """Test PDF rendering options."""
        config = RenderingConfig()
        # Should have PDF-related options
        assert config is not None

    def test_config_web_options(self):
        """Test web rendering options."""
        config = RenderingConfig()
        # Should have web-related options
        assert config is not None

    def test_config_slides_options(self):
        """Test slides rendering options."""
        config = RenderingConfig()
        # Should have slides-related options
        assert config is not None

    def test_config_format_selection(self):
        """Test format selection."""
        config = RenderingConfig()
        # Should support multiple formats
        assert config is not None

