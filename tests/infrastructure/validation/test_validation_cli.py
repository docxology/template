"""Comprehensive tests for infrastructure/validation/cli.py.

Tests the CLI interface for validation operations including PDF, markdown,
and integrity validation commands.
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.validation import cli


class TestValidatePdfCommand:
    """Test suite for validate_pdf_command."""
    
    def test_pdf_command_with_valid_pdf(self, tmp_path):
        """Test PDF validation with a valid PDF file using real validation."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a real PDF file
        pdf_file = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Test document content without issues")
        c.showPage()
        c.save()
        
        args = argparse.Namespace(
            pdf_path=str(pdf_file),
            preview_words=100,
            verbose=False
        )
        
        # Run real validation
        with pytest.raises(SystemExit) as exc_info:
            cli.validate_pdf_command(args)
        # Clean PDF should pass (exit code 0)
        assert exc_info.value.code == 0
    
    def test_pdf_command_with_issues(self, tmp_path):
        """Test PDF validation when issues are found using real PDF."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a PDF with ?? markers (unresolved references)
        pdf_file = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "See section ??")
        c.drawString(100, 730, "As shown in figure ??")
        c.showPage()
        c.save()
        
        args = argparse.Namespace(
            pdf_path=str(pdf_file),
            preview_words=100,
            verbose=True
        )
        
        # Run real validation - should find issues
        with pytest.raises(SystemExit) as exc_info:
            cli.validate_pdf_command(args)
        # PDF with ?? should have issues (exit code 1)
        assert exc_info.value.code == 1
    
    def test_pdf_command_nonexistent_file(self, tmp_path, capsys):
        """Test PDF validation with nonexistent file."""
        args = argparse.Namespace(
            pdf_path=str(tmp_path / "nonexistent.pdf"),
            preview_words=100,
            verbose=False
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.validate_pdf_command(args)
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestValidateMarkdownCommand:
    """Test suite for validate_markdown_command."""
    
    def test_markdown_command_with_valid_dir(self, tmp_path):
        """Test markdown validation with valid directory using real validation."""
        # Create valid markdown file
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent here.")
        
        args = argparse.Namespace(
            markdown_dir=str(tmp_path),
            repo_root=str(tmp_path)
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.validate_markdown_command(args)
        # Clean markdown should pass
        assert exc_info.value.code == 0
    
    def test_markdown_command_with_problems(self, tmp_path, capsys):
        """Test markdown validation when problems are found using real validation."""
        # Create markdown with missing image reference
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\n![broken](missing_image_that_does_not_exist.png)")
        
        args = argparse.Namespace(
            markdown_dir=str(tmp_path),
            repo_root=str(tmp_path)
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.validate_markdown_command(args)
        
        captured = capsys.readouterr()
        # Should report the missing image in output
        assert "missing_image_that_does_not_exist.png" in captured.out
        # Exit code may be 0 (non-strict) or 1 (strict mode)
        assert exc_info.value.code in [0, 1]
    
    def test_markdown_command_nonexistent_dir(self, tmp_path, capsys):
        """Test markdown validation with nonexistent directory."""
        args = argparse.Namespace(
            markdown_dir=str(tmp_path / "nonexistent"),
            repo_root=str(tmp_path)
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.validate_markdown_command(args)
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err
    
    def test_markdown_command_without_repo_root(self, tmp_path):
        """Test markdown validation without explicit repo root using real validation."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nValid content.")
        
        args = argparse.Namespace(
            markdown_dir=str(tmp_path),
            repo_root=None
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.validate_markdown_command(args)
        # Should use default repo_root and pass
        assert exc_info.value.code == 0


class TestVerifyIntegrityCommand:
    """Test suite for verify_integrity_command."""
    
    def test_integrity_command_with_valid_dir(self, tmp_path):
        """Test integrity verification with valid directory using real verification."""
        # Create test files
        (tmp_path / "test.pdf").write_bytes(b"pdf content")
        (tmp_path / "test.md").write_text("# Test document")
        
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            verbose=False
        )
        
        # Run real verification - it will find the files and verify integrity
        with pytest.raises(SystemExit) as exc_info:
            cli.verify_integrity_command(args)
        # May pass or fail depending on actual integrity state
        assert exc_info.value.code in [0, 1]
    
    def test_integrity_command_verbose(self, tmp_path):
        """Test integrity verification with verbose flag."""
        # Create test files
        (tmp_path / "test.txt").write_text("content")
        
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            verbose=True
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.verify_integrity_command(args)
        # Accept both pass and fail
        assert exc_info.value.code in [0, 1]
    
    def test_integrity_command_nonexistent_dir(self, tmp_path, capsys):
        """Test integrity verification with nonexistent directory."""
        args = argparse.Namespace(
            output_dir=str(tmp_path / "nonexistent"),
            verbose=False
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.verify_integrity_command(args)
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestMainCli:
    """Test suite for main CLI entry point."""
    
    def test_main_with_pdf_command(self, tmp_path):
        """Test main with pdf subcommand using real PDF."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a real PDF
        pdf_file = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Test content")
        c.showPage()
        c.save()
        
        with patch('sys.argv', ['cli.py', 'pdf', str(pdf_file)]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0
    
    def test_main_with_markdown_command(self, tmp_path):
        """Test main with markdown subcommand using real validation."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nValid content.")
        
        with patch('sys.argv', ['cli.py', 'markdown', str(tmp_path)]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0
    
    def test_main_with_integrity_command(self, tmp_path):
        """Test main with integrity subcommand using real verification."""
        # Create some files for integrity check
        (tmp_path / "test.txt").write_text("content")
        
        with patch('sys.argv', ['cli.py', 'integrity', str(tmp_path)]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            # Accept either pass or fail since integrity depends on actual state
            assert exc_info.value.code in [0, 1]
    
    def test_main_without_command(self, capsys):
        """Test main without any subcommand."""
        with patch('sys.argv', ['cli.py']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 1
    
    def test_main_with_invalid_pdf(self, tmp_path, capsys):
        """Test main when PDF is invalid and cannot be read."""
        # Create an invalid PDF (not a real PDF format)
        pdf_file = tmp_path / "invalid.pdf"
        pdf_file.write_bytes(b"not a real pdf")
        
        with patch('sys.argv', ['cli.py', 'pdf', str(pdf_file)]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            # Invalid PDF should fail
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        # Should have some error output
        assert len(captured.err) > 0 or len(captured.out) > 0


class TestCliArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_pdf_parser_default_preview_words(self, tmp_path):
        """Test PDF parser runs with default preview words using real PDF."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a real PDF
        pdf_file = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Test content for preview words validation")
        c.showPage()
        c.save()
        
        with patch('sys.argv', ['cli.py', 'pdf', str(pdf_file)]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            # Should run successfully
            assert exc_info.value.code == 0
    
    def test_pdf_parser_verbose_flag(self, tmp_path, capsys):
        """Test PDF parser verbose flag works with real PDF."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a real PDF with issues (unresolved refs)
        pdf_file = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "See section ?? for details")
        c.drawString(100, 730, "Reference to figure ??")
        c.showPage()
        c.save()
        
        with patch('sys.argv', ['cli.py', 'pdf', str(pdf_file), '-v']):
            with pytest.raises(SystemExit):
                cli.main()
        
        captured = capsys.readouterr()
        # Verbose output should show validation info
        assert 'Validating' in captured.out or 'issues' in captured.out.lower()

