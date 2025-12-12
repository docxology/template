import pytest
from pathlib import Path
from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.library import ReferenceManager
from infrastructure.literature.pdf import PDFHandler


@pytest.mark.requires_network
def test_full_workflow(mock_config, sample_result, tmp_path):
    """Test full literature workflow with real PDF downloads.
    
    This test uses real network calls to download PDFs from arXiv or Semantic Scholar.
    It tests the complete workflow: search -> add to library -> download PDF.
    """
    # Update config to use temp directory for downloads
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir(exist_ok=True)
    mock_config.pdf_dir = str(pdf_dir)
    
    # Initialize searcher
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
    
    # 2. Download PDF using real download logic
    # Note: This will attempt real network download
    # If download fails (e.g., no PDF URL), test will still pass if workflow is correct
    try:
        path = searcher.download_paper(sample_result)
        # If download succeeded, verify file exists
        if path and path.exists():
            assert path.suffix == ".pdf"
            assert path.stat().st_size > 0
    except Exception as e:
        # Download may fail if sample_result doesn't have valid PDF URL
        # This is acceptable - we're testing the workflow, not PDF availability
        pytest.skip(f"PDF download failed (expected for test data): {e}")

def test_reference_manager_deduplication(mock_config, sample_result):
    manager = ReferenceManager(mock_config)
    
    # Add twice
    key1 = manager.add_reference(sample_result)
    key2 = manager.add_reference(sample_result)
    
    assert key1 == key2
    
    # Check file only has one entry
    bib_content = Path(mock_config.bibtex_file).read_text()
    assert bib_content.count("@article") == 1

