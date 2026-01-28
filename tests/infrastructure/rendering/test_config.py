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

    def test_from_env_no_vars_returns_defaults(self, monkeypatch):
        """Test that from_env() returns defaults when no env vars are set."""
        # Ensure relevant env vars are not set
        for var in ["MANUSCRIPT_DIR", "OUTPUT_DIR", "LATEX_COMPILER"]:
            monkeypatch.delenv(var, raising=False)

        config = RenderingConfig.from_env()

        assert config.manuscript_dir == "manuscript"
        assert config.output_dir == "output"
        assert config.latex_compiler == "xelatex"

    def test_from_env_reads_manuscript_dir(self, monkeypatch):
        """Test that from_env() reads MANUSCRIPT_DIR."""
        monkeypatch.setenv("MANUSCRIPT_DIR", "/custom/manuscript")

        config = RenderingConfig.from_env()

        assert config.manuscript_dir == "/custom/manuscript"

    def test_from_env_reads_figures_dir(self, monkeypatch):
        """Test that from_env() reads FIGURES_DIR."""
        monkeypatch.setenv("FIGURES_DIR", "/custom/figures")

        config = RenderingConfig.from_env()

        assert config.figures_dir == "/custom/figures"

    def test_from_env_reads_output_dir(self, monkeypatch):
        """Test that from_env() reads OUTPUT_DIR."""
        monkeypatch.setenv("OUTPUT_DIR", "/custom/output")

        config = RenderingConfig.from_env()

        assert config.output_dir == "/custom/output"

    def test_from_env_reads_pdf_dir(self, monkeypatch):
        """Test that from_env() reads PDF_DIR."""
        monkeypatch.setenv("PDF_DIR", "/custom/pdf")

        config = RenderingConfig.from_env()

        assert config.pdf_dir == "/custom/pdf"

    def test_from_env_reads_web_dir(self, monkeypatch):
        """Test that from_env() reads WEB_DIR."""
        monkeypatch.setenv("WEB_DIR", "/custom/web")

        config = RenderingConfig.from_env()

        assert config.web_dir == "/custom/web"

    def test_from_env_reads_slides_dir(self, monkeypatch):
        """Test that from_env() reads SLIDES_DIR."""
        monkeypatch.setenv("SLIDES_DIR", "/custom/slides")

        config = RenderingConfig.from_env()

        assert config.slides_dir == "/custom/slides"

    def test_from_env_reads_poster_dir(self, monkeypatch):
        """Test that from_env() reads POSTER_DIR."""
        monkeypatch.setenv("POSTER_DIR", "/custom/posters")

        config = RenderingConfig.from_env()

        assert config.poster_dir == "/custom/posters"

    def test_from_env_reads_latex_compiler(self, monkeypatch):
        """Test that from_env() reads LATEX_COMPILER."""
        monkeypatch.setenv("LATEX_COMPILER", "pdflatex")

        config = RenderingConfig.from_env()

        assert config.latex_compiler == "pdflatex"

    def test_from_env_reads_pandoc_path(self, monkeypatch):
        """Test that from_env() reads PANDOC_PATH."""
        monkeypatch.setenv("PANDOC_PATH", "/usr/local/bin/pandoc")

        config = RenderingConfig.from_env()

        assert config.pandoc_path == "/usr/local/bin/pandoc"

    def test_from_env_reads_template_dir(self, monkeypatch):
        """Test that from_env() reads TEMPLATE_DIR."""
        monkeypatch.setenv("TEMPLATE_DIR", "/custom/templates")

        config = RenderingConfig.from_env()

        assert config.template_dir == "/custom/templates"

    def test_from_env_reads_slide_theme(self, monkeypatch):
        """Test that from_env() reads SLIDE_THEME."""
        monkeypatch.setenv("SLIDE_THEME", "beamer")

        config = RenderingConfig.from_env()

        assert config.slide_theme == "beamer"

    def test_from_env_reads_web_theme(self, monkeypatch):
        """Test that from_env() reads WEB_THEME."""
        monkeypatch.setenv("WEB_THEME", "tufte")

        config = RenderingConfig.from_env()

        assert config.web_theme == "tufte"

    def test_from_env_reads_multiple_vars(self, monkeypatch):
        """Test that from_env() reads multiple environment variables correctly."""
        monkeypatch.setenv("MANUSCRIPT_DIR", "/project/manuscript")
        monkeypatch.setenv("OUTPUT_DIR", "/project/output")
        monkeypatch.setenv("LATEX_COMPILER", "lualatex")
        monkeypatch.setenv("SLIDE_THEME", "madrid")

        config = RenderingConfig.from_env()

        assert config.manuscript_dir == "/project/manuscript"
        assert config.output_dir == "/project/output"
        assert config.latex_compiler == "lualatex"
        assert config.slide_theme == "madrid"
        # Unset vars should still use defaults
        assert config.pandoc_path == "pandoc"
        assert config.web_theme == "simple"

    def test_from_env_partial_override(self, monkeypatch):
        """Test that from_env() correctly handles partial environment overrides."""
        # Only set a few vars
        monkeypatch.setenv("OUTPUT_DIR", "/override/output")

        # Make sure others are not set
        monkeypatch.delenv("MANUSCRIPT_DIR", raising=False)
        monkeypatch.delenv("LATEX_COMPILER", raising=False)

        config = RenderingConfig.from_env()

        # Overridden value
        assert config.output_dir == "/override/output"
        # Defaults for unset
        assert config.manuscript_dir == "manuscript"
        assert config.latex_compiler == "xelatex"
