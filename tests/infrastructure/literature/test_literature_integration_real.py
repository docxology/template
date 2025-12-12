"""Real integration tests for literature search module.

These tests use real API calls, real PDF downloads, and real library operations
to verify complete functionality. Requires network access and may take time.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from infrastructure.literature.core import LiteratureSearch, LiteratureConfig
from infrastructure.literature.library import LibraryIndex
from infrastructure.literature.sources import SearchResult


@pytest.mark.integration
@pytest.mark.requires_network
class TestRealLiteratureSearch:
    """Real literature search tests with actual API calls."""

    @pytest.fixture
    def real_config(self, tmp_path):
        """Create real test configuration."""
        config = LiteratureConfig()
        config.download_dir = str(tmp_path / "pdfs")
        config.bibtex_file = str(tmp_path / "references.bib")
        config.library_index_file = str(tmp_path / "library.json")
        config.arxiv_delay = 1.0  # Realistic delay for real API
        config.semanticscholar_delay = 0.5
        config.retry_attempts = 2
        config.sources = ["arxiv", "semanticscholar"]
        return config

    def test_real_search_arxiv(self, real_config):
        """Test real arXiv search."""
        searcher = LiteratureSearch(real_config)
        
        # Search for a well-known paper
        results = searcher.search("active inference", limit=5, sources=["arxiv"])
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.source == "arxiv" for r in results)
        assert all(r.title for r in results)
        assert all(r.authors for r in results)

    def test_real_search_semanticscholar(self, real_config):
        """Test real Semantic Scholar search."""
        searcher = LiteratureSearch(real_config)
        
        results = searcher.search("machine learning", limit=5, sources=["semanticscholar"])
        
        # If no results due to rate limiting or API errors, skip the test
        if len(results) == 0:
            pytest.skip("Semantic Scholar API unavailable or rate limited (no results returned)")
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.source == "semanticscholar" for r in results)
        assert all(r.title for r in results)

    def test_real_search_multiple_sources(self, real_config):
        """Test real search across multiple sources."""
        searcher = LiteratureSearch(real_config)
        
        results = searcher.search("neural networks", limit=3)
        
        assert len(results) > 0
        sources = {r.source for r in results}
        assert len(sources) > 0  # Should get results from at least one source

    def test_real_search_with_statistics(self, real_config):
        """Test real search with statistics."""
        searcher = LiteratureSearch(real_config)
        
        results, stats = searcher.search("deep learning", limit=5, return_stats=True)
        
        assert len(results) > 0
        assert stats.total_results > 0
        assert len(stats.source_stats) > 0
        assert stats.total_time > 0


@pytest.mark.integration
@pytest.mark.requires_network
class TestRealPDFDownload:
    """Real PDF download tests with actual downloads."""

    @pytest.fixture
    def real_config(self, tmp_path):
        """Create real test configuration."""
        config = LiteratureConfig()
        config.download_dir = str(tmp_path / "pdfs")
        config.bibtex_file = str(tmp_path / "references.bib")
        config.library_index_file = str(tmp_path / "library.json")
        config.download_retry_attempts = 2
        return config

    def test_real_pdf_download_arxiv(self, real_config):
        """Test real PDF download from arXiv."""
        searcher = LiteratureSearch(real_config)
        
        # Search for arXiv paper with PDF
        results = searcher.search("active inference", limit=5, sources=["arxiv"])
        
        if not results:
            pytest.skip("No arXiv results found")
        
        # Find result with PDF URL
        result_with_pdf = next((r for r in results if r.pdf_url), None)
        if not result_with_pdf:
            pytest.skip("No arXiv results with PDF URL")
        
        # Download PDF
        pdf_path = searcher.download_paper(result_with_pdf)
        
        if pdf_path and pdf_path.exists():
            assert pdf_path.suffix == ".pdf"
            assert pdf_path.stat().st_size > 0
            # Verify it's actually a PDF
            assert pdf_path.read_bytes()[:4] == b"%PDF"

    def test_real_pdf_download_with_fallbacks(self, real_config):
        """Test real PDF download with fallback strategies."""
        searcher = LiteratureSearch(real_config)
        
        # Create result that might need fallbacks
        result = SearchResult(
            title="Test Paper",
            authors=["Test Author"],
            year=2024,
            abstract="Test abstract",
            url="https://example.com",
            source="test",
            pdf_url=None,
            doi="10.1162/neco_a_00912"  # Real DOI for testing
        )
        
        # Try download (may use fallbacks)
        pdf_path = searcher.download_paper(result)
        
        # If download succeeded, verify
        if pdf_path and pdf_path.exists():
            assert pdf_path.suffix == ".pdf"
            assert pdf_path.stat().st_size > 0


@pytest.mark.integration
class TestRealLibraryManagement:
    """Real library management tests."""

    @pytest.fixture
    def real_config(self, tmp_path):
        """Create real test configuration."""
        config = LiteratureConfig()
        config.download_dir = str(tmp_path / "pdfs")
        config.bibtex_file = str(tmp_path / "references.bib")
        config.library_index_file = str(tmp_path / "library.json")
        return config

    def test_real_add_to_library(self, real_config):
        """Test real library addition."""
        searcher = LiteratureSearch(real_config)
        
        result = SearchResult(
            title="Test Paper for Library",
            authors=["Author One", "Author Two"],
            year=2024,
            abstract="Test abstract for library",
            url="https://example.com/paper",
            doi="10.1234/test.library",
            source="test",
            venue="Test Journal"
        )
        
        citation_key = searcher.add_to_library(result)
        
        assert citation_key is not None
        assert len(citation_key) > 0
        
        # Verify in library index
        library_index = LibraryIndex(real_config)
        entry = library_index.get_entry(citation_key)
        assert entry is not None
        assert entry.title == result.title
        assert entry.doi == result.doi
        
        # Verify in BibTeX
        bib_content = Path(real_config.bibtex_file).read_text()
        assert citation_key in bib_content
        assert result.title in bib_content

    def test_real_library_deduplication(self, real_config):
        """Test real library deduplication."""
        searcher = LiteratureSearch(real_config)
        
        result = SearchResult(
            title="Duplicate Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Test",
            url="https://example.com",
            doi="10.1234/duplicate",
            source="test"
        )
        
        # Add twice
        key1 = searcher.add_to_library(result)
        key2 = searcher.add_to_library(result)
        
        assert key1 == key2
        
        # Verify only one entry
        library_index = LibraryIndex(real_config)
        entries = library_index.list_entries()
        matching = [e for e in entries if e.doi == result.doi]
        assert len(matching) == 1

    def test_real_library_stats(self, real_config, real_library_entries):
        """Test real library statistics."""
        # Add entries to library
        searcher = LiteratureSearch(real_config)
        for entry in real_library_entries:
            result = SearchResult(
                title=entry.title,
                authors=entry.authors,
                year=entry.year,
                abstract=entry.abstract,
                url=entry.url,
                doi=entry.doi,
                source=entry.source,
                venue=entry.venue,
                citation_count=entry.citation_count
            )
            searcher.add_to_library(result)
        
        stats = searcher.get_library_stats()
        
        assert stats["total_entries"] == len(real_library_entries)
        assert "sources" in stats
        assert "years" in stats


@pytest.mark.integration
@pytest.mark.requires_network
class TestRealWorkflowEndToEnd:
    """Real end-to-end workflow tests."""

    @pytest.fixture
    def real_config(self, tmp_path):
        """Create real test configuration."""
        config = LiteratureConfig()
        config.download_dir = str(tmp_path / "pdfs")
        config.bibtex_file = str(tmp_path / "references.bib")
        config.library_index_file = str(tmp_path / "library.json")
        config.arxiv_delay = 1.0
        return config

    def test_real_complete_workflow(self, real_config):
        """Test complete real workflow: search -> add -> download."""
        searcher = LiteratureSearch(real_config)
        
        # 1. Search
        results = searcher.search("active inference", limit=3)
        
        if not results:
            pytest.skip("No search results found")
        
        # 2. Add to library
        added_keys = []
        for result in results[:2]:  # Limit to 2 for speed
            key = searcher.add_to_library(result)
            added_keys.append(key)
            assert key is not None
        
        # 3. Download PDFs (if available)
        # Note: Some papers may be access-restricted (HTTP 403), which is a valid failure mode
        downloaded = 0
        for result in results[:2]:
            if result.pdf_url:
                try:
                    pdf_path = searcher.download_paper(result)
                    if pdf_path and pdf_path.exists():
                        downloaded += 1
                except Exception as e:
                    # HTTP 403 (access denied) and other download failures are acceptable
                    # for real integration tests - some papers are access-restricted
                    if "403" in str(e) or "access" in str(e).lower():
                        # Access-restricted paper - skip silently
                        pass
                    else:
                        # Re-raise unexpected errors
                        raise
        
        # Verify library state
        stats = searcher.get_library_stats()
        assert stats["total_entries"] >= len(added_keys)
        
        # Verify files exist
        bib_file = Path(real_config.bibtex_file)
        assert bib_file.exists()
        
        library_file = Path(real_config.library_index_file)
        assert library_file.exists()
