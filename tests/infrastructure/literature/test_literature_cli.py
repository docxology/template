"""Comprehensive tests for infrastructure/literature/cli.py.

Tests the CLI interface for literature search operations.
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass
import pytest

from infrastructure.literature import cli


@dataclass
class MockPaper:
    """Mock paper for testing."""
    title: str = "Test Paper Title"
    authors: list = None
    year: int = 2024
    doi: str = "10.1234/test"
    pdf_url: str = "https://example.com/paper.pdf"
    abstract: str = "Test abstract"
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = ["Author One", "Author Two"]


class TestSearchCommand:
    """Test suite for search_command."""
    
    def test_search_command_basic(self, capsys):
        """Test basic search command execution."""
        args = argparse.Namespace(
            query="machine learning",
            sources=None,
            limit=5,
            download=False
        )
        
        mock_papers = [MockPaper(), MockPaper(title="Second Paper")]
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = mock_papers
        
        with patch.object(cli, 'LiteratureConfig'):
            with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                cli.search_command(args)
        
        captured = capsys.readouterr()
        assert "machine learning" in captured.out
        assert "Test Paper Title" in captured.out
        assert "Author One" in captured.out
    
    def test_search_command_with_sources(self, capsys):
        """Test search command with specific sources."""
        args = argparse.Namespace(
            query="deep learning",
            sources="arxiv,semanticscholar",
            limit=10,
            download=False
        )
        
        mock_papers = [MockPaper()]
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = mock_papers
        
        with patch.object(cli, 'LiteratureConfig'):
            with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                cli.search_command(args)
        
        # Verify sources were split correctly
        mock_manager.search_papers.assert_called_once()
        call_kwargs = mock_manager.search_papers.call_args[1]
        assert call_kwargs['sources'] == ["arxiv", "semanticscholar"]
    
    def test_search_command_with_download(self, capsys):
        """Test search command with download option."""
        args = argparse.Namespace(
            query="neural networks",
            sources=None,
            limit=5,
            download=True
        )
        
        mock_papers = [MockPaper()]
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = mock_papers
        mock_manager.download_paper.return_value = Path("/tmp/paper.pdf")
        
        with patch.object(cli, 'LiteratureConfig'):
            with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                cli.search_command(args)
        
        mock_manager.download_paper.assert_called_once()
        captured = capsys.readouterr()
        assert "Downloaded" in captured.out
    
    def test_search_command_download_fails(self, capsys):
        """Test search command when download fails."""
        args = argparse.Namespace(
            query="neural networks",
            sources=None,
            limit=5,
            download=True
        )
        
        mock_papers = [MockPaper()]
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = mock_papers
        mock_manager.download_paper.return_value = None
        
        with patch.object(cli, 'LiteratureConfig'):
            with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                cli.search_command(args)
        
        captured = capsys.readouterr()
        assert "Downloaded" not in captured.out
    
    def test_search_command_paper_without_doi(self, capsys):
        """Test search command with paper missing DOI."""
        args = argparse.Namespace(
            query="test",
            sources=None,
            limit=5,
            download=False
        )
        
        paper_no_doi = MockPaper(doi=None)
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = [paper_no_doi]
        
        with patch.object(cli, 'LiteratureConfig'):
            with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                cli.search_command(args)
        
        captured = capsys.readouterr()
        assert "DOI:" not in captured.out
    
    def test_search_command_paper_without_pdf_url(self, capsys):
        """Test search command with paper missing PDF URL."""
        args = argparse.Namespace(
            query="test",
            sources=None,
            limit=5,
            download=True
        )
        
        paper_no_pdf = MockPaper(pdf_url=None)
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = [paper_no_pdf]
        
        with patch.object(cli, 'LiteratureConfig'):
            with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                cli.search_command(args)
        
        # Should not attempt download without PDF URL
        mock_manager.download_paper.assert_not_called()


class TestMainCli:
    """Test suite for main CLI entry point."""
    
    def test_main_with_search_command(self, capsys):
        """Test main with search subcommand."""
        mock_papers = [MockPaper()]
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = mock_papers
        
        with patch('sys.argv', ['cli.py', 'search', 'test query']):
            with patch.object(cli, 'LiteratureConfig'):
                with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                    cli.main()
        
        captured = capsys.readouterr()
        assert "test query" in captured.out
    
    def test_main_without_command(self, capsys):
        """Test main without any subcommand."""
        with patch('sys.argv', ['cli.py']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 1
    
    def test_main_with_exception(self, capsys):
        """Test main when command raises an exception."""
        with patch('sys.argv', ['cli.py', 'search', 'test']):
            with patch.object(cli, 'LiteratureConfig', side_effect=Exception("Config error")):
                with pytest.raises(SystemExit) as exc_info:
                    cli.main()
                assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err
    
    def test_main_with_limit_argument(self, capsys):
        """Test main with limit argument."""
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = []
        
        with patch('sys.argv', ['cli.py', 'search', 'test', '--limit', '20']):
            with patch.object(cli, 'LiteratureConfig'):
                with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                    cli.main()
        
        mock_manager.search_papers.assert_called_once()
        call_kwargs = mock_manager.search_papers.call_args[1]
        assert call_kwargs['limit'] == 20
    
    def test_main_with_sources_argument(self, capsys):
        """Test main with sources argument."""
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = []
        
        with patch('sys.argv', ['cli.py', 'search', 'test', '--sources', 'arxiv']):
            with patch.object(cli, 'LiteratureConfig'):
                with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                    cli.main()
        
        mock_manager.search_papers.assert_called_once()
        call_kwargs = mock_manager.search_papers.call_args[1]
        assert call_kwargs['sources'] == ['arxiv']
    
    def test_main_with_download_flag(self, capsys):
        """Test main with download flag."""
        mock_papers = [MockPaper()]
        mock_manager = MagicMock()
        mock_manager.search_papers.return_value = mock_papers
        mock_manager.download_paper.return_value = Path("/tmp/test.pdf")
        
        with patch('sys.argv', ['cli.py', 'search', 'test', '--download']):
            with patch.object(cli, 'LiteratureConfig'):
                with patch.object(cli, 'LiteratureSearch', return_value=mock_manager):
                    cli.main()
        
        mock_manager.download_paper.assert_called_once()


class TestCliModuleStructure:
    """Test CLI module structure and imports."""
    
    def test_module_has_main_function(self):
        """Test that cli module has main function."""
        assert hasattr(cli, 'main')
        assert callable(cli.main)
    
    def test_module_has_search_command(self):
        """Test that cli module has search_command function."""
        assert hasattr(cli, 'search_command')
        assert callable(cli.search_command)
    
    def test_imports_required_modules(self):
        """Test that required modules are imported."""
        assert hasattr(cli, 'LiteratureSearch')
        assert hasattr(cli, 'LiteratureConfig')

