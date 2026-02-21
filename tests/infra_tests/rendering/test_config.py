"""Tests for infrastructure.rendering.config module."""

import os
from pathlib import Path

import pytest

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
        assert config.output_dir == "output"
        assert config.manuscript_dir == "manuscript"
        assert config.latex_compiler == "xelatex"
        assert config.pandoc_path == "pandoc"
        assert config.slide_theme == "metropolis"
        assert config.web_theme == "simple"

    def test_config_custom_output_dir(self, tmp_path):
        """Test config with custom output directory."""
        config = RenderingConfig(output_dir=str(tmp_path))
        assert config.output_dir == str(tmp_path)

    def test_config_pdf_options(self):
        """Test PDF rendering options."""
        config = RenderingConfig()
        # Should have PDF-related options
        assert hasattr(config, "pdf_dir")
        assert config.pdf_dir == "output/pdf"

    def test_config_web_options(self):
        """Test web rendering options."""
        config = RenderingConfig()
        # Should have web-related options
        assert hasattr(config, "web_dir")
        assert hasattr(config, "web_theme")

    def test_config_slides_options(self):
        """Test slides rendering options."""
        config = RenderingConfig()
        # Should have slides-related options
        assert hasattr(config, "slides_dir")
        assert hasattr(config, "slide_theme")

    def test_config_format_selection(self):
        """Test format selection."""
        config = RenderingConfig()
        # Should support multiple formats
        assert hasattr(config, "pdf_dir")
        assert hasattr(config, "web_dir")
        assert hasattr(config, "slides_dir")
        assert hasattr(config, "poster_dir")


class TestRenderingConfigFromEnv:
    """Test RenderingConfig.from_env() method."""

    def test_from_env_no_vars_returns_defaults(self):
        """Test that from_env() returns defaults when no env vars are set."""
        # Ensure relevant env vars are not set
        config = RenderingConfig.from_env({})

        assert config.manuscript_dir == "manuscript"
        assert config.output_dir == "output"
        assert config.latex_compiler == "xelatex"

    def test_from_env_reads_manuscript_dir(self):
        """Test that from_env() reads MANUSCRIPT_DIR."""
        config = RenderingConfig.from_env({"MANUSCRIPT_DIR": "/custom/manuscript"})

        assert config.manuscript_dir == "/custom/manuscript"

    def test_from_env_reads_figures_dir(self):
        """Test that from_env() reads FIGURES_DIR."""
        config = RenderingConfig.from_env({"FIGURES_DIR": "/custom/figures"})

        assert config.figures_dir == "/custom/figures"

    def test_from_env_reads_output_dir(self):
        """Test that from_env() reads OUTPUT_DIR."""
        config = RenderingConfig.from_env({"OUTPUT_DIR": "/custom/output"})

        assert config.output_dir == "/custom/output"

    def test_from_env_reads_pdf_dir(self):
        """Test that from_env() reads PDF_DIR."""
        config = RenderingConfig.from_env({"PDF_DIR": "/custom/pdf"})

        assert config.pdf_dir == "/custom/pdf"

    def test_from_env_reads_web_dir(self):
        """Test that from_env() reads WEB_DIR."""
        config = RenderingConfig.from_env({"WEB_DIR": "/custom/web"})

        assert config.web_dir == "/custom/web"

    def test_from_env_reads_slides_dir(self):
        """Test that from_env() reads SLIDES_DIR."""
        config = RenderingConfig.from_env({"SLIDES_DIR": "/custom/slides"})

        assert config.slides_dir == "/custom/slides"

    def test_from_env_reads_poster_dir(self):
        """Test that from_env() reads POSTER_DIR."""
        config = RenderingConfig.from_env({"POSTER_DIR": "/custom/posters"})

        assert config.poster_dir == "/custom/posters"

    def test_from_env_reads_latex_compiler(self):
        """Test that from_env() reads LATEX_COMPILER."""
        config = RenderingConfig.from_env({"LATEX_COMPILER": "pdflatex"})

        assert config.latex_compiler == "pdflatex"

    def test_from_env_reads_pandoc_path(self):
        """Test that from_env() reads PANDOC_PATH."""
        config = RenderingConfig.from_env({"PANDOC_PATH": "/usr/local/bin/pandoc"})

        assert config.pandoc_path == "/usr/local/bin/pandoc"

    def test_from_env_reads_template_dir(self):
        """Test that from_env() reads TEMPLATE_DIR."""
        config = RenderingConfig.from_env({"TEMPLATE_DIR": "/custom/templates"})

        assert config.template_dir == "/custom/templates"

    def test_from_env_reads_slide_theme(self):
        """Test that from_env() reads SLIDE_THEME."""
        config = RenderingConfig.from_env({"SLIDE_THEME": "beamer"})

        assert config.slide_theme == "beamer"

    def test_from_env_reads_web_theme(self):
        """Test that from_env() reads WEB_THEME."""
        config = RenderingConfig.from_env({"WEB_THEME": "tufte"})

        assert config.web_theme == "tufte"

    def test_from_env_reads_multiple_vars(self):
        """Test that from_env() reads multiple environment variables correctly."""
        env = {
            "MANUSCRIPT_DIR": "/project/manuscript",
            "OUTPUT_DIR": "/project/output",
            "LATEX_COMPILER": "lualatex",
            "SLIDE_THEME": "madrid",
        }
        config = RenderingConfig.from_env(env)

        assert config.manuscript_dir == "/project/manuscript"
        assert config.output_dir == "/project/output"
        assert config.latex_compiler == "lualatex"
        assert config.slide_theme == "madrid"
        # Unset vars should still use defaults
        assert config.pandoc_path == "pandoc"
        assert config.web_theme == "simple"

    def test_from_env_partial_override(self):
        """Test that from_env() correctly handles partial environment overrides."""
        env = {"OUTPUT_DIR": "/override/output"}
        config = RenderingConfig.from_env(env)

        # Overridden value
        assert config.output_dir == "/override/output"
        # Defaults for unset
        assert config.manuscript_dir == "manuscript"
        assert config.latex_compiler == "xelatex"
