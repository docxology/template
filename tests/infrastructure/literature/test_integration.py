import pytest
from pathlib import Path
from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.reference_manager import ReferenceManager
from infrastructure.literature.pdf_handler import PDFHandler

def test_full_workflow(mock_config, sample_result, mocker):
    # Setup mocks
    mocker.patch.object(PDFHandler, "download_pdf", return_value=Path("test.pdf"))
    
    # Initialize
    searcher = LiteratureSearch(mock_config)
    
    # 1. Add to library
    key = searcher.add_to_library(sample_result)
    # Key format: last_name + year + first_word_of_title (sanitized)
    # "Author One" -> "one", year=2023, "Test" -> "test"
    assert key == "one2023test"
    
    # Verify bib file
    bib_content = Path(mock_config.bibtex_file).read_text()
    assert "@article{one2023test" in bib_content
    assert "title={Test Paper}" in bib_content
    
    # 2. Download PDF
    path = searcher.download_paper(sample_result)
    assert path == Path("test.pdf")

def test_reference_manager_deduplication(mock_config, sample_result):
    manager = ReferenceManager(mock_config)
    
    # Add twice
    key1 = manager.add_reference(sample_result)
    key2 = manager.add_reference(sample_result)
    
    assert key1 == key2
    
    # Check file only has one entry
    bib_content = Path(mock_config.bibtex_file).read_text()
    assert bib_content.count("@article") == 1

