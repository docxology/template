"""Comprehensive tests for infrastructure/literature/pdf_handler.py.

Tests PDF handling functionality with full coverage of all code paths.
Uses network isolation via patching for external HTTP requests.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import pytest
import requests

from infrastructure.literature.pdf_handler import PDFHandler
from infrastructure.literature.config import LiteratureConfig
from infrastructure.literature.api import SearchResult
from infrastructure.core.exceptions import FileOperationError, LiteratureSearchError


class TestPDFHandlerInit:
    """Test PDFHandler initialization."""

    def test_init_creates_download_directory(self, tmp_path):
        """Test that __init__ creates the download directory."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        
        handler = PDFHandler(config)
        
        assert download_dir.exists()
        assert handler.config == config

    def test_init_with_existing_directory(self, tmp_path):
        """Test initialization with existing download directory."""
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        config = LiteratureConfig(download_dir=str(download_dir))
        
        handler = PDFHandler(config)
        
        assert download_dir.exists()
        assert handler.config == config


class TestEnsureDownloadDir:
    """Test _ensure_download_dir method."""

    def test_ensure_download_dir_creates_directory(self, tmp_path):
        """Test that _ensure_download_dir creates the directory."""
        download_dir = tmp_path / "new_dir"
        config = LiteratureConfig(download_dir=str(download_dir))
        
        handler = PDFHandler(config)
        
        assert download_dir.exists()

    def test_ensure_download_dir_oserror(self, tmp_path):
        """Test _ensure_download_dir handles OSError (line 27-28)."""
        # Create a file where we want a directory
        blocking_file = tmp_path / "blocking"
        blocking_file.write_text("block")
        
        # Try to create a directory inside the file (impossible)
        invalid_path = str(blocking_file / "subdir")
        config = LiteratureConfig(download_dir=invalid_path)
        
        with pytest.raises(FileOperationError) as exc_info:
            PDFHandler(config)
        
        assert "Failed to create download directory" in str(exc_info.value)
        assert "path" in exc_info.value.context


class TestDownloadPdf:
    """Test download_pdf method."""

    def test_download_pdf_with_filename(self, tmp_path):
        """Test download_pdf with explicit filename."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir), timeout=5)
        handler = PDFHandler(config)
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF-1.4 content", b" more content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response) as mock_get:
            result = handler.download_pdf("https://example.com/paper", filename="test.pdf")
            
            assert result == download_dir / "test.pdf"
            assert result.exists()
            mock_get.assert_called_once()
            # Verify headers and timeout were passed
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs['timeout'] == 5
            assert "User-Agent" in call_kwargs['headers']

    def test_download_pdf_derives_filename_from_url(self, tmp_path):
        """Test download_pdf derives filename from URL (lines 43-44)."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF-1.4 content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            result = handler.download_pdf("https://arxiv.org/abs/2301.12345.pdf")
            
            assert result.name == "2301.12345.pdf"

    def test_download_pdf_adds_pdf_extension(self, tmp_path):
        """Test download_pdf adds .pdf extension if missing (lines 45-46)."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF-1.4 content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            result = handler.download_pdf("https://example.com/paper_without_extension")
            
            assert result.name == "paper_without_extension.pdf"

    def test_download_pdf_existing_file_returns_early(self, tmp_path):
        """Test download_pdf returns early if file exists (lines 50-52)."""
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        existing_pdf = download_dir / "existing.pdf"
        existing_pdf.write_bytes(b"%PDF-1.4 existing content")
        
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        with patch('infrastructure.literature.pdf_handler.requests.get') as mock_get:
            result = handler.download_pdf("https://example.com/existing.pdf", filename="existing.pdf")
            
            assert result == existing_pdf
            mock_get.assert_not_called()  # Should not make network request

    def test_download_pdf_network_error(self, tmp_path):
        """Test download_pdf handles network error (lines 71-75)."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        with patch('infrastructure.literature.pdf_handler.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
            
            with pytest.raises(LiteratureSearchError) as exc_info:
                handler.download_pdf("https://example.com/paper.pdf")
            
            assert "Failed to download PDF" in str(exc_info.value)
            assert "url" in exc_info.value.context
            assert "output_path" in exc_info.value.context

    def test_download_pdf_http_error(self, tmp_path):
        """Test download_pdf handles HTTP error status."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            with pytest.raises(LiteratureSearchError) as exc_info:
                handler.download_pdf("https://example.com/notfound.pdf")
            
            assert "Failed to download PDF" in str(exc_info.value)

    def test_download_pdf_connection_error(self, tmp_path):
        """Test download_pdf handles connection error."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        with patch('infrastructure.literature.pdf_handler.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
            
            with pytest.raises(LiteratureSearchError) as exc_info:
                handler.download_pdf("https://example.com/paper.pdf")
            
            assert "Failed to download PDF" in str(exc_info.value)

    def test_download_pdf_oserror_on_write(self, tmp_path):
        """Test download_pdf handles OSError on file write (lines 76-80)."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF-1.4 content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            with patch('builtins.open', side_effect=OSError("Disk full")):
                with pytest.raises(FileOperationError) as exc_info:
                    handler.download_pdf("https://example.com/paper.pdf")
                
                assert "Failed to write PDF file" in str(exc_info.value)
                assert "path" in exc_info.value.context

    def test_download_pdf_streaming_chunks(self, tmp_path):
        """Test download_pdf properly streams content in chunks (lines 65-67)."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        # Simulate multiple chunks
        chunks = [b"%PDF-1.4\n", b"object content\n", b"stream data\n", b"%%EOF"]
        mock_response = MagicMock()
        mock_response.iter_content.return_value = chunks
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            result = handler.download_pdf("https://example.com/large.pdf")
            
            # Verify all chunks were written
            content = result.read_bytes()
            assert content == b"%PDF-1.4\nobject content\nstream data\n%%EOF"


