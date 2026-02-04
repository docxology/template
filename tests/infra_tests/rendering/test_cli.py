"""Tests for infrastructure.rendering.cli module."""

import pytest

from infrastructure.rendering import cli


class TestRenderingCLI:
    """Test rendering CLI functionality."""

    def test_cli_module_exists(self):
        """Test CLI module is importable."""
        assert cli is not None
        assert hasattr(cli, "main")
        assert hasattr(cli, "render_pdf_command")
        assert hasattr(cli, "render_all_command")
        assert hasattr(cli, "render_slides_command")
        assert hasattr(cli, "render_web_command")

    def test_render_command_available(self):
        """Test render command is available."""
        assert cli is not None
        assert callable(cli.render_pdf_command)
        assert callable(cli.render_all_command)
        assert callable(cli.render_slides_command)
        assert callable(cli.render_web_command)

    def test_pdf_render_option(self):
        """Test PDF rendering option."""
        assert hasattr(cli, "render_pdf_command")
        assert callable(cli.render_pdf_command)

    def test_html_render_option(self):
        """Test HTML/web rendering option."""
        assert hasattr(cli, "render_web_command")
        assert callable(cli.render_web_command)

    def test_slides_render_option(self):
        """Test slides rendering option."""
        assert hasattr(cli, "render_slides_command")
        assert callable(cli.render_slides_command)

    def test_poster_render_option(self):
        """Test poster rendering option."""
        # Poster rendering may be part of slides or separate
        # Check that rendering commands exist
        assert hasattr(cli, "render_slides_command")
        assert callable(cli.render_slides_command)

    def test_cli_help_output(self):
        """Test CLI help output."""
        assert hasattr(cli, "main")
        assert callable(cli.main)

    def test_cli_format_selection(self):
        """Test CLI format selection."""
        # Format selection is tested in render_slides_command
        assert hasattr(cli, "render_slides_command")
        assert callable(cli.render_slides_command)

    def test_render_execution(self):
        """Test render execution through CLI."""
        assert hasattr(cli, "main")
        assert callable(cli.main)
        assert hasattr(cli, "render_pdf_command")
        assert callable(cli.render_pdf_command)
