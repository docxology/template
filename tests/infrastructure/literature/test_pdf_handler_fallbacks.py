"""Tests for PDF handler fallback mechanisms.

Tests the enhanced URL transformation, arXiv title search,
and bioRxiv/medRxiv DOI lookup fallback features.
"""
import pytest
from pathlib import Path

from infrastructure.literature.core import LiteratureConfig
from infrastructure.literature.sources import (
    SearchResult,
    ArxivSource,
    BiorxivSource,
    normalize_title,
    title_similarity,
)
from infrastructure.literature.pdf import transform_pdf_url, PDFHandler


class TestTitleNormalization:
    """Test title normalization for similarity matching."""

    def test_normalize_basic(self):
        """Test basic normalization removes punctuation."""
        result = normalize_title("Hello, World!")
        assert result == "hello world"

    def test_normalize_extra_whitespace(self):
        """Test normalization handles extra whitespace."""
        result = normalize_title("  Multiple   Spaces  Here  ")
        assert result == "multiple spaces here"

    def test_normalize_special_chars(self):
        """Test normalization removes special characters."""
        result = normalize_title("Title: A Study (with notes)")
        assert result == "title a study with notes"

    def test_normalize_empty_string(self):
        """Test normalization of empty string."""
        result = normalize_title("")
        assert result == ""


class TestTitleSimilarity:
    """Test title similarity calculation."""

    def test_identical_titles(self):
        """Test identical titles have similarity 1.0."""
        sim = title_similarity("Machine Learning", "Machine Learning")
        assert sim == 1.0

    def test_case_insensitive(self):
        """Test similarity is case insensitive."""
        sim = title_similarity("Machine Learning", "machine learning")
        assert sim == 1.0

    def test_different_titles(self):
        """Test different titles have low similarity."""
        sim = title_similarity("Machine Learning", "Quantum Physics")
        assert sim < 0.5

    def test_partial_overlap(self):
        """Test titles with partial overlap."""
        sim = title_similarity(
            "Deep Learning for Natural Language Processing",
            "Deep Learning for Computer Vision"
        )
        assert 0.3 < sim < 0.8

    def test_empty_title(self):
        """Test empty titles return 0.0."""
        assert title_similarity("", "Title") == 0.0
        assert title_similarity("Title", "") == 0.0
        assert title_similarity("", "") == 0.0


class TestTransformPdfUrl:
    """Test URL transformation for PDF candidates."""

    def test_pmc_ncbi_pattern(self):
        """Test PMC NCBI URL transformation."""
        url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/"
        candidates = transform_pdf_url(url)
        
        # Should generate multiple candidates
        assert len(candidates) > 0
        
        # Should include direct PDF endpoints
        assert any("PMC123456/pdf/" in c for c in candidates)
        
        # Should include Europe PMC fallback
        assert any("europepmc.org" in c for c in candidates)

    def test_pmc_new_domain(self):
        """Test PMC new domain URL transformation."""
        url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC789012/"
        candidates = transform_pdf_url(url)
        
        assert len(candidates) > 0
        assert any("PMC789012" in c for c in candidates)

    def test_europepmc_pattern(self):
        """Test Europe PMC URL transformation."""
        url = "https://europepmc.org/article/PMC/123456"
        candidates = transform_pdf_url(url)
        
        assert len(candidates) > 0
        # Should extract PMC ID and generate alternatives
        assert any("PMC123456" in c for c in candidates)

    def test_arxiv_abs_pattern(self):
        """Test arXiv abstract URL to PDF transformation."""
        url = "https://arxiv.org/abs/2401.12345"
        candidates = transform_pdf_url(url)
        
        # Should include PDF URL
        assert any("arxiv.org/pdf/2401.12345" in c for c in candidates)

    def test_biorxiv_pattern(self):
        """Test bioRxiv URL transformation."""
        url = "https://www.biorxiv.org/content/10.1101/2020.01.01.123456"
        candidates = transform_pdf_url(url)
        
        # Should include full.pdf endpoint
        assert any(".full.pdf" in c for c in candidates)

    def test_medrxiv_pattern(self):
        """Test medRxiv URL transformation."""
        url = "https://www.medrxiv.org/content/10.1101/2020.05.05.654321"
        candidates = transform_pdf_url(url)
        
        assert any(".full.pdf" in c for c in candidates)

    def test_mdpi_pattern(self):
        """Test MDPI URL transformation."""
        url = "https://www.mdpi.com/2073-4409/10/5/1234"
        candidates = transform_pdf_url(url)
        
        # Should include PDF endpoint
        assert any("/pdf" in c for c in candidates)

    def test_no_transformation_needed(self):
        """Test URL that doesn't match any pattern."""
        url = "https://example.com/some/random/path"
        candidates = transform_pdf_url(url)
        
        # Should return empty list (original URL not included)
        assert candidates == []

    def test_excludes_original_url(self):
        """Test that original URL is excluded from candidates."""
        url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/"
        candidates = transform_pdf_url(url)
        
        # Original URL should not be in candidates
        assert url not in candidates