class TestExtractCitations:
    """Test extract_citations method."""

    def test_extract_citations_file_not_found(self, tmp_path):
        """Test extract_citations raises error for missing file (lines 88-89)."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        nonexistent_pdf = tmp_path / "nonexistent.pdf"
        
        with pytest.raises(FileOperationError) as exc_info:
            handler.extract_citations(nonexistent_pdf)
        
        assert "PDF file not found" in str(exc_info.value)
        assert "path" in exc_info.value.context

    def test_extract_citations_returns_empty_list(self, tmp_path):
        """Test extract_citations returns empty list (placeholder) (lines 91-92)."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        # Create a test PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest content\n%%EOF")
        
        result = handler.extract_citations(pdf_file)
        
        assert result == []
        assert isinstance(result, list)


class TestPDFHandlerIntegration:
    """Integration tests for PDFHandler."""

    def test_full_download_workflow(self, tmp_path):
        """Test complete download workflow."""
        download_dir = tmp_path / "literature" / "pdfs"
        config = LiteratureConfig(
            download_dir=str(download_dir),
            timeout=30,
            user_agent="Test-Agent/1.0"
        )
        
        handler = PDFHandler(config)
        
        # Verify directory was created
        assert download_dir.exists()
        
        # Mock successful download
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF-1.4 content\n%%EOF"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            pdf_path = handler.download_pdf(
                "https://arxiv.org/pdf/2301.12345.pdf",
                filename="arxiv_paper.pdf"
            )
        
        # Verify file was created
        assert pdf_path.exists()
        assert pdf_path.name == "arxiv_paper.pdf"
        
        # Test extract_citations on the downloaded file
        citations = handler.extract_citations(pdf_path)
        assert citations == []

    def test_config_values_used_correctly(self, tmp_path):
        """Test that config values are properly used in requests."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(
            download_dir=str(download_dir),
            timeout=42,
            user_agent="Custom-Agent/2.0"
        )
        
        handler = PDFHandler(config)
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response) as mock_get:
            handler.download_pdf("https://example.com/paper.pdf")
            
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs['timeout'] == 42
            assert call_kwargs['headers']['User-Agent'] == "Custom-Agent/2.0"
            assert call_kwargs['stream'] is True


class TestSetLibraryIndex:
    """Test set_library_index method."""

    def test_set_library_index(self, tmp_path):
        """Test setting library index after initialization."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        # Initially no library index
        assert handler._library_index is None
        
        # Set library index
        mock_index = MagicMock()
        handler.set_library_index(mock_index)
        
        assert handler._library_index is mock_index

    def test_init_with_library_index(self, tmp_path):
        """Test initialization with library index."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        mock_index = MagicMock()
        
        handler = PDFHandler(config, library_index=mock_index)
        
        assert handler._library_index is mock_index


class TestDownloadPdfWithSearchResult:
    """Test download_pdf with SearchResult parameter."""

    def test_download_with_result_and_library_index(self, tmp_path):
        """Test download uses citation key from library index."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        
        mock_index = MagicMock()
        mock_index.generate_citation_key.return_value = "smith2024machine"
        
        handler = PDFHandler(config, library_index=mock_index)
        
        result = SearchResult(
            title="Machine Learning Methods",
            authors=["John Smith"],
            year=2024,
            abstract="An abstract",
            url="https://example.com/paper",
            pdf_url="https://example.com/paper.pdf"
        )
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            pdf_path = handler.download_pdf("https://example.com/paper.pdf", result=result)
        
        assert pdf_path.name == "smith2024machine.pdf"
        mock_index.generate_citation_key.assert_called_once_with(
            "Machine Learning Methods", ["John Smith"], 2024
        )
        mock_index.update_pdf_path.assert_called()

    def test_download_with_result_no_library_index(self, tmp_path):
        """Test download generates filename from result when no library index."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Deep Learning Methods",
            authors=["Jane Doe"],
            year=2023,
            abstract="An abstract",
            url="https://example.com/paper",
            pdf_url="https://example.com/paper.pdf"
        )
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            pdf_path = handler.download_pdf("https://example.com/paper.pdf", result=result)
        
        # Should use _generate_filename_from_result
        assert pdf_path.name == "doe2023deep.pdf"

    def test_download_existing_file_updates_library_index(self, tmp_path, monkeypatch):
        """Test existing file updates library index path."""
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        existing_pdf = download_dir / "existing.pdf"
        existing_pdf.write_bytes(b"%PDF content")
        
        # Change to tmp_path so relative path works
        monkeypatch.chdir(tmp_path)
        
        config = LiteratureConfig(download_dir=str(download_dir))
        mock_index = MagicMock()
        handler = PDFHandler(config, library_index=mock_index)
        
        result = SearchResult(
            title="Test Paper",
            authors=["Test Author"],
            year=2024,
            abstract="Abstract",
            url="https://example.com",
            pdf_url="https://example.com/paper.pdf"
        )
        
        with patch('infrastructure.literature.pdf_handler.requests.get') as mock_get:
            pdf_path = handler.download_pdf("https://example.com/paper.pdf", 
                                           filename="existing.pdf", 
                                           result=result)
            mock_get.assert_not_called()  # Should not download
        
        # Should update library index with path
        mock_index.update_pdf_path.assert_called_once()

    def test_download_updates_library_index_with_relative_path(self, tmp_path):
        """Test download updates library index with path."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        
        mock_index = MagicMock()
        mock_index.generate_citation_key.return_value = "paper2024test"
        
        handler = PDFHandler(config, library_index=mock_index)
        
        result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="https://example.com",
            pdf_url="https://example.com/paper.pdf"
        )
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            handler.download_pdf("https://example.com/paper.pdf", result=result)
        
        # Should call update_pdf_path with citation key
        mock_index.update_pdf_path.assert_called()
        call_args = mock_index.update_pdf_path.call_args
        assert call_args[0][0] == "paper2024test"


