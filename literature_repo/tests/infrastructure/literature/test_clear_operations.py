"""Tests for infrastructure.literature.library.clear module.

Comprehensive tests for clear operations including PDF clearing,
summary clearing, and complete library clearing.
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from infrastructure.literature.library import (
    clear_pdfs,
    clear_summaries,
    clear_library,
)


class TestClearPdfs:
    """Test clear_pdfs function."""

    def test_clear_pdfs_nonexistent_directory(self, tmp_path, monkeypatch):
        """Test clearing PDFs when directory doesn't exist."""
        # Mock Path to return tmp_path for data/pdfs
        def mock_path(path_str):
            if path_str == "data/pdfs":
                return tmp_path / "pdfs"
            return Path(path_str)
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            result = clear_pdfs(confirm=False)
        
        assert result['success'] is True
        assert result['files_removed'] == 0
        assert result['size_freed_mb'] == 0.0
        assert "does not exist" in result['message']

    def test_clear_pdfs_no_files(self, tmp_path, monkeypatch):
        """Test clearing PDFs when directory exists but is empty."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        
        def mock_path(path_str):
            if path_str == "data/pdfs":
                return pdf_dir
            return Path(path_str)
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            with patch('infrastructure.literature.library.clear.LiteratureConfig') as mock_config:
                result = clear_pdfs(confirm=False)
        
        assert result['success'] is True
        assert result['files_removed'] == 0
        assert result['size_freed_mb'] == 0.0
        assert "No PDFs to clear" in result['message']

    def test_clear_pdfs_with_files(self, tmp_path, monkeypatch):
        """Test clearing PDFs with existing files."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        
        # Create test PDF files
        pdf1 = pdf_dir / "paper1.pdf"
        pdf1.write_bytes(b"pdf content 1" * 100)  # ~1.3 KB
        pdf2 = pdf_dir / "paper2.pdf"
        pdf2.write_bytes(b"pdf content 2" * 100)
        
        def mock_path(path_str):
            if path_str == "data/pdfs":
                return pdf_dir
            return Path(path_str)
        
        mock_entry = Mock()
        mock_entry.citation_key = "test2024"
        mock_entry.pdf_path = "data/pdfs/paper1.pdf"
        
        mock_library_index = Mock()
        mock_library_index.list_entries.return_value = [mock_entry]
        mock_library_index.update_pdf_path = Mock()
        
        mock_config = Mock()
        mock_config.from_env.return_value = mock_config
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            with patch('infrastructure.literature.library.clear.LiteratureConfig', return_value=mock_config):
                with patch('infrastructure.literature.library.clear.LibraryIndex', return_value=mock_library_index):
                    result = clear_pdfs(confirm=False)
        
        assert result['success'] is True
        assert result['files_removed'] == 2
        assert result['size_freed_mb'] > 0
        assert not pdf1.exists()
        assert not pdf2.exists()
        assert mock_library_index.update_pdf_path.called

    def test_clear_pdfs_interactive_cancelled(self, tmp_path, monkeypatch):
        """Test interactive mode with cancellation."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_bytes(b"content")
        
        def mock_path(path_str):
            if path_str == "data/pdfs":
                return pdf_dir
            return Path(path_str)
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            with patch('builtins.input', return_value='n'):
                result = clear_pdfs(confirm=True, interactive=True)
        
        assert result['success'] is False
        assert result['files_removed'] == 0
        assert "cancelled" in result['message'].lower()

    def test_clear_pdfs_interactive_confirmed(self, tmp_path, monkeypatch):
        """Test interactive mode with confirmation."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_bytes(b"content")
        
        def mock_path(path_str):
            if path_str == "data/pdfs":
                return pdf_dir
            return Path(path_str)
        
        mock_entry = Mock()
        mock_entry.citation_key = "test2024"
        mock_entry.pdf_path = None
        
        mock_library_index = Mock()
        mock_library_index.list_entries.return_value = [mock_entry]
        mock_library_index.update_pdf_path = Mock()
        
        mock_config = Mock()
        mock_config.from_env.return_value = mock_config
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            with patch('infrastructure.literature.library.clear.LiteratureConfig', return_value=mock_config):
                with patch('infrastructure.literature.library.clear.LibraryIndex', return_value=mock_library_index):
                    with patch('builtins.input', return_value='y'):
                        result = clear_pdfs(confirm=True, interactive=True)
        
        assert result['success'] is True
        assert result['files_removed'] == 1


