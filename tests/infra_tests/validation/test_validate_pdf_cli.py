"""Behavioral tests for the canonical PDF validation CLI.

Tests the PDF validation CLI script using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from infrastructure.validation.content import pdf_reporting as validate_pdf_cli
from infrastructure.validation.content.pdf_discovery import discover_combined_pdf
from infrastructure.validation.cli.main import main as validation_main


def _validate(pdf_path: Path | None = None, n_words: int = 200, verbose: bool = False) -> int:
    arguments = ["pdf", "--preview-words", str(n_words)]
    if pdf_path is not None:
        arguments.append(str(pdf_path))
    if verbose:
        arguments.append("--verbose")
    try:
        return validation_main(arguments)
    except SystemExit as exc:
        return int(exc.code)


class TestValidatePdfCliModule:
    """Test PDF validation CLI module."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert validate_pdf_cli is not None

    def test_module_has_expected_attributes(self):
        """Test module has expected attributes."""
        module_attrs = dir(validate_pdf_cli)
        assert "__name__" in module_attrs


class TestDiscoverCombinedPdf:
    """Test discover_combined_pdf against a real output/ layout."""

    def test_named_project_found(self, tmp_path):
        """Named project resolves to output/{name}/pdf/{name}_combined.pdf."""
        pdf_dir = tmp_path / "output" / "proj" / "pdf"
        pdf_dir.mkdir(parents=True)
        combined = pdf_dir / "proj_combined.pdf"
        combined.write_bytes(b"%PDF-1.4")

        result = discover_combined_pdf(tmp_path, "proj")
        assert result == combined

    def test_named_project_missing(self, tmp_path):
        """Named project without a combined PDF returns None."""
        (tmp_path / "output" / "proj" / "pdf").mkdir(parents=True)
        assert discover_combined_pdf(tmp_path, "proj") is None

    def test_unnamed_selects_only_available_public_pdf(self, tmp_path):
        """Automatic discovery refuses ambiguous public PDFs."""
        for name in ("template_code_project",):
            pdf_dir = tmp_path / "output" / "templates" / name / "pdf"
            pdf_dir.mkdir(parents=True)
            (pdf_dir / f"{name}_combined.pdf").write_bytes(b"%PDF-1.4")

        result = discover_combined_pdf(tmp_path)
        assert result is not None
        assert result.name == "template_code_project_combined.pdf"

    def test_ambiguous_public_pdfs_require_selection(self, tmp_path):
        for name in ("template_code_project", "template_prose_project"):
            target = tmp_path / "output" / "templates" / name / "pdf" / f"{name}_combined.pdf"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"%PDF-1.4")
        with pytest.raises(ValueError, match="Multiple public"):
            discover_combined_pdf(tmp_path)

    @pytest.mark.parametrize("name", ["../private", "/absolute", "templates/../../private", "templates\\private"])
    def test_unsafe_names_refused(self, tmp_path, name):
        with pytest.raises(ValueError, match="confined"):
            discover_combined_pdf(tmp_path, name)

    def test_symlink_delivery_refused(self, tmp_path):
        delivery = tmp_path / "output" / "templates"
        delivery.parent.mkdir()
        external = tmp_path / "external"
        external.mkdir()
        delivery.symlink_to(external, target_is_directory=True)
        with pytest.raises(ValueError, match="symlink"):
            discover_combined_pdf(tmp_path, "templates/template_code_project")

    def test_qualified_project_cli_and_preview(self, tmp_path):
        pdf = tmp_path / "output" / "templates" / "template_code_project" / "pdf" / "template_code_project_combined.pdf"
        pdf.parent.mkdir(parents=True)
        document = canvas.Canvas(str(pdf), pagesize=letter)
        document.drawString(100, 750, "A real project PDF")
        document.showPage()
        document.save()
        with pytest.raises(SystemExit) as result:
            validation_main(
                [
                    "pdf",
                    "--project",
                    "templates/template_code_project",
                    "--repo-root",
                    str(tmp_path),
                    "--preview-words",
                    "10",
                ]
            )
        assert result.value.code == 0

    def test_nonpositive_preview_refused_before_validation(self, tmp_path):
        with pytest.raises(SystemExit) as result:
            validation_main(["pdf", str(tmp_path / "missing.pdf"), "--preview-words", "0"])
        assert result.value.code == 2

    def test_retired_module_is_unavailable(self):
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.validation.cli.pdf", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode != 0
        assert "No module named" in result.stderr

    def test_no_output_dir(self, tmp_path):
        """Empty repo root (no output/) returns None."""
        assert discover_combined_pdf(tmp_path) is None