class TestGenerateFilenameFromResult:
    """Test _generate_filename_from_result method."""

    def test_generate_filename_basic(self, tmp_path):
        """Test basic filename generation."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Novel Machine Learning Approach",
            authors=["John Smith"],
            year=2024,
            abstract="Abstract",
            url="https://example.com"
        )
        
        filename = handler._generate_filename_from_result(result)
        
        assert filename == "smith2024novel.pdf"

    def test_generate_filename_no_authors(self, tmp_path):
        """Test filename generation with no authors."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Novel Methods",
            authors=[],
            year=2024,
            abstract="Abstract",
            url="https://example.com"
        )
        
        filename = handler._generate_filename_from_result(result)
        
        assert filename == "anonymous2024novel.pdf"

    def test_generate_filename_no_year(self, tmp_path):
        """Test filename generation with no year."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Novel Methods",
            authors=["Jane Doe"],
            year=None,
            abstract="Abstract",
            url="https://example.com"
        )
        
        filename = handler._generate_filename_from_result(result)
        
        assert "doe" in filename
        assert "nodate" in filename
        assert filename.endswith(".pdf")

    def test_generate_filename_skips_stop_words(self, tmp_path):
        """Test filename generation skips common stop words."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="A Study on the Effects of Machine Learning",
            authors=["John Smith"],
            year=2024,
            abstract="Abstract",
            url="https://example.com"
        )
        
        filename = handler._generate_filename_from_result(result)
        
        # Should skip "A", "on", "the" and use "study"
        assert "study" in filename

    def test_generate_filename_sanitizes_author(self, tmp_path):
        """Test filename generation sanitizes special characters."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Novel Methods",
            authors=["John O'Brien-Smith, Jr."],
            year=2024,
            abstract="Abstract",
            url="https://example.com"
        )
        
        filename = handler._generate_filename_from_result(result)
        
        # Should sanitize to alphanumeric only
        assert ".pdf" in filename
        assert "'" not in filename
        assert "-" not in filename


class TestDownloadPaper:
    """Test download_paper convenience method."""

    def test_download_paper_with_pdf_url(self, tmp_path):
        """Test download_paper with valid pdf_url."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="https://example.com",
            pdf_url="https://example.com/paper.pdf"
        )
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            pdf_path = handler.download_paper(result)
        
        assert pdf_path is not None
        assert pdf_path.exists()

    def test_download_paper_no_pdf_url(self, tmp_path):
        """Test download_paper returns None when no pdf_url."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="https://example.com",
            pdf_url=None  # No PDF URL
        )
        
        pdf_path = handler.download_paper(result)
        
        assert pdf_path is None

    def test_download_paper_empty_pdf_url(self, tmp_path):
        """Test download_paper returns None for empty pdf_url."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="https://example.com",
            pdf_url=""  # Empty PDF URL
        )
        
        pdf_path = handler.download_paper(result)
        
        assert pdf_path is None


