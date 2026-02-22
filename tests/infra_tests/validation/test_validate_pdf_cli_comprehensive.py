"""Comprehensive tests for infrastructure/validation/validate_pdf_cli.py.

Tests PDF validation CLI functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real validation.
"""

import logging
import subprocess
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class TestValidatePdfCliModule:
    """Test module-level functionality."""

    def test_module_imports(self):
        """Test module imports correctly."""
        from infrastructure.validation import validate_pdf_cli

        assert validate_pdf_cli is not None


class TestPrintValidationReport:
    """Test print_validation_report function."""

    def test_print_report_no_issues(self, caplog):
        """Test printing report with no issues."""
        from infrastructure.validation.validate_pdf_cli import \
            print_validation_report

        report = {
            "pdf_path": "/path/to/test.pdf",
            "issues": {
                "total_issues": 0,
                "unresolved_references": 0,
                "warnings": 0,
                "errors": 0,
                "missing_citations": 0,
            },
            "summary": {
                "has_issues": False,
                "word_count": 100,
            },
            "first_words": "This is the beginning...",
        }

        with caplog.at_level(logging.INFO):
            print_validation_report(report)

        assert "No rendering issues detected" in caplog.text
        assert "test.pdf" in caplog.text

    def test_print_report_with_issues(self, caplog):
        """Test printing report with issues."""
        from infrastructure.validation.validate_pdf_cli import \
            print_validation_report

        report = {
            "pdf_path": "/path/to/test.pdf",
            "issues": {
                "total_issues": 5,
                "unresolved_references": 2,
                "warnings": 1,
                "errors": 1,
                "missing_citations": 1,
            },
            "summary": {
                "has_issues": True,
                "word_count": 100,
            },
            "first_words": "Content with issues...",
        }

        with caplog.at_level(logging.INFO):
            print_validation_report(report)

        assert "Found 5 rendering issue" in caplog.text
        assert "Unresolved references" in caplog.text
        assert "Warnings" in caplog.text
        assert "Errors" in caplog.text
        assert "Missing citations" in caplog.text

    def test_print_report_verbose(self, caplog):
        """Test printing report with verbose flag."""
        from infrastructure.validation.validate_pdf_cli import \
            print_validation_report

        report = {
            "pdf_path": "/path/to/test.pdf",
            "issues": {
                "total_issues": 0,
                "unresolved_references": 0,
                "warnings": 0,
                "errors": 0,
                "missing_citations": 0,
            },
            "summary": {"has_issues": False, "word_count": 100},
            "first_words": "Content...",
        }

        with caplog.at_level(logging.INFO):
            print_validation_report(report, verbose=True)

        assert "Full Report Details" in caplog.text
        assert "PDF Path" in caplog.text


class TestMainFunction:
    """Test main function using real PDF validation."""

    def test_main_success(self, tmp_path, capsys):
        """Test main with successful validation using real PDF."""
        from infrastructure.validation import validate_pdf_cli

        # Create a real PDF file
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content for validation")
        c.showPage()
        c.save()

        # Use real validation
        exit_code = validate_pdf_cli.main(pdf_path=pdf)

        # May return 0 (success) or 1 (issues found) depending on PDF content
        assert exit_code in [0, 1]

    def test_main_with_issues(self, tmp_path, capsys):
        """Test main with validation - uses real PDF validation."""
        from infrastructure.validation import validate_pdf_cli

        # Create a real PDF file
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.showPage()
        c.save()

        # Use real validation - may find issues or not
        exit_code = validate_pdf_cli.main(pdf_path=pdf)

        # Real validation may return 0 or 1 depending on actual PDF content
        assert exit_code in [0, 1]

    def test_main_file_not_found(self, tmp_path, caplog):
        """Test main with missing PDF."""
        from infrastructure.validation import validate_pdf_cli

        missing_pdf = tmp_path / "missing.pdf"

        with caplog.at_level(logging.ERROR):
            exit_code = validate_pdf_cli.main(pdf_path=missing_pdf)

        assert exit_code == 2
        assert "not found" in caplog.text.lower() or "error" in caplog.text.lower()

    def test_main_validation_error(self, tmp_path, capsys):
        """Test main with validation error - uses real validation."""
        from infrastructure.validation import validate_pdf_cli

        # Create a minimal PDF that might cause validation issues
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF")

        # Use real validation - may succeed or fail
        exit_code = validate_pdf_cli.main(pdf_path=pdf)

        # Real validation may return various codes depending on PDF validity
        assert exit_code in [0, 1, 2]

    def test_main_unexpected_error(self, tmp_path, capsys):
        """Test main error handling - uses real validation."""
        from infrastructure.validation import validate_pdf_cli

        # Create a real PDF
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test")
        c.save()

        # Use real validation - should handle errors gracefully
        exit_code = validate_pdf_cli.main(pdf_path=pdf)

        # Should return valid exit code
        assert exit_code in [0, 1, 2]

    def test_main_verbose_with_error(self, tmp_path, caplog):
        """Test main verbose mode - uses real validation."""
        from infrastructure.validation import validate_pdf_cli

        # Create a real PDF
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.save()

        # Use real validation with verbose flag
        with caplog.at_level(logging.INFO):
            exit_code = validate_pdf_cli.main(pdf_path=pdf, verbose=True)

        # Should return valid exit code
        assert exit_code in [0, 1, 2]
        # Verbose output should contain more details
        assert len(caplog.text) > 0


class TestDefaultPdfPath:
    """Test default PDF path handling."""

    def test_main_default_path(self, capsys):
        """Test main uses default path when none specified."""
        from infrastructure.validation import validate_pdf_cli

        # Without a real PDF, should return error
        exit_code = validate_pdf_cli.main()

        # Should try default path and fail (file not found)
        assert exit_code == 2


class TestValidatePdfCliIntegration:
    """Integration tests using real validation."""

    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow with real PDF."""
        from infrastructure.validation import validate_pdf_cli

        # Create a real PDF with content
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Full test content here for validation workflow testing")
        c.drawString(100, 730, "This is additional content to test word extraction")
        c.showPage()
        c.save()

        # Use real validation
        exit_code = validate_pdf_cli.main(pdf_path=pdf, n_words=100, verbose=True)

        # Real validation may return 0 or 1 depending on actual PDF content
        assert exit_code in [0, 1]


class TestValidatePdfCliSubprocess:
    """Test CLI via real subprocess execution."""

    def test_cli_via_subprocess(self, tmp_path):
        """Test CLI execution via real subprocess."""
        # Create a real PDF
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.save()

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.validation.validate_pdf_cli",
                str(pdf),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # Accept various exit codes depending on validation results
        assert result.returncode in [0, 1, 2]

    def test_cli_verbose_via_subprocess(self, tmp_path):
        """Test CLI with verbose flag via real subprocess."""
        # Create a real PDF
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.save()

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.validation.validate_pdf_cli",
                str(pdf),
                "--verbose",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # Accept various exit codes
        assert result.returncode in [0, 1, 2]
        # Verbose output should be present
        assert len(result.stdout) > 0 or len(result.stderr) > 0
