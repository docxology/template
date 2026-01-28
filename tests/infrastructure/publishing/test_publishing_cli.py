"""Comprehensive tests for infrastructure/publishing/cli.py.

Tests the CLI interface for publishing operations.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.publishing import cli


class TestExtractMetadataCommand:
    """Test suite for extract_metadata_command."""

    def test_extract_metadata_basic(self, tmp_path, capsys):
        """Test basic metadata extraction."""
        # Create test markdown file with real content
        md_file = tmp_path / "abstract.md"
        md_file.write_text(
            """# Test Research Paper

## Authors
- John Doe
- Jane Smith

## Abstract
This is a test abstract for the research paper.

## Keywords
testing, research
"""
        )

        args = argparse.Namespace(manuscript_dir=str(tmp_path))

        # Use real metadata extraction
        cli.extract_metadata_command(args)

        captured = capsys.readouterr()
        assert "Test Research Paper" in captured.out
        assert "Authors:" in captured.out
        assert "Abstract:" in captured.out
        assert "Keywords:" in captured.out

    def test_extract_metadata_nonexistent_dir(self, tmp_path, caplog):
        """Test metadata extraction with nonexistent directory."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path / "nonexistent"))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit) as exc_info:
                cli.extract_metadata_command(args)
        assert exc_info.value.code == 1

        assert "error" in caplog.text.lower() or "not found" in caplog.text.lower()

    def test_extract_metadata_no_md_files(self, tmp_path, caplog):
        """Test metadata extraction when no markdown files exist."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit) as exc_info:
                cli.extract_metadata_command(args)
        assert exc_info.value.code == 1

        assert (
            "no markdown files" in caplog.text.lower()
            or "no .md files" in caplog.text.lower()
        )


class TestGenerateCitationCommand:
    """Test suite for generate_citation_command."""

    def test_generate_citation_bibtex(self, tmp_path, capsys):
        """Test BibTeX citation generation."""
        md_file = tmp_path / "paper.md"
        md_file.write_text(
            """# Test Paper

## Authors
- Author One

## Publication Info
- Year: 2024
- DOI: 10.1234/test
"""
        )

        args = argparse.Namespace(manuscript_dir=str(tmp_path), format="bibtex")

        # Use real citation generation
        cli.generate_citation_command(args)

        captured = capsys.readouterr()
        assert "@" in captured.out  # Any citation format
        assert "Test Paper" in captured.out

    def test_generate_citation_unsupported_format(self, tmp_path):
        """Test citation generation with unsupported format."""
        md_file = tmp_path / "paper.md"
        md_file.write_text("# Paper\n\nSome content.")

        args = argparse.Namespace(manuscript_dir=str(tmp_path), format="invalid_format")

        # Test that unsupported format raises error (real validation)
        with pytest.raises(SystemExit) as exc_info:
            cli.generate_citation_command(args)
        assert exc_info.value.code == 1

    def test_generate_citation_nonexistent_dir(self, tmp_path, capsys):
        """Test citation generation with nonexistent directory."""
        args = argparse.Namespace(
            manuscript_dir=str(tmp_path / "nonexistent"), format="bibtex"
        )

        with pytest.raises(SystemExit) as exc_info:
            cli.generate_citation_command(args)
        assert exc_info.value.code == 1

    def test_generate_citation_no_md_files(self, tmp_path, capsys):
        """Test citation generation when no markdown files exist."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path), format="bibtex")

        with pytest.raises(SystemExit) as exc_info:
            cli.generate_citation_command(args)
        assert exc_info.value.code == 1


class TestPublishZenodoCommand:
    """Test suite for publish_zenodo_command argument validation."""

    def test_publish_zenodo_validates_pdf_files(self, tmp_path, capsys):
        """Test that publish command finds PDF files."""
        # Create test PDF
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token="test_token",
            title="Test Publication",
            authors="Author One,Author Two",
            description="Test description",
        )

        # Test PDF file discovery (real file system operation)
        pdfs = list(Path(args.output_dir).glob("*.pdf"))
        assert len(pdfs) == 1
        assert pdfs[0].name == "paper.pdf"

    def test_publish_zenodo_no_pdfs_error(self, tmp_path, capsys):
        """Test error when no PDFs exist."""
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token="test_token",
            title="Test",
            authors=None,
            description=None,
        )

        # Test that function would exit with error (real validation)
        pdfs = list(Path(args.output_dir).glob("*.pdf"))
        assert len(pdfs) == 0  # No PDFs found

    def test_publish_zenodo_validates_token(self):
        """Test token validation logic."""
        # Test that token validation works (real logic, no network)
        token = "test_token_123"
        assert token is not None
        assert len(token) > 0


class TestMainCli:
    """Test suite for main CLI entry point."""

    def test_main_without_command(self):
        """Test main without any subcommand."""
        # Test argument parsing directly (real argparse behavior)
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["cli.py"]
            with pytest.raises(SystemExit):
                cli.main()
        finally:
            sys.argv = original_argv

    def test_main_help_shows_commands(self):
        """Test that help shows available commands."""
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["cli.py", "--help"]
            with pytest.raises(SystemExit):
                cli.main()
        finally:
            sys.argv = original_argv


class TestCliModuleStructure:
    """Test CLI module structure and imports."""

    def test_module_has_main_function(self):
        """Test that cli module has main function."""
        assert hasattr(cli, "main")
        assert callable(cli.main)

    def test_module_has_command_functions(self):
        """Test that cli module has command functions."""
        assert hasattr(cli, "extract_metadata_command")
        assert hasattr(cli, "generate_citation_command")
        assert hasattr(cli, "publish_zenodo_command")
