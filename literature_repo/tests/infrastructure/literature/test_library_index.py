"""Tests for infrastructure/data/library_index.py"""
import pytest
import json
from pathlib import Path
from datetime import datetime

from infrastructure.literature.library import LibraryIndex, LibraryEntry
from infrastructure.literature.core import LiteratureConfig


class TestLibraryEntry:
    """Test suite for LibraryEntry dataclass."""

    def test_entry_creation_basic(self):
        """Test basic entry creation."""
        entry = LibraryEntry(
            citation_key="smith2024machine",
            title="Machine Learning Paper",
            authors=["John Smith", "Jane Doe"],
            year=2024
        )
        assert entry.citation_key == "smith2024machine"
        assert entry.title == "Machine Learning Paper"
        assert entry.authors == ["John Smith", "Jane Doe"]
        assert entry.year == 2024

    def test_entry_defaults(self):
        """Test entry default values."""
        entry = LibraryEntry(
            citation_key="test",
            title="Test",
            authors=[]
        )
        assert entry.year is None
        assert entry.doi is None
        assert entry.source == "unknown"
        assert entry.url == ""
        assert entry.pdf_path is None
        assert entry.added_date == ""
        assert entry.abstract == ""
        assert entry.venue is None
        assert entry.citation_count is None
        assert entry.metadata == {}

    def test_entry_to_dict(self):
        """Test conversion to dictionary."""
        entry = LibraryEntry(
            citation_key="smith2024machine",
            title="Machine Learning Paper",
            authors=["John Smith"],
            year=2024,
            doi="10.1234/test.123"
        )
        result = entry.to_dict()
        assert result["citation_key"] == "smith2024machine"
        assert result["title"] == "Machine Learning Paper"
        assert result["authors"] == ["John Smith"]
        assert result["year"] == 2024
        assert result["doi"] == "10.1234/test.123"

    def test_entry_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "citation_key": "smith2024machine",
            "title": "Machine Learning Paper",
            "authors": ["John Smith"],
            "year": 2024,
            "doi": "10.1234/test.123",
            "source": "arxiv",
            "url": "http://example.com",
            "pdf_path": None,
            "added_date": "2024-01-01T00:00:00",
            "abstract": "Test abstract",
            "venue": "Journal",
            "citation_count": 10,
            "metadata": {"key": "value"}
        }
        entry = LibraryEntry.from_dict(data)
        assert entry.citation_key == "smith2024machine"
        assert entry.year == 2024
        assert entry.metadata == {"key": "value"}