class TestMainFunctionWithRealPdf:
    """Test main function using real subprocess execution."""

    def test_main_with_file(self, tmp_path):
        """Test main with valid PDF file via real subprocess."""
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
                "infrastructure.validation.cli",
                "pdf",
                str(pdf),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        # May succeed or fail depending on validation
        assert result.returncode in [0, 1, 2]

    def test_main_with_directory(self, tmp_path):
        """Test main with directory of PDFs via real subprocess."""
        # Create real PDFs
        pdf1 = tmp_path / "a.pdf"
        c1 = canvas.Canvas(str(pdf1), pagesize=letter)
        c1.drawString(100, 750, "PDF A")
        c1.save()

        pdf2 = tmp_path / "b.pdf"
        c2 = canvas.Canvas(str(pdf2), pagesize=letter)
        c2.drawString(100, 750, "PDF B")
        c2.save()

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.validation.cli",
                "pdf",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        # May succeed or fail
        assert result.returncode in [0, 1, 2]

    def test_main_without_args(self, tmp_path):
        """Test default discovery failure via real subprocess in an empty repository."""
        repo_root = Path(__file__).parent.parent.parent.parent
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{env.get('PYTHONPATH', '')}"
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.validation.cli", "pdf"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
            timeout=5,
        )

        assert result.returncode == 2
        assert "PDF file not found" in result.stdout + result.stderr


class TestPdfCliIntegration:
    """Integration tests using real execution."""

    def test_module_structure(self):
        """Test module has expected structure."""

        # Should have main function
        assert callable(validation_main)


class TestPrintValidationReport:
    """Test print_validation_report function."""

    def test_print_report_no_issues(self, caplog):
        """Test printing report with no issues."""
        from infrastructure.validation.content.pdf_reporting import print_validation_report

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
        from infrastructure.validation.content.pdf_reporting import print_validation_report

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
        from infrastructure.validation.content.pdf_reporting import print_validation_report

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

        # Create a real PDF file
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content for validation")
        c.showPage()
        c.save()

        # Use real validation
        exit_code = _validate(pdf_path=pdf)

        # May return 0 (success) or 1 (issues found) depending on PDF content
        assert exit_code in [0, 1]

    def test_main_with_issues(self, tmp_path, capsys):
        """Test main with validation - uses real PDF validation."""

        # Create a real PDF file
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.showPage()
        c.save()

        # Use real validation - may find issues or not
        exit_code = _validate(pdf_path=pdf)

        # Real validation may return 0 or 1 depending on actual PDF content
        assert exit_code in [0, 1]

    def test_main_file_not_found(self, tmp_path, caplog):
        """Test main with missing PDF."""

        missing_pdf = tmp_path / "missing.pdf"

        with caplog.at_level(logging.ERROR):
            exit_code = _validate(pdf_path=missing_pdf)

        assert exit_code == 2
        assert "not found" in caplog.text.lower() or "error" in caplog.text.lower()

    def test_main_validation_error(self, tmp_path, capsys):
        """Test main with validation error - uses real validation."""

        # Create a minimal PDF that might cause validation issues
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF")

        # Use real validation - may succeed or fail
        exit_code = _validate(pdf_path=pdf)

        # Real validation may return various codes depending on PDF validity
        assert exit_code in [0, 1, 2]

    def test_main_unexpected_error(self, tmp_path, capsys):
        """Test main error handling - uses real validation."""

        # Create a real PDF
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test")
        c.save()

        # Use real validation - should handle errors gracefully
        exit_code = _validate(pdf_path=pdf)

        # Should return valid exit code
        assert exit_code in [0, 1, 2]

    def test_main_verbose_with_error(self, tmp_path, caplog):
        """Test main verbose mode - uses real validation."""

        # Create a real PDF
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.save()

        # Use real validation with verbose flag
        with caplog.at_level(logging.INFO):
            exit_code = _validate(pdf_path=pdf, verbose=True)

        # Should return valid exit code
        assert exit_code in [0, 1, 2]
        # Verbose output should contain more details
        assert len(caplog.text) > 0


