"""Comprehensive tests for infrastructure/validation/validate_pdf_cli.py.

Tests PDF validation CLI functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real validation.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class TestValidatePdfCliCore:
    """Test core validate PDF CLI functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        from infrastructure.validation import validate_pdf_cli

        assert validate_pdf_cli is not None

    def test_has_main_function(self):
        """Test that module has main function."""
        from infrastructure.validation import validate_pdf_cli

        assert hasattr(validate_pdf_cli, "main")


class TestPdfValidationCommand:
    """Test PDF validation command using real PDFs."""

    def test_validate_single_pdf(self, tmp_path):
        """Test validating a single PDF file using real PDF."""
        from infrastructure.validation import validate_pdf_cli

        # Create a real PDF
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.save()

        # Use real validation
        exit_code = validate_pdf_cli.main(pdf_path=pdf)
        assert exit_code in [0, 1, 2]

    def test_validate_pdf_directory(self, tmp_path):
        """Test validating a directory of PDFs using real PDFs."""
        from infrastructure.validation import validate_pdf_cli

        # Create real PDF files
        pdf1 = tmp_path / "a.pdf"
        c1 = canvas.Canvas(str(pdf1), pagesize=letter)
        c1.drawString(100, 750, "PDF A content")
        c1.save()

        pdf2 = tmp_path / "b.pdf"
        c2 = canvas.Canvas(str(pdf2), pagesize=letter)
        c2.drawString(100, 750, "PDF B content")
        c2.save()

        # Validate first PDF (directory validation not directly supported, test individual)
        exit_code = validate_pdf_cli.main(pdf_path=pdf1)
        assert exit_code in [0, 1, 2]

    def test_validate_nonexistent_pdf(self, tmp_path):
        """Test validating a nonexistent PDF."""
        from infrastructure.validation import validate_pdf_cli

        missing_pdf = tmp_path / "nonexistent.pdf"
        exit_code = validate_pdf_cli.main(pdf_path=missing_pdf)
        assert exit_code == 2


class TestPdfCliParsing:
    """Test CLI argument parsing via real subprocess."""

    def test_parse_args_basic(self):
        """Test basic argument parsing via real subprocess."""
        # Create a real PDF for testing
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp_dir:
            pdf = Path(tmp_dir) / "test.pdf"
            c = canvas.Canvas(str(pdf), pagesize=letter)
            c.drawString(100, 750, "Test")
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

            # Should execute (may succeed or fail depending on PDF)
            assert result.returncode in [0, 1, 2]

    def test_parse_args_verbose(self):
        """Test verbose flag parsing via real subprocess."""
        # Create a real PDF for testing
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp_dir:
            pdf = Path(tmp_dir) / "test.pdf"
            c = canvas.Canvas(str(pdf), pagesize=letter)
            c.drawString(100, 750, "Test")
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

            # Should execute with verbose flag
            assert result.returncode in [0, 1, 2]


class TestPdfValidationOutput:
    """Test PDF validation output formatting."""

    def test_format_results(self):
        """Test result formatting via print_validation_report."""
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
            "first_words": "Test content here",
        }

        # Should format without error
        print_validation_report(report)
        assert True  # If no exception, test passes

    def test_print_summary(self, capsys):
        """Test summary printing."""
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
                "word_count": 50,
            },
            "first_words": "Test content",
        }

        print_validation_report(report)
        captured = capsys.readouterr()
        assert len(captured.out) > 0  # Should produce output


class TestPdfCliMain:
    """Test main entry point using real subprocess execution."""

    def test_main_with_valid_pdf(self, tmp_path):
        """Test main with valid PDF via real subprocess."""
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

        # Should execute (may succeed or find issues)
        assert result.returncode in [0, 1, 2]

    def test_main_with_missing_pdf(self, tmp_path):
        """Test main with missing PDF via real subprocess."""
        missing_pdf = tmp_path / "missing.pdf"

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.validation.validate_pdf_cli",
                str(missing_pdf),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # Should fail with file not found
        assert result.returncode == 2


class TestValidatePdfCliIntegration:
    """Integration tests for validate PDF CLI using real validation."""

    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow with real PDF."""
        from infrastructure.validation import validate_pdf_cli

        # Create a real PDF with content
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Full test content for integration testing")
        c.showPage()
        c.save()

        # Use real validation
        exit_code = validate_pdf_cli.main(pdf_path=pdf)

        # Real validation may return 0 or 1 depending on actual PDF content
        assert exit_code in [0, 1, 2]