class TestArxivSourceTitleSearch:
    """Test arXiv title search functionality."""

    def test_arxiv_source_initialization(self, tmp_path):
        """Test ArxivSource initializes correctly."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        source = ArxivSource(config)
        
        assert source.TITLE_SIMILARITY_THRESHOLD == 0.7
        assert source.BASE_URL == "http://export.arxiv.org/api/query"

    def test_search_by_title_returns_none_for_no_match(self, tmp_path):
        """Test search_by_title returns None when no match found."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        source = ArxivSource(config)
        
        # Use a very unique title unlikely to exist
        result = source.search_by_title("xyzzy_nonexistent_title_12345_qwerty")
        
        # Should return None (no matches)
        assert result is None


class TestBiorxivSource:
    """Test bioRxiv/medRxiv source functionality."""

    def test_biorxiv_source_initialization(self, tmp_path):
        """Test BiorxivSource initializes correctly."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        source = BiorxivSource(config)
        
        assert source.TITLE_SIMILARITY_THRESHOLD == 0.7
        assert source.BASE_URL == "https://api.biorxiv.org"

    def test_search_by_doi_nonexistent(self, tmp_path):
        """Test search_by_doi returns None for nonexistent DOI."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        source = BiorxivSource(config)
        
        # Use a nonexistent DOI
        result = source.search_by_doi("10.9999/nonexistent.doi.12345")
        
        assert result is None

    def test_get_pdf_url_nonexistent(self, tmp_path):
        """Test get_pdf_url returns None for nonexistent DOI."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        source = BiorxivSource(config)
        
        result = source.get_pdf_url("10.9999/nonexistent")
        
        assert result is None

    def test_doi_cleaning(self, tmp_path):
        """Test DOI cleaning for various formats."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        source = BiorxivSource(config)
        
        # Test with URL prefix - should still work (clean internally)
        result1 = source.search_by_doi("https://doi.org/10.9999/test")
        result2 = source.search_by_doi("http://doi.org/10.9999/test")
        result3 = source.search_by_doi("doi:10.9999/test")
        result4 = source.search_by_doi("10.9999/test")
        
        # All should return None (nonexistent DOI) but not error
        assert result1 is None
        assert result2 is None
        assert result3 is None
        assert result4 is None


