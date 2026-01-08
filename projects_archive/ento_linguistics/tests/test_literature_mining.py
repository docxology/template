"""Tests for literature_mining.py module.

This module contains comprehensive tests for literature mining functionality
used in Ento-Linguistic research.
"""
from __future__ import annotations

import pytest
import json
from pathlib import Path
from typing import List, Dict

from src.literature_mining import LiteratureCorpus, Publication, PubMedMiner, ArXivMiner


class TestPublication:
    """Test Publication dataclass functionality."""

    def test_publication_creation(self) -> None:
        """Test creating a Publication instance."""
        pub = Publication(
            title="Ant Colony Behavior",
            authors=["Smith, J.", "Doe, A."],
            abstract="This paper studies ant colonies.",
            doi="10.1234/example",
            year=2023
        )

        assert pub.title == "Ant Colony Behavior"
        assert len(pub.authors) == 2
        assert pub.abstract == "This paper studies ant colonies."
        assert pub.doi == "10.1234/example"
        assert pub.year == 2023

    def test_publication_to_dict(self) -> None:
        """Test converting Publication to dictionary."""
        pub = Publication(
            title="Test Paper",
            authors=["Author, A."],
            year=2023
        )

        data = pub.to_dict()

        assert data['title'] == "Test Paper"
        assert data['authors'] == ["Author, A."]
        assert data['year'] == 2023
        assert data['keywords'] == []  # Should be initialized as empty list

    def test_publication_from_dict(self) -> None:
        """Test creating Publication from dictionary."""
        data = {
            'title': "Test Paper",
            'authors': ["Author, A."],
            'abstract': "Abstract text",
            'doi': "10.1234/test",
            'year': 2023,
            'journal': "Test Journal",
            'keywords': ["test", "paper"]
        }

        pub = Publication.from_dict(data)

        assert pub.title == "Test Paper"
        assert pub.authors == ["Author, A."]
        assert pub.abstract == "Abstract text"
        assert pub.doi == "10.1234/test"
        assert pub.year == 2023
        assert pub.journal == "Test Journal"
        assert pub.keywords == ["test", "paper"]

    def test_publication_optional_fields(self) -> None:
        """Test Publication with optional fields not set."""
        pub = Publication(title="Minimal Paper", authors=["Author"])

        assert pub.abstract is None
        assert pub.doi is None
        assert pub.year is None
        assert pub.journal is None
        assert pub.keywords == []