class TestClearSummaries:
    """Test clear_summaries function."""

    def test_clear_summaries_nonexistent_directory(self, tmp_path, monkeypatch):
        """Test clearing summaries when directory doesn't exist."""
        def mock_path(path_str):
            if path_str == "data/summaries":
                return tmp_path / "summaries"
            return Path(path_str)
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            result = clear_summaries(confirm=False)
        
        assert result['success'] is True
        assert result['files_removed'] == 0
        assert "does not exist" in result['message']

    def test_clear_summaries_no_files(self, tmp_path, monkeypatch):
        """Test clearing summaries when directory is empty."""
        summaries_dir = tmp_path / "summaries"
        summaries_dir.mkdir()
        
        def mock_path(path_str):
            if path_str == "data/summaries":
                return summaries_dir
            return Path(path_str)
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            result = clear_summaries(confirm=False)
        
        assert result['success'] is True
        assert result['files_removed'] == 0
        assert "No summaries to clear" in result['message']

    def test_clear_summaries_with_files(self, tmp_path, monkeypatch):
        """Test clearing summaries with existing files."""
        summaries_dir = tmp_path / "summaries"
        summaries_dir.mkdir()
        
        summary1 = summaries_dir / "paper1_summary.md"
        summary1.write_text("# Summary 1")
        summary2 = summaries_dir / "paper2_summary.md"
        summary2.write_text("# Summary 2")
        
        def mock_path(path_str):
            if path_str == "data/summaries":
                return summaries_dir
            return Path(path_str)
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            result = clear_summaries(confirm=False)
        
        assert result['success'] is True
        assert result['files_removed'] == 2
        assert result['size_freed_mb'] >= 0
        assert not summary1.exists()
        assert not summary2.exists()

    def test_clear_summaries_interactive_cancelled(self, tmp_path, monkeypatch):
        """Test interactive mode with cancellation."""
        summaries_dir = tmp_path / "summaries"
        summaries_dir.mkdir()
        (summaries_dir / "paper_summary.md").write_text("# Summary")
        
        def mock_path(path_str):
            if path_str == "data/summaries":
                return summaries_dir
            return Path(path_str)
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            with patch('builtins.input', return_value='n'):
                result = clear_summaries(confirm=True, interactive=True)
        
        assert result['success'] is False
        assert result['files_removed'] == 0
        assert "cancelled" in result['message'].lower()