class TestLibraryIndex:
    """Test suite for LibraryIndex manager."""

    def test_init_creates_empty_index(self, mock_config):
        """Test initialization creates empty index."""
        index = LibraryIndex(mock_config)
        assert len(index.list_entries()) == 0

    def test_init_loads_existing_index(self, mock_config):
        """Test initialization loads existing index."""
        # Create an index file
        index_path = Path(mock_config.library_index_file)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "entries": {
                "smith2024test": {
                    "citation_key": "smith2024test",
                    "title": "Test Paper",
                    "authors": ["Smith"],
                    "year": 2024,
                    "doi": None,
                    "source": "arxiv",
                    "url": "",
                    "pdf_path": None,
                    "added_date": "",
                    "abstract": "",
                    "venue": None,
                    "citation_count": None,
                    "metadata": {}
                }
            }
        }
        with open(index_path, 'w') as f:
            json.dump(data, f)
        
        index = LibraryIndex(mock_config)
        assert len(index.list_entries()) == 1
        assert index.get_entry("smith2024test") is not None

    def test_generate_citation_key_basic(self, mock_config):
        """Test basic citation key generation."""
        index = LibraryIndex(mock_config)
        key = index.generate_citation_key(
            title="Machine Learning for Everyone",
            authors=["John Smith"],
            year=2024
        )
        assert key == "smith2024machine"

    def test_generate_citation_key_no_year(self, mock_config):
        """Test citation key with no year."""
        index = LibraryIndex(mock_config)
        key = index.generate_citation_key(
            title="A Paper",
            authors=["Author"],
            year=None
        )
        assert "nodate" in key

    def test_generate_citation_key_no_authors(self, mock_config):
        """Test citation key with no authors."""
        index = LibraryIndex(mock_config)
        key = index.generate_citation_key(
            title="A Paper",
            authors=[],
            year=2024
        )
        assert key.startswith("anonymous")

    def test_generate_citation_key_skips_common_words(self, mock_config):
        """Test that common words are skipped in title."""
        index = LibraryIndex(mock_config)
        key = index.generate_citation_key(
            title="The Art of Programming",
            authors=["Author"],
            year=2024
        )
        assert "art" in key
        assert "the" not in key

    def test_generate_citation_key_handles_special_chars(self, mock_config):
        """Test handling of special characters."""
        index = LibraryIndex(mock_config)
        key = index.generate_citation_key(
            title="O'Brien's Method: A Study",
            authors=["O'Brien, James"],
            year=2024
        )
        # Should only contain alphanumeric
        assert key.isalnum() or key.replace("2024", "").isalpha()

    def test_add_entry_basic(self, mock_config):
        """Test adding an entry."""
        index = LibraryIndex(mock_config)
        key = index.add_entry(
            title="Test Paper",
            authors=["John Smith"],
            year=2024,
            source="arxiv",
            url="http://example.com"
        )
        assert key is not None
        entry = index.get_entry(key)
        assert entry is not None
        assert entry.title == "Test Paper"

    def test_add_entry_saves_to_disk(self, mock_config):
        """Test that adding entry saves to disk."""
        index = LibraryIndex(mock_config)
        index.add_entry(
            title="Test Paper",
            authors=["Author"],
            year=2024
        )
        
        # Verify file exists and contains entry
        index_path = Path(mock_config.library_index_file)
        assert index_path.exists()
        
        with open(index_path) as f:
            data = json.load(f)
        assert len(data["entries"]) == 1

    def test_add_entry_deduplicates_by_doi(self, mock_config):
        """Test deduplication by DOI."""
        index = LibraryIndex(mock_config)
        
        key1 = index.add_entry(
            title="Paper One",
            authors=["Author"],
            year=2024,
            doi="10.1234/test"
        )
        
        key2 = index.add_entry(
            title="Paper One (Different Title)",
            authors=["Different Author"],
            year=2023,
            doi="10.1234/test"
        )
        
        assert key1 == key2
        assert len(index.list_entries()) == 1

    def test_add_entry_deduplicates_by_title(self, mock_config):
        """Test deduplication by exact title."""
        index = LibraryIndex(mock_config)
        
        key1 = index.add_entry(
            title="Exact Same Title",
            authors=["Author One"],
            year=2024
        )
        
        key2 = index.add_entry(
            title="Exact Same Title",
            authors=["Author Two"],
            year=2023
        )
        
        assert key1 == key2
        assert len(index.list_entries()) == 1

    def test_add_entry_stores_metadata(self, mock_config):
        """Test that extra metadata is stored."""
        index = LibraryIndex(mock_config)
        key = index.add_entry(
            title="Test",
            authors=["Author"],
            year=2024,
            pdf_url="http://example.com/paper.pdf",
            custom_field="custom_value"
        )
        
        entry = index.get_entry(key)
        assert entry.metadata.get("pdf_url") == "http://example.com/paper.pdf"
        assert entry.metadata.get("custom_field") == "custom_value"

    def test_update_pdf_path(self, mock_config):
        """Test updating PDF path."""
        index = LibraryIndex(mock_config)
        key = index.add_entry(
            title="Test Paper",
            authors=["Author"],
            year=2024
        )
        
        assert index.get_entry(key).pdf_path is None
        
        index.update_pdf_path(key, "pdfs/test.pdf")
        
        assert index.get_entry(key).pdf_path == "pdfs/test.pdf"

    def test_update_pdf_path_nonexistent(self, mock_config):
        """Test updating PDF path for nonexistent entry."""
        index = LibraryIndex(mock_config)
        # Should not raise, just warn
        index.update_pdf_path("nonexistent_key", "test.pdf")

    def test_get_entry_existing(self, mock_config):
        """Test getting existing entry."""
        index = LibraryIndex(mock_config)
        key = index.add_entry(
            title="Test",
            authors=["Author"],
            year=2024
        )
        entry = index.get_entry(key)
        assert entry is not None
        assert entry.title == "Test"

    def test_get_entry_nonexistent(self, mock_config):
        """Test getting nonexistent entry."""
        index = LibraryIndex(mock_config)
        entry = index.get_entry("nonexistent")
        assert entry is None

    def test_list_entries_empty(self, mock_config):
        """Test listing empty index."""
        index = LibraryIndex(mock_config)
        entries = index.list_entries()
        assert entries == []

    def test_list_entries_multiple(self, mock_config):
        """Test listing multiple entries."""
        index = LibraryIndex(mock_config)
        
        index.add_entry(title="Paper 1", authors=["A"], year=2024)
        index.add_entry(title="Paper 2", authors=["B"], year=2023)
        index.add_entry(title="Paper 3", authors=["C"], year=2022)
        
        entries = index.list_entries()
        assert len(entries) == 3

    def test_has_paper_by_doi(self, mock_config):
        """Test checking paper existence by DOI."""
        index = LibraryIndex(mock_config)
        index.add_entry(
            title="Test",
            authors=["Author"],
            year=2024,
            doi="10.1234/test"
        )
        
        assert index.has_paper(doi="10.1234/test")
        assert not index.has_paper(doi="10.1234/other")

    def test_has_paper_by_title(self, mock_config):
        """Test checking paper existence by title."""
        index = LibraryIndex(mock_config)
        index.add_entry(
            title="Specific Paper Title",
            authors=["Author"],
            year=2024
        )
        
        assert index.has_paper(title="Specific Paper Title")
        assert index.has_paper(title="  Specific Paper Title  ")  # With whitespace
        assert not index.has_paper(title="Different Title")

    def test_export_json(self, mock_config, tmp_path):
        """Test exporting to JSON."""
        index = LibraryIndex(mock_config)
        index.add_entry(title="Paper 1", authors=["A"], year=2024)
        index.add_entry(title="Paper 2", authors=["B"], year=2023)
        
        export_path = tmp_path / "export.json"
        result_path = index.export_json(export_path)
        
        assert result_path == export_path
        assert export_path.exists()
        
        with open(export_path) as f:
            data = json.load(f)
        assert len(data["entries"]) == 2
        assert data["count"] == 2
        assert "exported" in data

    def test_export_json_default_path(self, mock_config):
        """Test exporting to default path."""
        index = LibraryIndex(mock_config)
        index.add_entry(title="Test", authors=["A"], year=2024)
        
        result_path = index.export_json()
        
        assert result_path == Path(mock_config.library_index_file)

    def test_get_stats_empty(self, mock_config):
        """Test stats on empty library."""
        index = LibraryIndex(mock_config)
        stats = index.get_stats()
        
        assert stats["total_entries"] == 0
        assert stats["downloaded_pdfs"] == 0
        assert stats["sources"] == {}
        assert stats["years"] == {}

    def test_get_stats_with_entries(self, mock_config, tmp_path, monkeypatch):
        """Test stats with entries."""
        # Set up PDF directory structure matching expected layout
        literature_dir = tmp_path / "literature"
        pdf_dir = literature_dir / "pdfs"
        pdf_dir.mkdir(parents=True)
        
        # Update config to use temp path
        mock_config.download_dir = str(pdf_dir)
        mock_config.library_index_file = str(literature_dir / "library.json")
        
        # Change to temp directory so relative paths resolve correctly
        import os
        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            index = LibraryIndex(mock_config)
            
            index.add_entry(title="Paper 1", authors=["A"], year=2024, source="arxiv")
            index.add_entry(title="Paper 2", authors=["B"], year=2023, source="arxiv")
            index.add_entry(title="Paper 3", authors=["C"], year=2024, source="semanticscholar")
            
            # Add PDF path to one and create the actual file
            key = list(index._entries.keys())[0]
            pdf_path = pdf_dir / "test.pdf"
            pdf_path.write_text("fake pdf content")
            # Update with relative path - get_stats will resolve it relative to literature/
            index.update_pdf_path(key, "pdfs/test.pdf")
            
            stats = index.get_stats()
            
            assert stats["total_entries"] == 3
            assert stats["downloaded_pdfs"] == 1
            assert stats["sources"]["arxiv"] == 2
            assert stats["sources"]["semanticscholar"] == 1
            assert stats["years"][2024] == 2
            assert stats["years"][2023] == 1
            assert stats["oldest_year"] == 2023
            assert stats["newest_year"] == 2024
        finally:
            os.chdir(original_cwd)

    def test_handles_corrupt_json(self, mock_config):
        """Test handling of corrupt JSON file."""
        index_path = Path(mock_config.library_index_file)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("{invalid json")
        
        # Should not raise, just start with empty index
        index = LibraryIndex(mock_config)
        assert len(index.list_entries()) == 0

    def test_duplicate_key_handling(self, mock_config):
        """Test handling of potential duplicate keys."""
        index = LibraryIndex(mock_config)
        
        # Add first paper
        key1 = index.add_entry(
            title="Machine Learning Paper",
            authors=["Smith"],
            year=2024
        )
        
        # Add different paper that would generate same key
        key2 = index.add_entry(
            title="Machine Intelligence Paper",  # Different title, same first word
            authors=["Smith"],
            year=2024
        )
        
        # Should get different keys
        assert key1 != key2
        assert len(index.list_entries()) == 2


class TestLibraryIndexIntegration:
    """Integration tests for library index with other components."""

    def test_roundtrip_save_load(self, mock_config):
        """Test saving and loading index."""
        # Create and populate index
        index1 = LibraryIndex(mock_config)
        index1.add_entry(
            title="Test Paper",
            authors=["John Smith", "Jane Doe"],
            year=2024,
            doi="10.1234/test",
            source="arxiv",
            abstract="Test abstract"
        )
        
        # Create new index from same file
        index2 = LibraryIndex(mock_config)
        
        entries = index2.list_entries()
        assert len(entries) == 1
        assert entries[0].title == "Test Paper"
        assert entries[0].authors == ["John Smith", "Jane Doe"]
        assert entries[0].doi == "10.1234/test"

    def test_concurrent_adds(self, mock_config):
        """Test adding multiple entries in sequence."""
        index = LibraryIndex(mock_config)
        
        for i in range(10):
            index.add_entry(
                title=f"Paper {i}",
                authors=[f"Author {i}"],
                year=2020 + i
            )
        
        assert len(index.list_entries()) == 10
        
        # Verify persistence
        index2 = LibraryIndex(mock_config)
        assert len(index2.list_entries()) == 10