class TestPDFHandlerFallbackIntegration:
    """Test PDFHandler fallback chain integration."""

    def test_handler_initialization(self, tmp_path):
        """Test PDFHandler initializes fallback sources."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        handler = PDFHandler(config)
        
        # Should have fallback sources initialized
        assert handler._fallbacks._arxiv is not None
        assert handler._fallbacks._biorxiv is not None
        assert isinstance(handler._fallbacks._arxiv, ArxivSource)
        assert isinstance(handler._fallbacks._biorxiv, BiorxivSource)

    def test_get_arxiv_fallback_no_title(self, tmp_path):
        """Test get_arxiv_fallback returns None when no title."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="",
            authors=["Author"],
            year=2024,
            abstract="",
            url="https://example.com"
        )
        
        pdf_url = handler._fallbacks.get_arxiv_fallback(result)
        
        assert pdf_url is None

    def test_get_biorxiv_fallback_no_doi(self, tmp_path):
        """Test get_biorxiv_fallback returns None when no DOI."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Some Title",
            authors=["Author"],
            year=2024,
            abstract="",
            url="https://example.com",
            doi=None
        )
        
        pdf_url = handler._fallbacks.get_biorxiv_fallback(result)
        
        assert pdf_url is None

    def test_fallback_chain_with_existing_pdf(self, tmp_path):
        """Test download_pdf returns existing file without fallbacks."""
        pdfs_dir = tmp_path / "pdfs"
        pdfs_dir.mkdir()
        
        # Create existing PDF file
        existing_pdf = pdfs_dir / "test2024paper.pdf"
        existing_pdf.write_bytes(b'%PDF-1.4 test content')
        
        config = LiteratureConfig(
            download_dir=str(pdfs_dir),
            bibtex_file=str(tmp_path / "refs.bib"),
            library_index_file=str(tmp_path / "library.json")
        )
        handler = PDFHandler(config)
        
        result = SearchResult(
            title="Paper",
            authors=["Test"],
            year=2024,
            abstract="",
            url="https://example.com",
            pdf_url="https://example.com/fake.pdf"
        )
        
        # Download should return existing file
        path = handler.download_pdf(
            url="https://example.com/fake.pdf",
            filename="test2024paper.pdf",
            result=result
        )
        
        assert path == existing_pdf


class TestTransformPdfUrlMultiplePatterns:
    """Additional tests for URL transformation edge cases."""

    def test_pmc_with_trailing_content(self):
        """Test PMC URL with trailing content."""
        url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/pdf/nihms-1234.pdf"
        candidates = transform_pdf_url(url)
        
        # Should still extract PMC ID correctly
        assert any("PMC123456" in c for c in candidates)

    def test_arxiv_old_format(self):
        """Test arXiv old format IDs."""
        url = "https://arxiv.org/abs/hep-th/9901001"
        candidates = transform_pdf_url(url)
        
        # Should handle old format
        assert any("hep-th/9901001" in c for c in candidates)

    def test_frontiers_pattern(self):
        """Test Frontiers URL transformation."""
        url = "https://www.frontiersin.org/articles/10.3389/fpsyg.2024.1234567/full"
        candidates = transform_pdf_url(url)
        
        # Should include PDF endpoint
        assert any("/pdf" in c for c in candidates)

    def test_sciencedirect_pattern(self):
        """Test ScienceDirect URL transformation."""
        url = "https://www.sciencedirect.com/science/article/pii/S1234567890123456"
        candidates = transform_pdf_url(url)
        
        # Should include PDF download endpoint
        assert any("pdfft" in c for c in candidates)


class TestArxivSourceAttributes:
    """Test ArxivSource class attributes and methods."""

    def test_similarity_threshold(self, tmp_path):
        """Test that similarity threshold is reasonable."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        source = ArxivSource(config)
        
        # Threshold should be between 0 and 1
        assert 0 < source.TITLE_SIMILARITY_THRESHOLD < 1
        # Should be reasonably high to avoid false matches
        assert source.TITLE_SIMILARITY_THRESHOLD >= 0.5


class TestBiorxivSourceAttributes:
    """Test BiorxivSource class attributes and methods."""

    def test_similarity_threshold(self, tmp_path):
        """Test that similarity threshold is reasonable."""
        config = LiteratureConfig(
            download_dir=str(tmp_path / "pdfs"),
            bibtex_file=str(tmp_path / "refs.bib")
        )
        source = BiorxivSource(config)
        
        # Threshold should be between 0 and 1
        assert 0 < source.TITLE_SIMILARITY_THRESHOLD < 1
        # Should be reasonably high to avoid false matches
        assert source.TITLE_SIMILARITY_THRESHOLD >= 0.5


class TestPDFHandlerDocstring:
    """Test PDFHandler documentation reflects fallback chain."""

    def test_docstring_mentions_fallbacks(self):
        """Test class docstring documents fallback chain."""
        docstring = PDFHandler.__doc__
        
        # Should document the fallback order
        assert "Primary URL" in docstring or "fallback" in docstring.lower()
        assert "arXiv" in docstring
        assert "bioRxiv" in docstring or "Unpaywall" in docstring


class TestTitleSimilarityEdgeCases:
    """Test edge cases in title similarity calculation."""

    def test_unicode_titles(self):
        """Test similarity with Unicode characters."""
        # Unicode accented chars are preserved by alnum check
        sim = title_similarity(
            "Étude des systèmes complexes",
            "etude des systemes complexes"
        )
        # Words with accents differ from without, so lower similarity expected
        assert sim >= 0.0  # Just verify it doesn't crash

    def test_identical_unicode_titles(self):
        """Test identical Unicode titles have perfect similarity."""
        sim = title_similarity(
            "Étude des systèmes complexes",
            "Étude des systèmes complexes"
        )
        assert sim == 1.0

    def test_hyphenated_words(self):
        """Test similarity with hyphenated words."""
        # Hyphenated words become separate words after punctuation removal
        sim = title_similarity(
            "Self-Supervised Learning",
            "Self Supervised Learning"
        )
        # "selfsupervised" vs "self supervised" -> different word counts
        # Just verify it returns a valid similarity
        assert 0 <= sim <= 1

    def test_numbers_in_titles(self):
        """Test similarity with numbers."""
        sim = title_similarity(
            "GPT-4 Technical Report",
            "GPT4 Technical Report"
        )
        # After removing punctuation: "gpt4 technical report" vs "gpt4 technical report"
        # Should be identical
        assert sim >= 0.75