class TestClearLibrary:
    """Test clear_library function."""

    def test_clear_library_already_empty(self, tmp_path, monkeypatch):
        """Test clearing library when already empty."""
        def mock_path(path_str):
            paths = {
                "data/pdfs": tmp_path / "pdfs",
                "data/summaries": tmp_path / "summaries",
                "literature/summarization_progress.json": tmp_path / "progress.json",
                "data/references.bib": tmp_path / "references.bib"
            }
            return paths.get(path_str, Path(path_str))
        
        mock_entry = Mock()
        mock_entry.citation_key = "test2024"
        
        mock_library_index = Mock()
        mock_library_index.list_entries.return_value = []
        mock_library_index.remove_entry = Mock()
        
        mock_config = Mock()
        mock_config.from_env.return_value = mock_config
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            with patch('infrastructure.literature.library.clear.LiteratureConfig', return_value=mock_config):
                with patch('infrastructure.literature.library.clear.LibraryIndex', return_value=mock_library_index):
                    result = clear_library(confirm=False)
        
        assert result['success'] is True
        assert result['entries_removed'] == 0
        assert result['pdfs_removed'] == 0
        assert result['summaries_removed'] == 0
        assert "already empty" in result['message'].lower()

    def test_clear_library_complete(self, tmp_path, monkeypatch):
        """Test complete library clearing."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        pdf1 = pdf_dir / "paper1.pdf"
        pdf1.write_bytes(b"pdf content")
        
        summaries_dir = tmp_path / "summaries"
        summaries_dir.mkdir()
        summary1 = summaries_dir / "paper1_summary.md"
        summary1.write_text("# Summary")
        
        progress_file = tmp_path / "progress.json"
        progress_file.write_text('{}')
        
        bibtex_file = tmp_path / "references.bib"
        bibtex_file.write_text("@article{test2024}")
        
        def mock_path(path_str):
            paths = {
                "data/pdfs": pdf_dir,
                "data/summaries": summaries_dir,
                "literature/summarization_progress.json": progress_file,
                "data/references.bib": bibtex_file
            }
            return paths.get(path_str, Path(path_str))
        
        mock_entry = Mock()
        mock_entry.citation_key = "test2024"
        
        mock_library_index = Mock()
        mock_library_index.list_entries.return_value = [mock_entry]
        mock_library_index.remove_entry = Mock()
        
        mock_config = Mock()
        mock_config.from_env.return_value = mock_config
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            with patch('infrastructure.literature.library.clear.LiteratureConfig', return_value=mock_config):
                with patch('infrastructure.literature.library.clear.LibraryIndex', return_value=mock_library_index):
                    result = clear_library(confirm=False)
        
        assert result['success'] is True
        assert result['entries_removed'] == 1
        assert result['pdfs_removed'] == 1
        assert result['summaries_removed'] == 1
        assert result['progress_file_removed'] is True
        assert result['bibtex_file_removed'] is True
        assert not pdf1.exists()
        assert not summary1.exists()
        assert not progress_file.exists()
        assert not bibtex_file.exists()
        assert mock_library_index.remove_entry.called

    def test_clear_library_interactive_cancelled(self, tmp_path, monkeypatch):
        """Test interactive mode with cancellation."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_bytes(b"content")
        
        def mock_path(path_str):
            paths = {
                "data/pdfs": pdf_dir,
                "data/summaries": tmp_path / "summaries",
                "literature/summarization_progress.json": tmp_path / "progress.json",
                "data/references.bib": tmp_path / "references.bib"
            }
            return paths.get(path_str, Path(path_str))
        
        mock_entry = Mock()
        mock_entry.citation_key = "test2024"
        
        mock_library_index = Mock()
        mock_library_index.list_entries.return_value = [mock_entry]
        
        mock_config = Mock()
        mock_config.from_env.return_value = mock_config
        
        with patch('infrastructure.literature.library.clear.Path', side_effect=mock_path):
            with patch('infrastructure.literature.library.clear.LiteratureConfig', return_value=mock_config):
                with patch('infrastructure.literature.library.clear.LibraryIndex', return_value=mock_library_index):
                    with patch('builtins.input', return_value='n'):
                        result = clear_library(confirm=True, interactive=True)
        
        assert result['success'] is False
        assert result['entries_removed'] == 0
        assert "cancelled" in result['message'].lower()

    def test_clear_library_error_handling(self, tmp_path, monkeypatch):
        """Test error handling in clear_library."""
        # Force an exception by making LiteratureConfig.from_env() raise
        with patch('infrastructure.literature.library.clear.LiteratureConfig') as mock_config:
            mock_config.from_env.side_effect = Exception("Test error")
            result = clear_library(confirm=False)
        
        assert result['success'] is False
        assert "Error" in result['message'] or "error" in result['message'].lower()
        assert result['entries_removed'] == 0



