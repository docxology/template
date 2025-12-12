"""Comprehensive tests for infrastructure/literature/cli.py.

Tests the CLI interface for literature search operations using real execution
and function-level testing.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from infrastructure.literature.core import cli, LiteratureSearch, LiteratureConfig


class TestCLIExecution:
    """Test CLI execution with real subprocess calls."""

    def test_cli_help_output(self):
        """Test that CLI help works."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.literature.core.cli", "--help"],
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
            [sys.executable, "-m", "infrastructure.literature.core.cli"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "usage:" in result.stdout.lower()


class TestSearchCommand:
    """Test search_command function."""

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_list_empty(self, mock_config, mock_search_class):
        """Test library list with empty library."""
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = []
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            mock_print.assert_any_call("Library is empty.")

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
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

    @patch('infrastructure.literature.core.cli.search_command')
    def test_main_search_command(self, mock_search):
        """Test main function with search command."""
        with patch('sys.argv', ['cli.py', 'search', 'test query']):
            with patch('sys.exit') as mock_exit:
                cli.main()
                mock_search.assert_called_once()
                # Should not exit with error
                mock_exit.assert_not_called()

    @patch('infrastructure.literature.core.cli.library_list_command')
    def test_main_library_list(self, mock_list):
        """Test main function with library list command."""
        with patch('sys.argv', ['cli.py', 'library', 'list']):
            with patch('sys.exit') as mock_exit:
                cli.main()
                mock_list.assert_called_once()

    @patch('infrastructure.literature.core.cli.library_export_command')
    def test_main_library_export(self, mock_export):
        """Test main function with library export command."""
        with patch('sys.argv', ['cli.py', 'library', 'export']):
            with patch('sys.exit') as mock_exit:
                cli.main()
                mock_export.assert_called_once()

    @patch('infrastructure.literature.core.cli.library_stats_command')
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

    @patch('infrastructure.literature.core.cli.search_command')
    def test_main_exception_handling(self, mock_search):
        """Test main function exception handling."""
        mock_search.side_effect = Exception("Test error")
        
        with patch('sys.argv', ['cli.py', 'search', 'test']):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stderr', new=StringIO()) as mock_stderr:
                    cli.main()
                    mock_exit.assert_called_once_with(1)
                    assert "Error: Test error" in mock_stderr.getvalue()


class TestSearchCommandEdgeCases:
    """Test search_command edge cases and error handling."""

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_search_command_search_failure(self, mock_config, mock_search_class):
        """Test search_command when search raises exception."""
        mock_manager = Mock()
        mock_manager.search.side_effect = Exception("Search API error")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test query"
        args.sources = None
        args.limit = 10
        args.download = False
        
        # Should propagate exception
        with pytest.raises(Exception, match="Search API error"):
            cli.search_command(args)

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_search_command_empty_query(self, mock_config, mock_search_class):
        """Test search_command with empty query."""
        mock_manager = Mock()
        mock_manager.search.return_value = []
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = ""
        args.sources = None
        args.limit = 10
        args.download = False
        
        with patch('builtins.print') as mock_print:
            cli.search_command(args)
            mock_print.assert_any_call("Searching for: ...")
            mock_print.assert_any_call("No results found.")

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_search_command_invalid_limit(self, mock_config, mock_search_class):
        """Test search_command with invalid limit (negative or zero)."""
        mock_manager = Mock()
        mock_manager.search.return_value = []
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test"
        args.sources = None
        args.limit = -1  # Invalid limit
        args.download = False
        
        # Should still work (limit validation happens in manager)
        cli.search_command(args)
        mock_manager.search.assert_called_once()

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_search_command_download_failure(self, mock_config, mock_search_class):
        """Test search_command when download fails."""
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
        mock_manager.download_paper.return_value = None  # Download fails
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test"
        args.sources = None
        args.limit = 10
        args.download = True
        
        with patch('builtins.print') as mock_print:
            cli.search_command(args)
            # Should not print "Downloaded:" if download returns None
            download_calls = [str(call) for call in mock_print.call_args_list if "Downloaded:" in str(call)]
            assert len(download_calls) == 0

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_search_command_add_to_library_failure(self, mock_config, mock_search_class):
        """Test search_command when add_to_library raises exception."""
        mock_paper = Mock()
        mock_paper.title = "Test Paper"
        mock_paper.authors = ["Author"]
        mock_paper.year = 2024
        
        mock_manager = Mock()
        mock_manager.search.return_value = [mock_paper]
        mock_manager.add_to_library.side_effect = Exception("Library error")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test"
        args.sources = None
        args.limit = 10
        args.download = False
        
        # Should propagate exception
        with pytest.raises(Exception, match="Library error"):
            cli.search_command(args)

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_search_command_sources_empty_string(self, mock_config, mock_search_class):
        """Test search_command with empty sources string."""
        mock_manager = Mock()
        mock_manager.search.return_value = []
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test"
        args.sources = ""  # Empty string
        args.limit = 10
        args.download = False
        
        cli.search_command(args)
        # Empty string should split to [''], which should be handled
        mock_manager.search.assert_called_once()


class TestLibraryListCommandEdgeCases:
    """Test library_list_command edge cases."""

    def test_library_list_malformed_entry_missing_title(self, tmp_path, monkeypatch):
        """Test library list with malformed entry missing title."""
        import os
        
        # Set environment variables to use tmp_path
        library_index_file = str(tmp_path / "library.json")
        bibtex_file = str(tmp_path / "refs.bib")
        download_dir = str(tmp_path / "pdfs")
        
        monkeypatch.setenv("LITERATURE_LIBRARY_INDEX", library_index_file)
        monkeypatch.setenv("LITERATURE_BIBTEX_FILE", bibtex_file)
        monkeypatch.setenv("LITERATURE_DOWNLOAD_DIR", download_dir)
        
        # Create real library index JSON file with malformed entry (missing title)
        index_path = Path(library_index_file)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        library_data = {
            "version": "1.0",
            "entries": {
                "test2024author": {
                    "citation_key": "test2024author",
                    # Missing title field
                    "authors": ["Author"],
                    "year": 2024,
                    "doi": None,
                    "source": "unknown",
                    "url": "",
                    "pdf_path": None,
                    "added_date": "",
                    "abstract": "",
                    "venue": None,
                    "citation_count": None,
                    "metadata": {}
                }
            }
        }
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(library_data, f)
        
        # Create real args object
        args = argparse.Namespace()
        
        # Should handle missing title gracefully
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        try:
            cli.library_list_command(args)
            output = captured_output.getvalue()
            # Should still print something
            assert len(output) > 0
            # Should not raise KeyError
            assert "test2024author" in output or "No title" in output
        finally:
            sys.stdout = old_stdout

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_list_entry_long_title(self, mock_config, mock_search_class):
        """Test library list with very long title (truncation)."""
        long_title = "A" * 100  # Very long title
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = [
            {
                "citation_key": "test2024author",
                "title": long_title,
                "authors": ["Author"],
                "year": 2024
            }
        ]
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            # Should truncate title to 70 chars
            calls = [str(call) for call in mock_print.call_args_list]
            title_call = [c for c in calls if "A" * 70 in c]
            assert len(title_call) > 0

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_list_entry_no_authors(self, mock_config, mock_search_class):
        """Test library list with entry having no authors."""
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = [
            {
                "citation_key": "test2024author",
                "title": "Test Paper",
                "authors": [],  # Empty authors
                "year": 2024
            }
        ]
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            # Should show "Unknown" for no authors
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Unknown" in str(call) for call in calls)

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_list_entry_no_year(self, mock_config, mock_search_class):
        """Test library list with entry having no year."""
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = [
            {
                "citation_key": "test2024author",
                "title": "Test Paper",
                "authors": ["Author"]
                # Missing year
            }
        ]
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            # Should show "n/d" for no year
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("n/d" in str(call) for call in calls)


class TestLibraryExportCommandEdgeCases:
    """Test library_export_command edge cases."""

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_export_invalid_format(self, mock_config, mock_search_class):
        """Test library export with invalid format (should be caught by argparse)."""
        # Note: argparse should prevent invalid formats, but test error handling
        mock_manager = Mock()
        mock_manager.export_library.side_effect = ValueError("Invalid format: xml")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.output = None
        args.format = "json"  # Valid format, but test ValueError handling
        
        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            with patch('sys.exit') as mock_exit:
                # Force ValueError by mocking export_library
                mock_manager.export_library.side_effect = ValueError("Invalid format")
                cli.library_export_command(args)
                mock_exit.assert_called_once_with(1)
                assert "Error:" in mock_stderr.getvalue()

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_export_file_io_error(self, mock_config, mock_search_class):
        """Test library export with file I/O error."""
        mock_manager = Mock()
        mock_manager.export_library.side_effect = IOError("Permission denied")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.output = "/invalid/path.json"
        args.format = "json"
        
        # IOError should propagate (not caught as ValueError)
        with pytest.raises(IOError, match="Permission denied"):
            cli.library_export_command(args)

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_export_path_conversion(self, mock_config, mock_search_class):
        """Test library export with Path conversion."""
        mock_manager = Mock()
        mock_manager.export_library.return_value = Path("/path/to/output.json")
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.output = "/custom/path.json"
        args.format = "json"
        
        with patch('builtins.print') as mock_print:
            cli.library_export_command(args)
            # Should convert string to Path
            call_args = mock_manager.export_library.call_args
            assert isinstance(call_args[0][0], Path)


class TestLibraryStatsCommandEdgeCases:
    """Test library_stats_command edge cases."""

    def test_library_stats_empty_stats(self, tmp_path, monkeypatch):
        """Test library stats with empty stats dictionary."""
        import os
        
        # Set environment variables to use tmp_path
        library_index_file = str(tmp_path / "library.json")
        bibtex_file = str(tmp_path / "refs.bib")
        download_dir = str(tmp_path / "pdfs")
        
        monkeypatch.setenv("LITERATURE_LIBRARY_INDEX", library_index_file)
        monkeypatch.setenv("LITERATURE_BIBTEX_FILE", bibtex_file)
        monkeypatch.setenv("LITERATURE_DOWNLOAD_DIR", download_dir)
        
        # Create empty library index JSON file
        index_path = Path(library_index_file)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        library_data = {
            "version": "1.0",
            "entries": {}
        }
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(library_data, f)
        
        # Create real args object
        args = argparse.Namespace()
        
        # Should handle missing keys gracefully
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        try:
            cli.library_stats_command(args)
            output = captured_output.getvalue()
            # Should print header
            assert "Library Statistics" in output
            assert "=" * 40 in output
            # Should handle missing keys gracefully (should show 0 for total_entries)
            assert "Total entries: 0" in output
        finally:
            sys.stdout = old_stdout

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_stats_only_oldest_year(self, mock_config, mock_search_class):
        """Test library stats with only oldest_year (no newest_year)."""
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {
            "total_entries": 10,
            "downloaded_pdfs": 5,
            "oldest_year": 2020
            # Missing newest_year
        }
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_stats_command(args)
            # Should not print year range if newest_year missing
            calls = [str(call) for call in mock_print.call_args_list]
            assert not any("Year range:" in str(call) for call in calls)

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_stats_only_newest_year(self, mock_config, mock_search_class):
        """Test library stats with only newest_year (no oldest_year)."""
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {
            "total_entries": 10,
            "downloaded_pdfs": 5,
            "newest_year": 2024
            # Missing oldest_year
        }
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_stats_command(args)
            # Should not print year range if oldest_year missing
            calls = [str(call) for call in mock_print.call_args_list]
            assert not any("Year range:" in str(call) for call in calls)

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_stats_many_years(self, mock_config, mock_search_class):
        """Test library stats with more than 10 years (should limit to 10)."""
        years = {str(year): 1 for year in range(2010, 2025)}  # 15 years
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {
            "total_entries": 15,
            "downloaded_pdfs": 5,
            "years": years
        }
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_stats_command(args)
            # Should only show first 10 years
            calls = [str(call) for call in mock_print.call_args_list]
            year_calls = [c for c in calls if any(year in c for year in years.keys())]
            # Should have at most 10 year entries
            assert len(year_calls) <= 10


class TestArgumentParsingEdgeCases:
    """Test argument parsing edge cases."""

    def test_main_invalid_command(self):
        """Test main with invalid command."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.literature.core.cli", "invalid_command"],
            capture_output=True,
            text=True
        )
        # argparse uses exit code 2 for invalid choices
        assert result.returncode == 2
        assert "error:" in result.stderr.lower() or "invalid choice" in result.stderr.lower()

    def test_main_library_no_subcommand(self):
        """Test main with library command but no subcommand."""
        with patch('sys.argv', ['cli.py', 'library']):
            with patch('sys.exit') as mock_exit:
                with patch('argparse.ArgumentParser.print_help') as mock_help:
                    cli.main()
                    mock_exit.assert_called_once_with(1)

    def test_main_search_no_query(self):
        """Test main function with search command but no query."""
        # argparse uses exit code 2 for missing required arguments
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.literature.core.cli", "search"],
            capture_output=True,
            text=True
        )
        # argparse uses exit code 2 for missing required arguments
        assert result.returncode == 2
        assert "error:" in result.stderr.lower() or "required" in result.stderr.lower()

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_search_command_multiple_papers(self, mock_config, mock_search_class):
        """Test search command with multiple papers."""
        papers = []
        for i in range(3):
            mock_paper = Mock()
            mock_paper.title = f"Paper {i+1}"
            mock_paper.authors = [f"Author {i+1}"]
            mock_paper.year = 2024
            mock_paper.doi = f"10.1234/paper{i+1}"
            mock_paper.citation_count = i * 10
            mock_paper.pdf_url = None
            papers.append(mock_paper)
        
        mock_manager = Mock()
        mock_manager.search.return_value = papers
        mock_manager.add_to_library.side_effect = [f"paper{i+1}2024author{i+1}" for i in range(3)]
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test"
        args.sources = None
        args.limit = 10
        args.download = False
        
        with patch('builtins.print') as mock_print:
            cli.search_command(args)
            # Should print all papers
            assert any("Paper 1" in str(call) for call in mock_print.call_args_list)
            assert any("Paper 2" in str(call) for call in mock_print.call_args_list)
            assert any("Paper 3" in str(call) for call in mock_print.call_args_list)
            assert any("Added 3 papers" in str(call) for call in mock_print.call_args_list)

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_search_command_paper_without_doi_or_citations(self, mock_config, mock_search_class):
        """Test search command with paper missing DOI and citations."""
        mock_paper = Mock()
        mock_paper.title = "Test Paper"
        mock_paper.authors = ["Author"]
        mock_paper.year = 2024
        mock_paper.doi = None
        mock_paper.citation_count = None
        mock_paper.pdf_url = None
        
        mock_manager = Mock()
        mock_manager.search.return_value = [mock_paper]
        mock_manager.add_to_library.return_value = "test2024author"
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        args.query = "test"
        args.sources = None
        args.limit = 10
        args.download = False
        
        with patch('builtins.print') as mock_print:
            cli.search_command(args)
            # Should not print DOI or Citations lines
            calls_str = ' '.join(str(call) for call in mock_print.call_args_list)
            assert "DOI:" not in calls_str
            assert "Citations:" not in calls_str

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_list_entry_without_doi(self, mock_config, mock_search_class):
        """Test library list entry without DOI."""
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = [
            {
                "citation_key": "test2024author",
                "title": "Test Paper",
                "authors": ["Author"],
                "year": 2024,
                "pdf_path": "/path/to/paper.pdf"
                # No DOI
            }
        ]
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            # Should not print DOI line
            calls_str = ' '.join(str(call) for call in mock_print.call_args_list)
            assert "DOI:" not in calls_str

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_list_single_author(self, mock_config, mock_search_class):
        """Test library list entry with single author (no 'et al.')."""
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = [
            {
                "citation_key": "test2024author",
                "title": "Test Paper",
                "authors": ["Single Author"],
                "year": 2024,
                "pdf_path": "/path/to/paper.pdf"
            }
        ]
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_list_command(args)
            # Should not have "et al."
            calls_str = ' '.join(str(call) for call in mock_print.call_args_list)
            assert "et al." not in calls_str
            assert "Single Author" in calls_str

    @patch('infrastructure.literature.core.cli.LiteratureSearch')
    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_stats_with_all_fields(self, mock_config, mock_search_class):
        """Test library stats with all optional fields present."""
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {
            "total_entries": 20,
            "downloaded_pdfs": 15,
            "oldest_year": 2018,
            "newest_year": 2024,
            "sources": {"arxiv": 12, "semanticscholar": 8},
            "years": {"2024": 8, "2023": 6, "2022": 4, "2021": 2}
        }
        mock_search_class.return_value = mock_manager
        
        args = Mock()
        
        with patch('builtins.print') as mock_print:
            cli.library_stats_command(args)
            calls_str = ' '.join(str(call) for call in mock_print.call_args_list)
            assert "Total entries: 20" in calls_str
            assert "Downloaded PDFs: 15" in calls_str
            assert "Year range: 2018 - 2024" in calls_str
            assert "By Source:" in calls_str
            assert "By Year" in calls_str

    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_list_uses_from_env_when_env_vars_set(self, mock_config_class, tmp_path, monkeypatch):
        """Test that library_list_command uses from_env() when env vars are set."""
        # Set environment variables
        monkeypatch.setenv("LITERATURE_LIBRARY_INDEX", str(tmp_path / "library.json"))
        monkeypatch.setenv("LITERATURE_BIBTEX_FILE", str(tmp_path / "refs.bib"))
        
        mock_from_env = Mock(return_value=Mock())
        mock_config_class.from_env = mock_from_env
        
        mock_manager = Mock()
        mock_manager.get_library_entries.return_value = []
        
        with patch('infrastructure.literature.core.cli.LiteratureSearch', return_value=mock_manager):
            args = Mock()
            cli.library_list_command(args)
            
            # Should have called from_env()
            mock_from_env.assert_called_once()

    @patch('infrastructure.literature.core.cli.LiteratureConfig')
    def test_library_stats_uses_from_env_when_env_vars_set(self, mock_config_class, tmp_path, monkeypatch):
        """Test that library_stats_command uses from_env() when env vars are set."""
        # Set environment variables
        monkeypatch.setenv("LITERATURE_LIBRARY_INDEX", str(tmp_path / "library.json"))
        
        mock_from_env = Mock(return_value=Mock())
        mock_config_class.from_env = mock_from_env
        
        mock_manager = Mock()
        mock_manager.get_library_stats.return_value = {"total_entries": 0}
        
        with patch('infrastructure.literature.core.cli.LiteratureSearch', return_value=mock_manager):
            args = Mock()
            cli.library_stats_command(args)
            
            # Should have called from_env()
            mock_from_env.assert_called_once()
        """Test main with search command but no query."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.literature.core.cli", "search"],
            capture_output=True,
            text=True
        )
        # argparse uses exit code 2 for missing required arguments
        assert result.returncode == 2
        assert "error:" in result.stderr.lower() or "required" in result.stderr.lower()
