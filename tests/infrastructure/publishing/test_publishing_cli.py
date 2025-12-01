"""Comprehensive tests for infrastructure/publishing/cli.py.

Tests the CLI interface for publishing operations.
"""

import argparse
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.publishing import cli


class TestExtractMetadataCommand:
    """Test suite for extract_metadata_command."""
    
    def test_extract_metadata_basic(self, tmp_path, capsys):
        """Test basic metadata extraction."""
        # Create test markdown file
        md_file = tmp_path / "abstract.md"
        md_file.write_text("# Abstract\n\nThis is a test abstract.")
        
        args = argparse.Namespace(manuscript_dir=str(tmp_path))
        
        mock_metadata = {
            'title': 'Test Research Paper',
            'authors': ['John Doe', 'Jane Smith'],
            'abstract': 'This is a test abstract for the research paper.',
            'keywords': ['testing', 'research']
        }
        
        with patch.object(cli, 'extract_publication_metadata', return_value=mock_metadata):
            cli.extract_metadata_command(args)
        
        captured = capsys.readouterr()
        assert 'Test Research Paper' in captured.out
        assert 'John Doe' in captured.out
        assert 'testing' in captured.out
    
    def test_extract_metadata_nonexistent_dir(self, tmp_path, capsys):
        """Test metadata extraction with nonexistent directory."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path / "nonexistent"))
        
        with pytest.raises(SystemExit) as exc_info:
            cli.extract_metadata_command(args)
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err
    
    def test_extract_metadata_no_md_files(self, tmp_path, capsys):
        """Test metadata extraction when no markdown files exist."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path))
        
        with pytest.raises(SystemExit) as exc_info:
            cli.extract_metadata_command(args)
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "No markdown files" in captured.err


