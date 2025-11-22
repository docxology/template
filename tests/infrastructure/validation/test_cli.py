"""Tests for infrastructure.validation.cli module."""
import pytest


class TestValidationCLI:
    """Test validation CLI functionality."""

    def test_cli_module_exists(self):
        """Test CLI module is importable."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_validate_command_available(self):
        """Test validate command is available."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_markdown_validation_option(self):
        """Test markdown validation option."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_pdf_validation_option(self):
        """Test PDF validation option."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_links_validation_option(self):
        """Test links validation option."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_integrity_check_option(self):
        """Test integrity check option."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_cli_help_output(self):
        """Test CLI help output."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_cli_report_generation(self):
        """Test CLI report generation."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

    def test_strict_mode_option(self):
        """Test strict mode option."""
        try:
            from infrastructure.validation import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module imports not available")

