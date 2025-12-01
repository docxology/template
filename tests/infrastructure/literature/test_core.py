import pytest
from pathlib import Path
from unittest.mock import MagicMock
from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.api import SearchResult

def test_search_integration(mock_config, mocker):
    # Mock sources
    mock_arxiv = mocker.patch("infrastructure.literature.core.ArxivSource")
    mock_ss = mocker.patch("infrastructure.literature.core.SemanticScholarSource")
    
    mock_arxiv_instance = mock_arxiv.return_value
    mock_ss_instance = mock_ss.return_value
    
    mock_arxiv_instance.search.return_value = [
        SearchResult("Title 1", ["Auth"], 2023, "Abs", "url1", "doi1", "arxiv")
    ]
    mock_ss_instance.search.return_value = [
        SearchResult("Title 1", ["Auth"], 2023, "Abs", "url1", "doi1", "ss"), # Duplicate
        SearchResult("Title 2", ["Auth"], 2023, "Abs", "url2", "doi2", "ss")
    ]

    searcher = LiteratureSearch(mock_config)
    results = searcher.search("query")

    assert len(results) == 2  # Deduplicated
    assert {r.title for r in results} == {"Title 1", "Title 2"}

def test_download_paper(mock_config, sample_result, mocker):
    mock_pdf_handler = mocker.patch("infrastructure.literature.core.PDFHandler")
    mock_handler_instance = mock_pdf_handler.return_value
    mock_handler_instance.download_pdf.return_value = Path("test.pdf")

    searcher = LiteratureSearch(mock_config)
    path = searcher.download_paper(sample_result)

    assert path == Path("test.pdf")
    # Now passes result for citation key naming
    mock_handler_instance.download_pdf.assert_called_with(sample_result.pdf_url, result=sample_result)

def test_add_to_library(mock_config, sample_result, mocker):
    mock_ref_manager = mocker.patch("infrastructure.literature.core.ReferenceManager")
    mock_manager_instance = mock_ref_manager.return_value
    mock_manager_instance.add_reference.return_value = "Key2023"

    searcher = LiteratureSearch(mock_config)
    key = searcher.add_to_library(sample_result)

    assert key == "Key2023"
    mock_manager_instance.add_reference.assert_called_with(sample_result)

