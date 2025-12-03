import pytest
from pathlib import Path
from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.api import SearchResult
from infrastructure.literature.library_index import LibraryIndex
from infrastructure.literature.reference_manager import ReferenceManager


def test_search_integration(mock_config):
    """Test search with real LiteratureSearch instance."""
    searcher = LiteratureSearch(mock_config)

    # Mock the source search methods to return test data
    def mock_arxiv_search(query, limit=10):
        return [SearchResult("Title 1", ["Auth"], 2023, "Abs", "url1", "doi1", "arxiv")]

    def mock_ss_search(query, limit=10):
        return [
            SearchResult("Title 1", ["Auth"], 2023, "Abs", "url1", "doi1", "ss"),  # Duplicate
            SearchResult("Title 2", ["Auth"], 2023, "Abs", "url2", "doi2", "ss")
        ]

    # Replace the source methods
    original_arxiv_search = searcher.sources['arxiv'].search
    original_ss_search = searcher.sources['semanticscholar'].search

    searcher.sources['arxiv'].search = mock_arxiv_search
    searcher.sources['semanticscholar'].search = mock_ss_search

    try:
        results = searcher.search("query")
        assert len(results) == 2  # Deduplicated
        assert {r.title for r in results} == {"Title 1", "Title 2"}
    finally:
        # Restore original methods
        searcher.sources['arxiv'].search = original_arxiv_search
        searcher.sources['semanticscholar'].search = original_ss_search


def test_download_paper(mock_config, sample_result, tmp_path):
    """Test paper download with real implementations."""
    searcher = LiteratureSearch(mock_config)

    # Mock the PDF handler's download_pdf method
    original_download_pdf = searcher.pdf_handler.download_pdf

    def mock_download_pdf(url, filename=None, result=None):
        # Create a test PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("mock pdf content")
        return pdf_path

    searcher.pdf_handler.download_pdf = mock_download_pdf

    try:
        path = searcher.download_paper(sample_result)
        assert path.name == "test.pdf"
        assert path.exists()
    finally:
        # Restore original method
        searcher.pdf_handler.download_pdf = original_download_pdf


def test_add_to_library(mock_config, sample_result, tmp_path):
    """Test adding paper to library with real implementations."""
    searcher = LiteratureSearch(mock_config)

    # Mock the reference manager's add_reference method
    original_add_reference = searcher.reference_manager.add_reference

    def mock_add_reference(result):
        return "Key2023"

    searcher.reference_manager.add_reference = mock_add_reference

    try:
        key = searcher.add_to_library(sample_result)
        assert key == "Key2023"
    finally:
        # Restore original method
        searcher.reference_manager.add_reference = original_add_reference