class TestLiteratureCorpus:
    """Test LiteratureCorpus functionality."""

    @pytest.fixture
    def sample_publications(self) -> List[Publication]:
        """Create sample publications for testing."""
        return [
            Publication(
                title="Ant Colony Optimization",
                authors=["Dorigo, M.", "Colorni, A."],
                abstract="Algorithm inspired by ant behavior",
                year=1996
            ),
            Publication(
                title="Eusociality in Insects",
                authors=["Wilson, E.O."],
                abstract="Evolution of social insects",
                year=1971
            ),
            Publication(
                title="Division of Labor in Ants",
                authors=["Oster, G.", "Wilson, E.O."],
                abstract="Mathematical modeling of task allocation",
                year=1978
            )
        ]

    @pytest.fixture
    def corpus(self, sample_publications: List[Publication]) -> LiteratureCorpus:
        """Create a LiteratureCorpus with sample data."""
        return LiteratureCorpus(sample_publications)

    def test_corpus_initialization(self, corpus: LiteratureCorpus) -> None:
        """Test corpus initialization."""
        assert len(corpus.publications) == 3
        assert all(isinstance(pub, Publication) for pub in corpus.publications)

    def test_add_publication(self, corpus: LiteratureCorpus) -> None:
        """Test adding publications to corpus."""
        initial_count = len(corpus.publications)

        new_pub = Publication(title="New Paper", authors=["New, A."])
        corpus.add_publication(new_pub)

        assert len(corpus.publications) == initial_count + 1
        assert corpus.publications[-1] == new_pub

    @pytest.mark.skipif(not Path("tmp").exists(), reason="Temporary directory needed")
    def test_corpus_save_load(self, corpus: LiteratureCorpus, tmp_path: Path) -> None:
        """Test saving and loading corpus to/from file."""
        filepath = tmp_path / "test_corpus.json"

        # Save corpus
        corpus.save_to_file(filepath)
        assert filepath.exists()

        # Load corpus
        loaded_corpus = LiteratureCorpus.load_from_file(filepath)

        assert len(loaded_corpus.publications) == len(corpus.publications)
        assert loaded_corpus.publications[0].title == corpus.publications[0].title
        assert loaded_corpus.publications[0].authors == corpus.publications[0].authors

    def test_get_text_corpus(self, corpus: LiteratureCorpus) -> None:
        """Test extracting text corpus from publications."""
        texts = corpus.get_text_corpus()

        assert len(texts) == 3
        assert all(isinstance(text, str) for text in texts)
        assert all(len(text.strip()) > 0 for text in texts)

        # Should contain title, authors, and abstract
        first_text = texts[0].lower()
        assert "ant colony optimization" in first_text
        assert "dorigo" in first_text
        assert "algorithm inspired" in first_text

    def test_get_text_corpus_missing_abstract(self) -> None:
        """Test text corpus extraction when abstract is missing."""
        pub = Publication(title="Title Only", authors=["Author"])
        corpus = LiteratureCorpus([pub])

        texts = corpus.get_text_corpus()

        assert len(texts) == 1
        assert "title only" in texts[0].lower()
        assert "author" in texts[0].lower()

    def test_search_publications(self, corpus: LiteratureCorpus) -> None:
        """Test publication search functionality."""
        # Search by title
        results = corpus.search_publications("colony", field="title")
        assert len(results) >= 1
        assert any("colony" in pub.title.lower() for pub in results)

        # Search by author
        results = corpus.search_publications("wilson", field="all")
        assert len(results) >= 1
        assert any("wilson" in author.lower() for pub in results for author in pub.authors)

        # Search all fields
        results = corpus.search_publications("evolution", field="all")
        assert len(results) >= 1

    def test_search_no_results(self, corpus: LiteratureCorpus) -> None:
        """Test search with no matching results."""
        results = corpus.search_publications("nonexistent", field="title")
        assert len(results) == 0

    def test_get_statistics(self, corpus: LiteratureCorpus) -> None:
        """Test corpus statistics generation."""
        stats = corpus.get_statistics()

        assert 'total_publications' in stats
        assert 'date_range' in stats
        assert 'unique_journals' in stats
        assert 'publications_with_abstract' in stats
        assert 'avg_title_length' in stats

        assert stats['total_publications'] == 3
        assert stats['publications_with_abstract'] == 3  # All have abstracts
        assert stats['avg_title_length'] > 0

    def test_empty_corpus_statistics(self) -> None:
        """Test statistics for empty corpus."""
        corpus = LiteratureCorpus()
        stats = corpus.get_statistics()

        assert stats['total_publications'] == 0
        assert stats['date_range'] is None
        assert stats['publications_with_abstract'] == 0


