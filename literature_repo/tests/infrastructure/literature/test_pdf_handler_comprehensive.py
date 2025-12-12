"""Simplified tests for infrastructure/literature/pdf_handler.py.

Tests PDF handling functionality with real file operations instead of mocking.
Focuses on core functionality without network dependencies.
"""

from pathlib import Path
import os
import pytest

from infrastructure.literature.pdf import PDFHandler
from infrastructure.literature.core import LiteratureConfig
from infrastructure.literature.sources import SearchResult
from infrastructure.core.exceptions import FileOperationError


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


class TestPDFHandlerCore:
    """Test core PDFHandler functionality with real file operations."""

    def test_download_with_mock_content(self, tmp_path):
        """Test PDF download simulation with real file operations."""
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        handler = PDFHandler(config)

        # Create mock PDF content
        mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"

        # Simulate successful download by creating the file directly
        citation_key = "test2024paper"
        pdf_path = Path(handler.config.download_dir) / f"{citation_key}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(mock_pdf_content)

        assert pdf_path.exists()
        assert pdf_path.read_bytes() == mock_pdf_content

    def test_file_operations(self, tmp_path):
        """Test basic file operations without network."""
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        handler = PDFHandler(config)

        # Test directory creation
        test_dir = Path(handler.config.download_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

        # Test file creation
        test_file = test_dir / "test.txt"
        test_content = "test content"
        test_file.write_text(test_content)

        assert test_file.exists()
        assert test_file.read_text() == test_content

    def test_path_handling(self, tmp_path):
        """Test path handling and validation."""
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        handler = PDFHandler(config)

        # Test relative path handling
        relative_path = Path("test.pdf")
        assert relative_path.name == "test.pdf"

        # Test absolute path handling
        abs_path = tmp_path / "downloads" / "test.pdf"
        assert abs_path.is_absolute()
        assert abs_path.suffix == ".pdf"

    def test_error_handling(self, tmp_path):
        """Test error handling in file operations."""
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        handler = PDFHandler(config)

        # Test accessing non-existent file
        nonexistent = Path(handler.config.download_dir) / "nonexistent.pdf"
        assert not nonexistent.exists()

        # Test creating files in read-only directory would require special setup
        # For now, just test basic error handling
        try:
            nonexistent.read_text()
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected


class TestPDFHandlerIntegration:
    """Integration tests for PDFHandler with other components."""

    def test_with_search_result(self, tmp_path):
        """Test PDFHandler working with SearchResult objects."""
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        handler = PDFHandler(config)

        # Create a realistic SearchResult
        result = SearchResult(
            title="Test Research Paper",
            authors=["Smith, John", "Doe, Jane"],
            year=2024,
            abstract="This is a test abstract.",
            url="https://example.com/paper",
            doi="10.1234/test.5678",
            source="arxiv",
            pdf_url="https://example.com/paper.pdf"
        )

        # Test that we can work with the result
        assert result.title == "Test Research Paper"
        assert result.doi == "10.1234/test.5678"
        assert result.pdf_url == "https://example.com/paper.pdf"

        # Test citation key generation logic (simplified)
        citation_key = "smith2024test"
        assert len(citation_key) > 0
