"""Tests for infrastructure/publishing/citations.py.

Tests citation formatting with real data. No mocks.
"""

from __future__ import annotations

from infrastructure.publishing.citations import (
    format_authors_apa,
    format_authors_mla,
    generate_citation_bibtex,
    generate_citation_apa,
    generate_citation_mla,
    extract_citations_from_markdown,
)
from infrastructure.publishing.models import PublicationMetadata


def make_metadata(**kwargs) -> PublicationMetadata:
    defaults = dict(
        title="Test Paper",
        authors=["Alice Smith", "Bob Jones"],
        abstract="An abstract.",
        keywords=["testing"],
        doi="10.5281/zenodo.99999",
        license="CC-BY-4.0",
    )
    defaults.update(kwargs)
    return PublicationMetadata(**defaults)


class TestFormatAuthorsApa:
    def test_empty_returns_unknown(self):
        assert format_authors_apa([]) == "Unknown Author"

    def test_single_author_returned_as_is(self):
        assert format_authors_apa(["Alice Smith"]) == "Alice Smith"

    def test_two_authors_joined_with_ampersand(self):
        result = format_authors_apa(["Alice Smith", "Bob Jones"])
        assert result == "Alice Smith & Bob Jones"

    def test_three_plus_authors_et_al(self):
        result = format_authors_apa(["Alice", "Bob", "Carol"])
        assert "et al." in result
        assert result.startswith("Alice")


class TestFormatAuthorsMla:
    def test_empty_returns_unknown(self):
        assert format_authors_mla([]) == "Unknown Author"

    def test_single_author_returned_as_is(self):
        assert format_authors_mla(["Alice Smith"]) == "Alice Smith"

    def test_two_authors_joined_with_and(self):
        result = format_authors_mla(["Alice Smith", "Bob Jones"])
        assert result == "Alice Smith and Bob Jones"

    def test_three_plus_authors_et_al(self):
        result = format_authors_mla(["Alice", "Bob", "Carol"])
        assert "et al." in result


class TestGenerateCitationBibtex:
    def test_returns_string(self):
        metadata = make_metadata()
        result = generate_citation_bibtex(metadata)
        assert isinstance(result, str)

    def test_contains_author(self):
        metadata = make_metadata(authors=["Alice Smith"])
        result = generate_citation_bibtex(metadata)
        assert "Alice Smith" in result

    def test_contains_title(self):
        metadata = make_metadata(title="My Test Paper")
        result = generate_citation_bibtex(metadata)
        assert "My Test Paper" in result

    def test_contains_license(self):
        metadata = make_metadata(license="MIT")
        result = generate_citation_bibtex(metadata)
        assert "MIT" in result

    def test_bibtex_starts_with_at(self):
        metadata = make_metadata()
        result = generate_citation_bibtex(metadata)
        assert result.strip().startswith("@")


class TestGenerateCitationApa:
    def test_returns_string(self):
        metadata = make_metadata()
        result = generate_citation_apa(metadata)
        assert isinstance(result, str)

    def test_contains_title(self):
        metadata = make_metadata(title="My Paper")
        result = generate_citation_apa(metadata)
        assert "My Paper" in result


class TestGenerateCitationMla:
    def test_returns_string(self):
        metadata = make_metadata()
        result = generate_citation_mla(metadata)
        assert isinstance(result, str)

    def test_contains_title(self):
        metadata = make_metadata(title="My Paper")
        result = generate_citation_mla(metadata)
        assert "My Paper" in result


class TestExtractCitationsFromMarkdown:
    def test_empty_file_list_returns_empty(self):
        result = extract_citations_from_markdown([])
        assert result == []

    def test_extracts_latex_cite(self, tmp_path):
        f = tmp_path / "paper.md"
        f.write_text(r"See \cite{smith2023} and \cite{jones2024}.")
        result = extract_citations_from_markdown([f])
        assert "smith2023" in result
        assert "jones2024" in result

    def test_missing_file_skipped_gracefully(self, tmp_path):
        missing = tmp_path / "nonexistent.md"
        result = extract_citations_from_markdown([missing])
        assert isinstance(result, list)

    def test_returns_sorted_list(self, tmp_path):
        f = tmp_path / "paper.md"
        f.write_text(r"\cite{zzz} \cite{aaa}")
        result = extract_citations_from_markdown([f])
        assert result == sorted(result)