class TestGenerateCitationCommand:
    """Test suite for generate_citation_command."""
    
    def test_generate_citation_bibtex(self, tmp_path, capsys):
        """Test BibTeX citation generation."""
        md_file = tmp_path / "paper.md"
        md_file.write_text("# Paper Title\n\nContent here.")
        
        args = argparse.Namespace(
            manuscript_dir=str(tmp_path),
            format="bibtex"
        )
        
        mock_metadata = {
            'title': 'Test Paper',
            'authors': ['Author One'],
            'year': 2024
        }
        mock_bibtex = "@article{test2024,\n  title={Test Paper}\n}"
        
        with patch.object(cli, 'extract_publication_metadata', return_value=mock_metadata):
            with patch.object(cli, 'generate_citation_bibtex', return_value=mock_bibtex):
                cli.generate_citation_command(args)
        
        captured = capsys.readouterr()
        assert "@article" in captured.out
    
    def test_generate_citation_unsupported_format(self, tmp_path, capsys):
        """Test citation generation with unsupported format."""
        md_file = tmp_path / "paper.md"
        md_file.write_text("# Paper")
        
        args = argparse.Namespace(
            manuscript_dir=str(tmp_path),
            format="invalid_format"
        )
        
        mock_metadata = {'title': 'Test'}
        
        with patch.object(cli, 'extract_publication_metadata', return_value=mock_metadata):
            with pytest.raises(SystemExit) as exc_info:
                cli.generate_citation_command(args)
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Unsupported format" in captured.err
    
    def test_generate_citation_nonexistent_dir(self, tmp_path, capsys):
        """Test citation generation with nonexistent directory."""
        args = argparse.Namespace(
            manuscript_dir=str(tmp_path / "nonexistent"),
            format="bibtex"
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.generate_citation_command(args)
        assert exc_info.value.code == 1
    
    def test_generate_citation_no_md_files(self, tmp_path, capsys):
        """Test citation generation when no markdown files exist."""
        args = argparse.Namespace(
            manuscript_dir=str(tmp_path),
            format="bibtex"
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.generate_citation_command(args)
        assert exc_info.value.code == 1


class TestPublishZenodoCommand:
    """Test suite for publish_zenodo_command."""
    
    def test_publish_zenodo_basic(self, tmp_path, capsys):
        """Test basic Zenodo publishing."""
        # Create test PDF
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token="test_token",
            title="Test Publication",
            authors="Author One,Author Two",
            description="Test description"
        )
        
        mock_client = MagicMock()
        mock_client.upload_publication.return_value = "12345"
        
        with patch.object(cli, 'ZenodoClient', return_value=mock_client):
            cli.publish_zenodo_command(args)
        
        captured = capsys.readouterr()
        assert "Published successfully" in captured.out
        assert "12345" in captured.out
    
    def test_publish_zenodo_env_token(self, tmp_path, capsys):
        """Test Zenodo publishing with environment token."""
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF")
        
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token=None,
            title="Test",
            authors=None,
            description=None
        )
        
        mock_client = MagicMock()
        mock_client.upload_publication.return_value = "12345"
        
        with patch.dict(os.environ, {'ZENODO_TOKEN': 'env_token'}):
            with patch.object(cli, 'ZenodoClient', return_value=mock_client):
                cli.publish_zenodo_command(args)
        
        captured = capsys.readouterr()
        assert "Published successfully" in captured.out
    
    def test_publish_zenodo_no_token(self, tmp_path, capsys):
        """Test Zenodo publishing without token."""
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token=None,
            title=None,
            authors=None,
            description=None
        )
        
        with patch.dict(os.environ, {}, clear=True):
            # Ensure ZENODO_TOKEN is not set
            if 'ZENODO_TOKEN' in os.environ:
                del os.environ['ZENODO_TOKEN']
            with pytest.raises(SystemExit) as exc_info:
                cli.publish_zenodo_command(args)
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "ZENODO_TOKEN" in captured.err
    
    def test_publish_zenodo_nonexistent_dir(self, tmp_path, capsys):
        """Test Zenodo publishing with nonexistent directory."""
        args = argparse.Namespace(
            output_dir=str(tmp_path / "nonexistent"),
            token="test_token",
            title=None,
            authors=None,
            description=None
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.publish_zenodo_command(args)
        assert exc_info.value.code == 1
    
    def test_publish_zenodo_no_pdfs(self, tmp_path, capsys):
        """Test Zenodo publishing when no PDFs exist."""
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token="test_token",
            title=None,
            authors=None,
            description=None
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cli.publish_zenodo_command(args)
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "No PDF files" in captured.err
    
    def test_publish_zenodo_upload_error(self, tmp_path, capsys):
        """Test Zenodo publishing when upload fails."""
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF")
        
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token="test_token",
            title="Test",
            authors=None,
            description=None
        )
        
        mock_client = MagicMock()
        mock_client.upload_publication.side_effect = Exception("Upload failed")
        
        with patch.object(cli, 'ZenodoClient', return_value=mock_client):
            with pytest.raises(SystemExit) as exc_info:
                cli.publish_zenodo_command(args)
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestMainCli:
    """Test suite for main CLI entry point."""
    
    def test_main_with_extract_metadata(self, tmp_path, capsys):
        """Test main with extract-metadata subcommand."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")
        
        mock_metadata = {'title': 'Test', 'authors': [], 'abstract': '', 'keywords': []}
        
        with patch('sys.argv', ['cli.py', 'extract-metadata', str(tmp_path)]):
            with patch.object(cli, 'extract_publication_metadata', return_value=mock_metadata):
                cli.main()
        
        captured = capsys.readouterr()
        assert 'Metadata' in captured.out
    
    def test_main_with_generate_citation(self, tmp_path, capsys):
        """Test main with generate-citation subcommand."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")
        
        mock_metadata = {'title': 'Test', 'authors': []}
        mock_bibtex = "@article{test, title={Test}}"
        
        with patch('sys.argv', ['cli.py', 'generate-citation', str(tmp_path)]):
            with patch.object(cli, 'extract_publication_metadata', return_value=mock_metadata):
                with patch.object(cli, 'generate_citation_bibtex', return_value=mock_bibtex):
                    cli.main()
        
        captured = capsys.readouterr()
        assert "@article" in captured.out
    
    def test_main_without_command(self, capsys):
        """Test main without any subcommand."""
        with patch('sys.argv', ['cli.py']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 1
    
    def test_main_with_exception(self, tmp_path, capsys):
        """Test main when command raises an exception."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")
        
        with patch('sys.argv', ['cli.py', 'extract-metadata', str(tmp_path)]):
            with patch.object(cli, 'extract_publication_metadata', side_effect=Exception("Error")):
                with pytest.raises(SystemExit) as exc_info:
                    cli.main()
                assert exc_info.value.code == 1


class TestCliModuleStructure:
    """Test CLI module structure and imports."""
    
    def test_module_has_main_function(self):
        """Test that cli module has main function."""
        assert hasattr(cli, 'main')
        assert callable(cli.main)
    
    def test_module_has_command_functions(self):
        """Test that cli module has command functions."""
        assert hasattr(cli, 'extract_metadata_command')
        assert hasattr(cli, 'generate_citation_command')
        assert hasattr(cli, 'publish_zenodo_command')