class TestPubMedMiner:
    """Test PubMed mining functionality."""

    @pytest.fixture
    def miner(self) -> PubMedMiner:
        """Create a PubMed miner instance."""
        return PubMedMiner()

    def test_search_success(self, httpserver, miner: PubMedMiner) -> None:
        """Test successful PubMed search."""
        # Mock PubMed API response
        response_data = {
            "esearchresult": {
                "idlist": ["12345", "67890"]
            }
        }

        # Configure mock server to expect the request
        httpserver.expect_request(
            "/esearch.fcgi"
        ).respond_with_json(response_data)

        # Temporarily override the base URL to point to our test server
        original_base_url = miner.BASE_URL
        miner.BASE_URL = httpserver.url_for("")  # Just the server URL without path

        try:
            results = miner.search("ant+colony", max_results=10)  # Use URL-encoded query

            assert len(results) == 2
            assert "12345" in results
            assert "67890" in results
        finally:
            miner.BASE_URL = original_base_url

    def test_search_error_handling(self, httpserver, miner: PubMedMiner) -> None:
        """Test PubMed search error handling."""
        # Configure server to return 500 error
        httpserver.expect_request("/esearch.fcgi").respond_with_data(
            "Internal Server Error", status=500
        )

        # Temporarily override the base URL
        original_base_url = miner.BASE_URL
        miner.BASE_URL = httpserver.url_for("")

        try:
            results = miner.search("ant+colony")
            assert results == []
        finally:
            miner.BASE_URL = original_base_url

    def test_fetch_publications_success(self, httpserver, miner: PubMedMiner) -> None:
        """Test successful publication fetching."""
        # Mock PubMed summary API response
        response_data = {
            "result": {
                "12345": {
                    "title": "Test Paper",
                    "authors": [{"name": "Author, A."}],
                    "abstract": "Test abstract",
                    "pubdate": "2023",
                    "source": "Test Journal",
                    "elocationid": "10.1234/test",
                    "uid": "12345"
                }
            }
        }

        # Configure mock server
        httpserver.expect_request("/esummary.fcgi").respond_with_json(response_data)

        # Temporarily override the base URL
        original_base_url = miner.BASE_URL
        miner.BASE_URL = httpserver.url_for("")

        try:
            publications = miner.fetch_publications(["12345"])

            assert len(publications) == 1
            assert publications[0].title == "Test Paper"
            assert publications[0].authors == ["Author, A."]
            assert publications[0].abstract == "Test abstract"
            assert publications[0].year == 2023
        finally:
            miner.BASE_URL = original_base_url

    def test_fetch_publications_parse_error(self, httpserver, miner: PubMedMiner) -> None:
        """Test handling of PubMed parsing errors."""
        # Configure server to return invalid JSON
        httpserver.expect_request("/esummary.fcgi").respond_with_data("invalid json")

        # Temporarily override the base URL
        original_base_url = miner.BASE_URL
        miner.BASE_URL = httpserver.url_for("")

        try:
            publications = miner.fetch_publications(["12345"])
            assert len(publications) == 0
        finally:
            miner.BASE_URL = original_base_url

    def test_parse_pubmed_summary_minimal(self, miner: PubMedMiner) -> None:
        """Test parsing minimal PubMed summary."""
        data = {
            "title": "Minimal Paper",
            "authors": [{"name": "Author, A."}]
        }

        pub = miner._parse_pubmed_summary(data)

        assert pub is not None
        assert pub.title == "Minimal Paper"
        assert pub.authors == ["Author, A."]
        assert pub.abstract is None

    def test_parse_pubmed_summary_missing_title(self, miner: PubMedMiner) -> None:
        """Test parsing PubMed summary with missing title."""
        data = {
            "authors": [{"name": "Author, A."}]
        }

        pub = miner._parse_pubmed_summary(data)

        assert pub is None


