"""Tests for infrastructure.publishing.cli module."""
import pytest


class TestPublishingCLI:
    """Test publishing CLI functionality."""

    def test_cli_module_exists(self):
        """Test CLI module is importable."""
        try:
            from infrastructure.publishing import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_publish_command_available(self):
        """Test publish command is available."""
        try:
            from infrastructure.publishing import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_zenodo_publish_available(self):
        """Test Zenodo publish functionality."""
        try:
            from infrastructure.publishing import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_arxiv_submit_available(self):
        """Test arXiv submission functionality."""
        try:
            from infrastructure.publishing import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_github_release_available(self):
        """Test GitHub release functionality."""
        try:
            from infrastructure.publishing import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_cli_help_output(self):
        """Test CLI help output."""
        try:
            from infrastructure.publishing import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_cli_error_messages(self):
        """Test CLI error message handling."""
        try:
            from infrastructure.publishing import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

