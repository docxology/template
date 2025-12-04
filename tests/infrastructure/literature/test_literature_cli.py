"""Comprehensive tests for infrastructure/literature/cli.py.

Tests the CLI interface for literature search operations using real execution
and function-level testing.
"""

import subprocess
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from infrastructure.literature import cli
from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.config import LiteratureConfig


class TestCLIExecution:
    """Test CLI execution with real subprocess calls."""

    def test_cli_help_output(self):
        """Test that CLI help works."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.literature.cli", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "search" in result.stdout

    def test_cli_importable(self):
        """Test that CLI module can be imported."""
        # This tests that the CLI module structure is correct
        assert hasattr(cli, 'main')
        assert callable(cli.main)

    def test_cli_module_structure(self):
        """Test that CLI module has expected functions."""
        # Test that key functions exist
        assert hasattr(cli, 'main')
        assert hasattr(cli, 'search_command')
        assert hasattr(cli, 'library_list_command')
        assert hasattr(cli, 'library_export_command')
        assert hasattr(cli, 'library_stats_command')

    def test_cli_no_command_shows_help(self):
        """Test that CLI shows help when no command provided."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.literature.cli"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "usage:" in result.stdout.lower()


class TestSearchCommand:
    """Test search_command function."""

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_search_command_no_results(self, mock_config, mock_search_class):
        """Test search command with no results."""
        mock_manager = Mock()
        mock_manager.search.return_value = []
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test query"
        args.sources = None
        args.limit = 10
        args.download = False
        
        # Capture stdout
        with patch('builtins.print') as mock_print:
            cli.search_command(args)
            # Should print "No results found."
            mock_print.assert_any_call("No results found.")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_search_command_with_results(self, mock_config, mock_search_class):
        """Test search command with results."""
        # Create mock paper
        mock_paper = Mock()
        mock_paper.title = "Test Paper"
        mock_paper.authors = ["Author 1", "Author 2"]
        mock_paper.year = 2024
        mock_paper.doi = "10.1234/test"
        mock_paper.citation_count = 5
        mock_paper.pdf_url = None
        
        mock_manager = Mock()
        mock_manager.search.return_value = [mock_paper]
        mock_manager.add_to_library.return_value = "test2024author1"
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test query"
        args.sources = None
        args.limit = 10
        args.download = False
        
        with patch('builtins.print') as mock_print:
            cli.search_command(args)
            # Should print paper details
            mock_print.assert_any_call("Searching for: test query...")
            mock_print.assert_any_call("\n1. Test Paper")
            mock_print.assert_any_call("   Authors: Author 1, Author 2")
            mock_print.assert_any_call("   Year: 2024")
            mock_print.assert_any_call("   DOI: 10.1234/test")
            mock_print.assert_any_call("   Citations: 5")
            mock_print.assert_any_call("   Citation key: test2024author1")
            mock_print.assert_any_call("\nAdded 1 papers to library.")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_search_command_with_download(self, mock_config, mock_search_class):
        """Test search command with download option."""
        mock_paper = Mock()
        mock_paper.title = "Test Paper"
        mock_paper.authors = ["Author"]
        mock_paper.year = 2024
        mock_paper.doi = None
        mock_paper.citation_count = None
        mock_paper.pdf_url = "http://example.com/paper.pdf"
        
        mock_manager = Mock()
        mock_manager.search.return_value = [mock_paper]
        mock_manager.add_to_library.return_value = "test2024author"
        mock_manager.download_paper.return_value = Path("/path/to/paper.pdf")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test"
        args.sources = None
        args.limit = 10
        args.download = True
        
        with patch('builtins.print') as mock_print:
            cli.search_command(args)
            # Should call download_paper
            mock_manager.download_paper.assert_called_once_with(mock_paper)
            mock_print.assert_any_call("   Downloaded: /path/to/paper.pdf")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_search_command_with_sources(self, mock_config, mock_search_class):
        """Test search command with specific sources."""
        mock_manager = Mock()
        mock_manager.search.return_value = []
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test"
        args.sources = "arxiv,semanticscholar"
        args.limit = 5
        args.download = False
        
        cli.search_command(args)
        
        # Should split sources
        mock_manager.search.assert_called_once_with(
            query="test",
            sources=["arxiv", "semanticscholar"],
            limit=5
        )


class TestLibraryListCommand:
    """Test library_list_command function."""

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_list_empty(self, mock_config, mock_search_class):
        """Test library list with empty library."""
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = []
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            mock_print.assert_any_call("Library is empty.")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_list_with_entries(self, mock_config, mock_search_class):
        """Test library list with entries."""
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = [
            {
                "citation_key": "test2024author",
                "title": "Test Paper Title",
                "authors": ["Author 1", "Author 2"],
                "year": 2024,
                "doi": "10.1234/test",
                "pdf_path": "/path/to/paper.pdf"
            }
        ]
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            mock_print.assert_any_call("Library contains 1 entries:\n")
            mock_print.assert_any_call("[✓] test2024author")
            mock_print.assert_any_call("    Test Paper Title")
            mock_print.assert_any_call("    Author 1 et al. (2024)")
            mock_print.assert_any_call("    DOI: 10.1234/test")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_list_no_pdf(self, mock_config, mock_search_class):
        """Test library list entry without PDF."""
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = [
            {
                "citation_key": "test2024author",
                "title": "Test Paper",
                "authors": ["Author"],
                "year": 2024,
                "pdf_path": None
            }
        ]
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            # Should show ✗ for no PDF
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("✗" in str(call) for call in calls)