class TestLibraryIndexIntegration:
    """Test library index integration paths."""

    def test_download_with_path_relative_to_cwd(self, tmp_path, monkeypatch):
        """Test relative path calculation when inside cwd."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        
        # Change to temp directory so relative path works
        monkeypatch.chdir(tmp_path)
        
        mock_index = MagicMock()
        mock_index.generate_citation_key.return_value = "test2024paper"
        
        handler = PDFHandler(config, library_index=mock_index)
        
        result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="https://example.com",
            pdf_url="https://example.com/paper.pdf"
        )
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            handler.download_pdf("https://example.com/paper.pdf", result=result)
        
        # Should have called update_pdf_path with relative path
        mock_index.update_pdf_path.assert_called()
        call_args = mock_index.update_pdf_path.call_args[0]
        assert "downloads/test2024paper.pdf" in call_args[1]

    def test_download_with_path_outside_cwd(self, tmp_path, monkeypatch):
        """Test absolute path when output is outside cwd."""
        download_dir = tmp_path / "downloads"
        config = LiteratureConfig(download_dir=str(download_dir))
        
        # Set cwd to a different location
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        monkeypatch.chdir(other_dir)
        
        mock_index = MagicMock()
        mock_index.generate_citation_key.return_value = "test2024paper"
        
        handler = PDFHandler(config, library_index=mock_index)
        
        result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="https://example.com",
            pdf_url="https://example.com/paper.pdf"
        )
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"%PDF content"]
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.literature.pdf_handler.requests.get', return_value=mock_response):
            handler.download_pdf("https://example.com/paper.pdf", result=result)
        
        # Should have called update_pdf_path (path can be absolute or relative)
        mock_index.update_pdf_path.assert_called()

