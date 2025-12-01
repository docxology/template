"""Comprehensive tests for infrastructure/literature/search_cli.py.

Tests the wrapper CLI script for literature search.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
import pytest

from infrastructure.literature import search_cli


@dataclass
class MockPaper:
    """Mock paper for testing."""
    title: str = "Test Paper"
    authors: list = None
    year: int = 2024
    doi: str = "10.1234/test"
    pdf_url: str = "https://example.com/paper.pdf"
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = ["Author One"]


class TestSearchCliMain:
    """Test suite for search_cli main function."""
    
    def test_main_basic_search(self, capsys):
        """Test basic search execution."""
        mock_papers = [MockPaper()]
        mock_searcher = MagicMock()
        mock_searcher.search.return_value = mock_papers
        
        with patch('sys.argv', ['search_cli.py', 'test query']):
            with patch.object(search_cli, 'LiteratureConfig'):
                with patch.object(search_cli, 'LiteratureSearch', return_value=mock_searcher):
                    search_cli.main()
        
        captured = capsys.readouterr()
        assert "test query" in captured.out
        assert "Test Paper" in captured.out
    
    def test_main_with_limit(self, capsys):
        """Test search with limit argument."""
        mock_searcher = MagicMock()
        mock_searcher.search.return_value = []
        
        with patch('sys.argv', ['search_cli.py', 'test', '--limit', '5']):
            with patch.object(search_cli, 'LiteratureConfig'):
                with patch.object(search_cli, 'LiteratureSearch', return_value=mock_searcher):
                    search_cli.main()
        
        mock_searcher.search.assert_called_once()
        call_kwargs = mock_searcher.search.call_args[1]
        assert call_kwargs['limit'] == 5
    
    def test_main_with_download(self, capsys):
        """Test search with download flag."""
        mock_papers = [MockPaper()]
        mock_searcher = MagicMock()
        mock_searcher.search.return_value = mock_papers
        mock_searcher.download_paper.return_value = Path("/tmp/paper.pdf")
        
        with patch('sys.argv', ['search_cli.py', 'test', '--download']):
            with patch.object(search_cli, 'LiteratureConfig'):
                with patch.object(search_cli, 'LiteratureSearch', return_value=mock_searcher):
                    search_cli.main()
        
        mock_searcher.download_paper.assert_called_once()
        captured = capsys.readouterr()
        assert "Downloaded" in captured.out
    
    def test_main_paper_without_doi(self, capsys):
        """Test output when paper has no DOI."""
        mock_papers = [MockPaper(doi=None)]
        mock_searcher = MagicMock()
        mock_searcher.search.return_value = mock_papers
        
        with patch('sys.argv', ['search_cli.py', 'test']):
            with patch.object(search_cli, 'LiteratureConfig'):
                with patch.object(search_cli, 'LiteratureSearch', return_value=mock_searcher):
                    search_cli.main()
        
        captured = capsys.readouterr()
        assert "DOI:" not in captured.out
    
    def test_main_paper_without_pdf_url(self, capsys):
        """Test download skipped when no PDF URL."""
        mock_papers = [MockPaper(pdf_url=None)]
        mock_searcher = MagicMock()
        mock_searcher.search.return_value = mock_papers
        
        with patch('sys.argv', ['search_cli.py', 'test', '--download']):
            with patch.object(search_cli, 'LiteratureConfig'):
                with patch.object(search_cli, 'LiteratureSearch', return_value=mock_searcher):
                    search_cli.main()
        
        mock_searcher.download_paper.assert_not_called()
    
    def test_main_download_returns_none(self, capsys):
        """Test when download fails (returns None)."""
        mock_papers = [MockPaper()]
        mock_searcher = MagicMock()
        mock_searcher.search.return_value = mock_papers
        mock_searcher.download_paper.return_value = None
        
        with patch('sys.argv', ['search_cli.py', 'test', '--download']):
            with patch.object(search_cli, 'LiteratureConfig'):
                with patch.object(search_cli, 'LiteratureSearch', return_value=mock_searcher):
                    search_cli.main()
        
        captured = capsys.readouterr()
        assert "Downloaded" not in captured.out


class TestSearchCliModule:
    """Test module structure."""
    
    def test_has_main_function(self):
        """Test that module has main function."""
        assert hasattr(search_cli, 'main')
        assert callable(search_cli.main)