class TestLibraryExportCommand:
    """Test library_export_command function."""

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_export_default(self, mock_config, mock_search_class):
        """Test library export with default output."""
        mock_manager = Mock()
        mock_manager.export_library.return_value = Path("/path/to/library.json")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.output = None
        args.format = "json"
        
        with patch('builtins.print') as mock_print:
            cli.library_export_command(args)
            mock_manager.export_library.assert_called_once_with(None, format="json")
            mock_print.assert_called_once_with("Library exported to: /path/to/library.json")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_export_custom_output(self, mock_config, mock_search_class):
        """Test library export with custom output path."""
        mock_manager = Mock()
        mock_manager.export_library.return_value = Path("/custom/path.json")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.output = "/custom/path.json"
        args.format = "json"
        
        with patch('builtins.print') as mock_print:
            cli.library_export_command(args)
            mock_manager.export_library.assert_called_once_with(
                Path("/custom/path.json"),
                format="json"
            )

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_export_error(self, mock_config, mock_search_class):
        """Test library export with error."""
        mock_manager = Mock()
        mock_manager.export_library.side_effect = ValueError("Export failed")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.output = None
        args.format = "json"
        
        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            with patch('sys.exit') as mock_exit:
                cli.library_export_command(args)
                mock_exit.assert_called_once_with(1)
                assert "Error: Export failed" in mock_stderr.getvalue()


class TestLibraryStatsCommand:
    """Test library_stats_command function."""

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_stats_basic(self, mock_config, mock_search_class):
        """Test library stats with basic stats."""
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {
            "total_entries": 10,
            "downloaded_pdfs": 5
        }
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_stats_command(args)
            mock_print.assert_any_call("Library Statistics")
            mock_print.assert_any_call("=" * 40)
            mock_print.assert_any_call("Total entries: 10")
            mock_print.assert_any_call("Downloaded PDFs: 5")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_stats_with_year_range(self, mock_config, mock_search_class):
        """Test library stats with year range."""
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {
            "total_entries": 10,
            "downloaded_pdfs": 5,
            "oldest_year": 2020,
            "newest_year": 2024
        }
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_stats_command(args)
            mock_print.assert_any_call("Year range: 2020 - 2024")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_stats_with_sources(self, mock_config, mock_search_class):
        """Test library stats with source breakdown."""
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {
            "total_entries": 10,
            "downloaded_pdfs": 5,
            "sources": {"arxiv": 7, "semanticscholar": 3}
        }
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_stats_command(args)
            mock_print.assert_any_call("\nBy Source:")
            mock_print.assert_any_call("  arxiv: 7")
            mock_print.assert_any_call("  semanticscholar: 3")

    @patch('infrastructure.literature.cli.LiteratureSearch')
    @patch('infrastructure.literature.cli.LiteratureConfig')
    def test_library_stats_with_years(self, mock_config, mock_search_class):
        """Test library stats with year breakdown."""
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {
            "total_entries": 10,
            "downloaded_pdfs": 5,
            "years": {"2024": 5, "2023": 3, "2022": 2}
        }
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_stats_command(args)
            mock_print.assert_any_call("\nBy Year (recent first):")
            # Should show up to 10 most recent years


class TestMainFunction:
    """Test main CLI function."""

    @patch('infrastructure.literature.cli.search_command')
    def test_main_search_command(self, mock_search):
        """Test main function with search command."""
        with patch('sys.argv', ['cli.py', 'search', 'test query']):
            with patch('sys.exit') as mock_exit:
                cli.main()
                mock_search.assert_called_once()
                # Should not exit with error
                mock_exit.assert_not_called()

    @patch('infrastructure.literature.cli.library_list_command')
    def test_main_library_list(self, mock_list):
        """Test main function with library list command."""
        with patch('sys.argv', ['cli.py', 'library', 'list']):
            with patch('sys.exit') as mock_exit:
                cli.main()
                mock_list.assert_called_once()

    @patch('infrastructure.literature.cli.library_export_command')
    def test_main_library_export(self, mock_export):
        """Test main function with library export command."""
        with patch('sys.argv', ['cli.py', 'library', 'export']):
            with patch('sys.exit') as mock_exit:
                cli.main()
                mock_export.assert_called_once()

    @patch('infrastructure.literature.cli.library_stats_command')
    def test_main_library_stats(self, mock_stats):
        """Test main function with library stats command."""
        with patch('sys.argv', ['cli.py', 'library', 'stats']):
            with patch('sys.exit') as mock_exit:
                cli.main()
                mock_stats.assert_called_once()

    def test_main_no_command(self):
        """Test main function with no command."""
        with patch('sys.argv', ['cli.py']):
            with patch('sys.exit') as mock_exit:
                with patch('argparse.ArgumentParser.print_help') as mock_help:
                    cli.main()
                    # print_help may be called multiple times (main parser and subparsers)
                    assert mock_help.called, "print_help should be called"
                    mock_exit.assert_called_once_with(1)

    @patch('infrastructure.literature.cli.search_command')
    def test_main_exception_handling(self, mock_search):
        """Test main function exception handling."""
        mock_search.side_effect = Exception("Test error")
        
        with patch('sys.argv', ['cli.py', 'search', 'test']):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stderr', new=StringIO()) as mock_stderr:
                    cli.main()
                    mock_exit.assert_called_once_with(1)
                    assert "Error: Test error" in mock_stderr.getvalue()
