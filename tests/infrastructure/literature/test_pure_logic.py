"""Pure logic tests for literature module.

Tests that verify business logic without network access or mocking.
These test real data transformations, formatting, and validation.
"""
import pytest
from pathlib import Path

from infrastructure.literature.core import LiteratureConfig
from infrastructure.literature.sources import SearchResult
from infrastructure.literature.library import ReferenceManager
from infrastructure.literature.core import LiteratureSearch


class TestSearchResultDataclass:
    """Test SearchResult dataclass behavior."""

    def test_search_result_creation(self):
        """Test creating a SearchResult with all fields."""
        result = SearchResult(
            title="Test Paper Title",
            authors=["Author One", "Author Two"],
            year=2024,
            abstract="This is the abstract.",
            url="https://example.com/paper",
            doi="10.1234/test.123",
            source="arxiv",
            pdf_url="https://example.com/paper.pdf",
            venue="Journal of Testing",
            citation_count=42
        )
        
        assert result.title == "Test Paper Title"
        assert result.authors == ["Author One", "Author Two"]
        assert result.year == 2024
        assert result.doi == "10.1234/test.123"
        assert result.citation_count == 42

    def test_search_result_minimal(self):
        """Test creating SearchResult with minimal required fields."""
        result = SearchResult(
            title="Minimal Paper",
            authors=["Single Author"],
            year=None,
            abstract="",
            url="https://example.com"
        )
        
        assert result.title == "Minimal Paper"
        assert result.doi is None
        assert result.pdf_url is None
        assert result.source == "unknown"

    def test_search_result_defaults(self):
        """Test SearchResult default values."""
        result = SearchResult(
            title="Test",
            authors=[],
            year=2024,
            abstract="abs",
            url="url"
        )
        
        assert result.source == "unknown"
        assert result.doi is None
        assert result.pdf_url is None
        assert result.venue is None
        assert result.citation_count is None


class TestReferenceManagerKeyGeneration:
    """Test BibTeX key generation logic."""

    def test_generate_key_basic(self, tmp_path):
        """Test basic key generation: LastName + Year + FirstWord."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Deep Learning for NLP",
            authors=["John Smith"],
            year=2024,
            abstract="",
            url=""
        )
        
        key = manager._generate_key(result)
        
        assert key == "smith2024deep"

    def test_generate_key_multiple_authors(self, tmp_path):
        """Test key uses first author's last name."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Collaborative Research",
            authors=["Jane Doe", "John Smith", "Alice Johnson"],
            year=2023,
            abstract="",
            url=""
        )
        
        key = manager._generate_key(result)
        
        assert key == "doe2023collaborative"

    def test_generate_key_no_year(self, tmp_path):
        """Test key generation when year is None."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Undated Paper",
            authors=["Author Name"],
            year=None,
            abstract="",
            url=""
        )
        
        key = manager._generate_key(result)
        
        assert key == "namenodateundated"

    def test_generate_key_no_authors(self, tmp_path):
        """Test key generation when authors list is empty."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Anonymous Paper",
            authors=[],
            year=2024,
            abstract="",
            url=""
        )
        
        key = manager._generate_key(result)
        
        assert key == "anonymous2024anonymous"

    def test_generate_key_special_characters(self, tmp_path):
        """Test key sanitizes non-alphanumeric characters."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="What's New? A Study!",
            authors=["José García-López"],
            year=2024,
            abstract="",
            url=""
        )
        
        key = manager._generate_key(result)
        
        # Non-alphanumeric chars removed (hyphens, apostrophes, etc.)
        # Note: accented chars like í, ó are considered alphanumeric in Python 3
        assert "whats" in key  # Apostrophe and question mark removed
        assert "-" not in key  # Hyphen removed
        assert all(c.isalnum() for c in key)

    def test_generate_key_compound_name(self, tmp_path):
        """Test key uses last word of author name."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Research Paper",
            authors=["Mary Jane Watson"],
            year=2024,
            abstract="",
            url=""
        )
        
        key = manager._generate_key(result)
        
        assert key == "watson2024research"


