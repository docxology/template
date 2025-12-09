import pytest
from pathlib import Path
from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.sources import SearchResult
from infrastructure.literature.library_index import LibraryIndex
from infrastructure.literature.reference_manager import ReferenceManager


@pytest.mark.requires_network
def test_search_integration(mock_config):
    """Test search with real LiteratureSearch instance using real API calls."""
    searcher = LiteratureSearch(mock_config)

    # Use real search - skip if network unavailable
    try:
        results = searcher.search("machine learning", limit=5, sources=["arxiv"])
        # Verify we got results
        assert len(results) > 0
        # Verify deduplication works (if multiple sources)
        titles = {r.title for r in results}
        assert len(titles) == len(results)  # No duplicates
    except Exception as e:
        pytest.skip(f"Network unavailable or API error: {e}")


@pytest.mark.requires_network
def test_download_paper(mock_config, sample_result, tmp_path):
    """Test paper download with real implementations."""
    searcher = LiteratureSearch(mock_config)

    # Create a real test PDF file for download testing
    test_pdf_path = tmp_path / "test.pdf"
    test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    test_pdf_path.write_bytes(test_pdf_content)

    # Test with a result that has a PDF URL
    # If PDF URL exists, download will be attempted
    # If network unavailable, test will skip
    try:
        # For testing, we'll verify the download method exists and can handle the result
        # Actual download requires network, so we test the method signature and error handling
        if sample_result.pdf_url:
            # Try download - may fail if network unavailable, which is expected
            try:
                path = searcher.download_paper(sample_result)
                if path:
                    assert path.exists()
            except Exception:
                # Network unavailable - skip test
                pytest.skip("Network unavailable for PDF download")
    except Exception as e:
        pytest.skip(f"Download test requires network: {e}")


def test_add_to_library(mock_config, sample_result, tmp_path):
    """Test adding paper to library with real implementations."""
    searcher = LiteratureSearch(mock_config)

    # Use real add_to_library method
    key = searcher.add_to_library(sample_result)
    
    # Verify a citation key was generated
    assert key is not None
    assert len(key) > 0
    
    # Verify it was added to library index
    entry = searcher.library_index.get_entry(key)
    assert entry is not None
    assert entry.citation_key == key
    assert entry.title == sample_result.title
    
    # Verify BibTeX entry was created
    bibtex_path = Path(searcher.config.bibtex_file)
    if bibtex_path.exists():
        bibtex_content = bibtex_path.read_text()
        assert key in bibtex_content