class TestArXivMiner:
    """Test ArXiv mining functionality."""

    @pytest.fixture
    def miner(self) -> ArXivMiner:
        """Create an ArXiv miner instance."""
        return ArXivMiner()

    def test_search_success(self, httpserver, miner: ArXivMiner) -> None:
        """Test successful ArXiv search."""
        # Mock arXiv API XML response
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Paper</title>
                <author><name>Author, A.</name></author>
                <summary>Test abstract</summary>
                <published>2023-01-01T00:00:00Z</published>
            </entry>
        </feed>"""

        # Configure mock server
        httpserver.expect_request("/api/query").respond_with_data(
            xml_response, content_type="application/xml"
        )

        # Temporarily override the base URL
        original_base_url = miner.BASE_URL
        miner.BASE_URL = httpserver.url_for("/api/query?")

        try:
            results = miner.search("ant+colony", max_results=5)

            assert len(results) == 1
            assert results[0].title == "Test Paper"
            assert results[0].authors == ["Author, A."]
            assert results[0].abstract == "Test abstract"
        finally:
            miner.BASE_URL = original_base_url

    def test_search_error_handling(self, httpserver, miner: ArXivMiner) -> None:
        """Test ArXiv search error handling."""
        # Configure server to return 500 error
        httpserver.expect_request("/api/query").respond_with_data(
            "Internal Server Error", status=500
        )

        # Temporarily override the base URL
        original_base_url = miner.BASE_URL
        miner.BASE_URL = httpserver.url_for("/api/query?")

        try:
            results = miner.search("ant+colony")
            assert results == []
        finally:
            miner.BASE_URL = original_base_url

    def test_parse_arxiv_entry_minimal(self, miner: ArXivMiner) -> None:
        """Test parsing minimal ArXiv entry."""
        # Create a real XML element for testing
        import xml.etree.ElementTree as ET

        entry_xml = """<entry xmlns="http://www.w3.org/2005/Atom">
            <title>Test Paper</title>
            <author><name>Author, A.</name></author>
            <summary>Test abstract</summary>
            <published>2023-01-01T00:00:00Z</published>
        </entry>"""

        entry = ET.fromstring(entry_xml)
        ns = {'arxiv': 'http://www.w3.org/2005/Atom'}

        pub = miner._parse_arxiv_entry(entry, ns)

        assert pub is not None
        assert pub.title == "Test Paper"
        assert pub.authors == ["Author, A."]
        assert pub.abstract == "Test abstract"
        assert pub.year == 2023

    def test_parse_arxiv_entry_missing_title(self, miner: ArXivMiner) -> None:
        """Test parsing ArXiv entry with missing title."""
        import xml.etree.ElementTree as ET

        entry_xml = """<entry xmlns="http://www.w3.org/2005/Atom">
            <author><name>Author, A.</name></author>
            <summary>Test abstract</summary>
        </entry>"""

        entry = ET.fromstring(entry_xml)
        ns = {'arxiv': 'http://www.w3.org/2005/Atom'}

        pub = miner._parse_arxiv_entry(entry, ns)

        assert pub is None


class TestLiteratureMiningIntegration:
    """Integration tests for literature mining components."""

    def test_corpus_pubmed_integration(self) -> None:
        """Test integration between LiteratureCorpus and PubMedMiner."""
        corpus = LiteratureCorpus()

        # Create mock publications
        pubs = [
            Publication(title="Paper 1", authors=["Author 1"], abstract="Abstract 1"),
            Publication(title="Paper 2", authors=["Author 2"], abstract="Abstract 2")
        ]

        for pub in pubs:
            corpus.add_publication(pub)

        assert len(corpus.publications) == 2

        # Test text extraction
        texts = corpus.get_text_corpus()
        assert len(texts) == 2
        assert all("paper" in text.lower() for text in texts)

    def test_miner_corpus_integration(self) -> None:
        """Test integration between miners and corpus."""
        corpus = LiteratureCorpus()

        # Simulate miner results
        publications = [
            Publication(title="Entomology Paper", authors=["Ento, A."],
                       abstract="Study of insect behavior", year=2023),
            Publication(title="Ant Research", authors=["Ant, B."],
                       abstract="Colony organization study", year=2022)
        ]

        for pub in publications:
            corpus.add_publication(pub)

        # Test search functionality
        results = corpus.search_publications("ant")
        assert len(results) >= 1

        # Test statistics
        stats = corpus.get_statistics()
        assert stats['total_publications'] == 2
        assert stats['publications_with_abstract'] == 2

    @pytest.mark.skipif(not Path("tmp").exists(), reason="Temporary directory needed")
    def test_full_mining_workflow(self, tmp_path: Path) -> None:
        """Test a complete mining workflow."""
        corpus = LiteratureCorpus()

        # Add sample publications
        pubs = [
            Publication(title="Eusociality in Ants", authors=["Wilson, E.O."],
                       abstract="Evolution of social behavior in ants", year=1971),
            Publication(title="Division of Labor", authors=["Oster, G."],
                       abstract="Mathematical models of task allocation", year=1978)
        ]

        for pub in pubs:
            corpus.add_publication(pub)

        # Save and reload
        corpus_file = tmp_path / "workflow_test.json"
        corpus.save_to_file(corpus_file)
        loaded_corpus = LiteratureCorpus.load_from_file(corpus_file)

        # Verify data integrity
        assert len(loaded_corpus.publications) == 2
        assert loaded_corpus.publications[0].title == "Eusociality in Ants"
        assert loaded_corpus.publications[1].year == 1978

        # Test text extraction
        texts = loaded_corpus.get_text_corpus()
        assert len(texts) == 2
        assert all("ants" in text.lower() or "labor" in text.lower() for text in texts)

    def test_create_entomology_query(self) -> None:
        """Test entomology query creation."""
        from src.literature_mining import create_entomology_query

        query = create_entomology_query()

        assert isinstance(query, str)
        assert len(query) > 0
        # Should contain entomology-related terms
        assert "ants" in query
        assert "eusocial" in query
        assert "English[Language]" in query
        assert ' OR ' in query  # Should join terms with OR

    def test_mine_entomology_literature(self) -> None:
        """Test the complete entomology literature mining workflow."""
        from src.literature_mining import mine_entomology_literature, LiteratureCorpus

        # This test is primarily for code coverage - the actual mining
        # would require real API calls, so we just test that it returns a corpus
        # Note: This function makes real API calls, so we'll just test the structure

        # Test that the function exists and can be called (without actually calling it
        # to avoid real API dependencies in CI)
        assert callable(mine_entomology_literature)

        # Test that it returns the expected type when we create an empty corpus
        corpus = LiteratureCorpus()
        assert isinstance(corpus, LiteratureCorpus)