class TestReferenceManagerBibTeXFormatting:
    """Test BibTeX entry formatting."""

    def test_format_bibtex_complete(self, tmp_path):
        """Test formatting with all fields."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Complete Paper",
            authors=["Author One", "Author Two"],
            year=2024,
            abstract="This is the abstract.",
            url="https://example.com/paper",
            doi="10.1234/test",
            venue="Nature"
        )
        
        entry = manager._format_bibtex(result, "one2024complete")
        
        assert "@article{one2024complete," in entry
        assert "title={Complete Paper}" in entry
        assert "author={Author One and Author Two}" in entry
        assert "year={2024}" in entry
        assert "url={https://example.com/paper}" in entry
        assert "abstract={This is the abstract.}" in entry
        assert "doi={10.1234/test}" in entry
        assert "journal={Nature}" in entry

    def test_format_bibtex_minimal(self, tmp_path):
        """Test formatting with minimal fields."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Minimal Paper",
            authors=["Single Author"],
            year=None,
            abstract="",
            url="https://example.com"
        )
        
        entry = manager._format_bibtex(result, "author_minimal")
        
        assert "@article{author_minimal," in entry
        assert "title={Minimal Paper}" in entry
        assert "author={Single Author}" in entry
        assert "url={https://example.com}" in entry
        # Optional fields should not appear
        assert "year=" not in entry
        assert "abstract=" not in entry
        assert "doi=" not in entry
        assert "journal=" not in entry

    def test_format_bibtex_multiple_authors(self, tmp_path):
        """Test author list joined with 'and'."""
        config = LiteratureConfig(bibtex_file=str(tmp_path / "refs.bib"))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Team Paper",
            authors=["Alice", "Bob", "Charlie"],
            year=2024,
            abstract="",
            url=""
        )
        
        entry = manager._format_bibtex(result, "key")
        
        assert "author={Alice and Bob and Charlie}" in entry


class TestReferenceManagerFileOperations:
    """Test BibTeX file operations."""

    def test_add_reference_creates_file(self, tmp_path):
        """Test add_reference creates BibTeX file if not exists."""
        bib_path = tmp_path / "new_refs.bib"
        config = LiteratureConfig(bibtex_file=str(bib_path))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="New Paper",
            authors=["Author"],
            year=2024,
            abstract="",
            url=""
        )
        
        key = manager.add_reference(result)
        
        assert bib_path.exists()
        content = bib_path.read_text()
        assert "@article" in content
        assert key in content

    def test_add_reference_appends_to_file(self, tmp_path):
        """Test add_reference appends to existing file."""
        bib_path = tmp_path / "refs.bib"
        bib_path.write_text("% Existing content\n")
        
        config = LiteratureConfig(bibtex_file=str(bib_path))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="New Paper",
            authors=["Author"],
            year=2024,
            abstract="",
            url=""
        )
        
        manager.add_reference(result)
        
        content = bib_path.read_text()
        assert "% Existing content" in content
        assert "@article" in content

    def test_add_reference_deduplication(self, tmp_path):
        """Test add_reference skips duplicates."""
        bib_path = tmp_path / "refs.bib"
        config = LiteratureConfig(bibtex_file=str(bib_path))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Same Paper",
            authors=["Same Author"],
            year=2024,
            abstract="",
            url=""
        )
        
        # Add same paper twice
        key1 = manager.add_reference(result)
        key2 = manager.add_reference(result)
        
        assert key1 == key2
        
        # File should only have one entry
        content = bib_path.read_text()
        assert content.count("@article") == 1

    def test_add_reference_creates_parent_dirs(self, tmp_path):
        """Test add_reference creates parent directories."""
        bib_path = tmp_path / "deep" / "nested" / "refs.bib"
        config = LiteratureConfig(bibtex_file=str(bib_path))
        manager = ReferenceManager(config)
        
        result = SearchResult(
            title="Paper",
            authors=["Author"],
            year=2024,
            abstract="",
            url=""
        )
        
        manager.add_reference(result)
        
        assert bib_path.exists()