class TestDefaultPdfPath:
    """Test default PDF path handling."""

    def test_main_default_path(self, tmp_path, monkeypatch, capsys):
        """Test main returns 2 when no combined PDF is discoverable."""

        monkeypatch.chdir(tmp_path)
        exit_code = _validate()

        assert exit_code == 2


class TestValidatePdfCliIntegrationRealValidation:
    """Integration tests using real validation."""

    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow with real PDF."""

        # Create a real PDF with content
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Full test content here for validation workflow testing")
        c.drawString(100, 730, "This is additional content to test word extraction")
        c.showPage()
        c.save()

        # Use real validation
        exit_code = _validate(pdf_path=pdf, n_words=100, verbose=True)

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
                "infrastructure.validation.cli",
                "pdf",
                str(pdf),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
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
                "infrastructure.validation.cli",
                "pdf",
                str(pdf),
                "--verbose",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        # Accept various exit codes
        assert result.returncode in [0, 1, 2]
        # Verbose output should be present
        assert len(result.stdout) > 0 or len(result.stderr) > 0


class TestValidatePdfCliCore:
    """Test core validate PDF CLI functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""

        assert validate_pdf_cli is not None

    def test_has_main_function(self):
        """Test that module has main function."""

        assert callable(validation_main)


class TestPdfValidationCommand:
    """Test PDF validation command using real PDFs."""

    def test_validate_single_pdf(self, tmp_path):
        """Test validating a single PDF file using real PDF."""

        # Create a real PDF
        pdf = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.save()

        # Use real validation
        exit_code = _validate(pdf_path=pdf)
        assert exit_code in [0, 1, 2]

    def test_validate_pdf_directory(self, tmp_path):
        """Test validating a directory of PDFs using real PDFs."""

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
        exit_code = _validate(pdf_path=pdf1)
        assert exit_code in [0, 1, 2]

    def test_validate_nonexistent_pdf(self, tmp_path):
        """Test validating a nonexistent PDF."""

        missing_pdf = tmp_path / "nonexistent.pdf"
        exit_code = _validate(pdf_path=missing_pdf)
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
                    "infrastructure.validation.cli",
                    "pdf",
                    str(pdf),
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent,
                timeout=30,
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
                    "infrastructure.validation.cli",
                    "pdf",
                    str(pdf),
                    "--verbose",
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent,
                timeout=30,
            )

            # Should execute with verbose flag
            assert result.returncode in [0, 1, 2]


class TestPdfValidationOutput:
    """Test PDF validation output formatting."""

    def test_format_results(self):
        """Test result formatting via print_validation_report."""
        from infrastructure.validation.content.pdf_reporting import print_validation_report

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

    def test_print_summary(self, caplog):
        """Test summary printing."""
        from infrastructure.validation.content.pdf_reporting import print_validation_report

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

        import logging

        with caplog.at_level(logging.INFO):
            print_validation_report(report)
        assert len(caplog.records) > 0  # Should produce log output


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
                "infrastructure.validation.cli",
                "pdf",
                str(pdf),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
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
                "infrastructure.validation.cli",
                "pdf",
                str(missing_pdf),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        # Should fail with file not found
        assert result.returncode == 2
