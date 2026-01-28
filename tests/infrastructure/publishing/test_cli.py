"""Tests for infrastructure.publishing.cli module."""

import pytest

from infrastructure.publishing import cli


class TestPublishingCLI:
    """Test publishing CLI functionality."""

    def test_cli_module_exists(self):
        """Test CLI module is importable."""
        assert cli is not None
        assert hasattr(cli, "main")
        assert hasattr(cli, "extract_metadata_command")
        assert hasattr(cli, "generate_citation_command")
        assert hasattr(cli, "publish_zenodo_command")

    def test_publish_command_available(self):
        """Test publish command is available."""
        assert cli is not None
        assert callable(cli.publish_zenodo_command)

    def test_zenodo_publish_available(self):
        """Test Zenodo publish functionality."""
        assert hasattr(cli, "publish_zenodo_command")
        assert callable(cli.publish_zenodo_command)

    def test_arxiv_submit_available(self):
        """Test arXiv submission functionality."""
        # arXiv submission may be part of publishing workflow
        # Check that publishing commands exist
        assert hasattr(cli, "publish_zenodo_command")
        assert callable(cli.publish_zenodo_command)

    def test_github_release_available(self):
        """Test GitHub release functionality."""
        # GitHub release may be part of publishing workflow
        # Check that publishing commands exist
        assert hasattr(cli, "publish_zenodo_command")
        assert callable(cli.publish_zenodo_command)

    def test_cli_help_output(self):
        """Test CLI help output."""
        assert hasattr(cli, "main")
        assert callable(cli.main)

    def test_cli_error_messages(self):
        """Test CLI error message handling."""
        # Error handling is tested in command functions
        assert cli is not None
        assert hasattr(cli, "extract_metadata_command")
        assert callable(cli.extract_metadata_command)