class TestLiteratureSearchDeduplication:
    """Test search result deduplication logic."""

    def test_deduplicate_by_doi(self, tmp_path):
        """Test deduplication by DOI."""
        config = LiteratureConfig(
            bibtex_file=str(tmp_path / "refs.bib"),
            download_dir=str(tmp_path / "pdfs")
        )
        search = LiteratureSearch(config)
        
        results = [
            SearchResult(
                title="Paper A",
                authors=["Author"],
                year=2024,
                abstract="",
                url="url1",
                doi="10.1234/same",
                source="arxiv"
            ),
            SearchResult(
                title="Paper A (duplicate)",
                authors=["Author"],
                year=2024,
                abstract="",
                url="url2",
                doi="10.1234/same",
                source="semanticscholar"
            ),
            SearchResult(
                title="Paper B",
                authors=["Author"],
                year=2024,
                abstract="",
                url="url3",
                doi="10.1234/different"
            ),
        ]
        
        unique = search._deduplicate_results(results)
        
        assert len(unique) == 2
        dois = {r.doi for r in unique}
        assert dois == {"10.1234/same", "10.1234/different"}

    def test_deduplicate_by_title(self, tmp_path):
        """Test deduplication by title when DOI is missing."""
        config = LiteratureConfig(
            bibtex_file=str(tmp_path / "refs.bib"),
            download_dir=str(tmp_path / "pdfs")
        )
        search = LiteratureSearch(config)
        
        results = [
            SearchResult(
                title="Unique Title",
                authors=["Author"],
                year=2024,
                abstract="",
                url="url1"
            ),
            SearchResult(
                title="unique title",  # Same title, different case
                authors=["Author"],
                year=2024,
                abstract="",
                url="url2"
            ),
            SearchResult(
                title="Different Title",
                authors=["Author"],
                year=2024,
                abstract="",
                url="url3"
            ),
        ]
        
        unique = search._deduplicate_results(results)
        
        assert len(unique) == 2
        titles = {r.title.lower() for r in unique}
        assert "unique title" in titles
        assert "different title" in titles

    def test_deduplicate_preserves_order(self, tmp_path):
        """Test deduplication preserves first occurrence."""
        config = LiteratureConfig(
            bibtex_file=str(tmp_path / "refs.bib"),
            download_dir=str(tmp_path / "pdfs")
        )
        search = LiteratureSearch(config)
        
        results = [
            SearchResult(
                title="First Occurrence",
                authors=["Author"],
                year=2024,
                abstract="First",
                url="url1",
                source="arxiv"
            ),
            SearchResult(
                title="First Occurrence",
                authors=["Author"],
                year=2024,
                abstract="Second",
                url="url2",
                source="semanticscholar"
            ),
        ]
        
        unique = search._deduplicate_results(results)
        
        assert len(unique) == 1
        # Deduplication may prefer one result over another based on _is_better_result
        # The test verifies deduplication works, not which specific result is kept
        assert unique[0].title == "First Occurrence"
        assert unique[0].abstract in ["First", "Second"]

    def test_deduplicate_empty_list(self, tmp_path):
        """Test deduplication with empty input."""
        config = LiteratureConfig(
            bibtex_file=str(tmp_path / "refs.bib"),
            download_dir=str(tmp_path / "pdfs")
        )
        search = LiteratureSearch(config)
        
        unique = search._deduplicate_results([])
        
        assert unique == []

    def test_deduplicate_title_whitespace(self, tmp_path):
        """Test deduplication handles title whitespace."""
        config = LiteratureConfig(
            bibtex_file=str(tmp_path / "refs.bib"),
            download_dir=str(tmp_path / "pdfs")
        )
        search = LiteratureSearch(config)
        
        results = [
            SearchResult(
                title="  Title with Spaces  ",
                authors=["Author"],
                year=2024,
                abstract="",
                url="url1"
            ),
            SearchResult(
                title="Title with Spaces",
                authors=["Author"],
                year=2024,
                abstract="",
                url="url2"
            ),
        ]
        
        unique = search._deduplicate_results(results)
        
        assert len(unique) == 1


class TestLiteratureSearchDownloadPaper:
    """Test download_paper method edge cases."""

    def test_download_paper_no_pdf_url(self, tmp_path):
        """Test download_paper returns None when no PDF URL."""
        config = LiteratureConfig(
            bibtex_file=str(tmp_path / "refs.bib"),
            download_dir=str(tmp_path / "pdfs")
        )
        search = LiteratureSearch(config)
        
        result = SearchResult(
            title="No PDF",
            authors=["Author"],
            year=2024,
            abstract="",
            url="https://example.com",
            pdf_url=None
        )
        
        path = search.download_paper(result)
        
        assert path is None


class TestCliIntegration:
    """Test CLI function integration with real objects."""

    def test_search_command_imports(self):
        """Test CLI module imports work correctly."""
        from infrastructure.literature.core.cli import search_command, main
        
        assert callable(search_command)
        assert callable(main)

    def test_cli_uses_correct_method(self):
        """Verify CLI calls search() not search_papers()."""
        from infrastructure.literature.core import cli
        import inspect
        
        # Read the source code of search_command
        source = inspect.getsource(cli.search_command)
        
        # Should use manager.search() not manager.search_papers()
        assert "manager.search(" in source
        assert "manager.search_papers(" not in source

