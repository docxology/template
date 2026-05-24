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
    generate_citations_markdown,
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


def _make_metadata(**overrides):
    defaults = {
        "title": "Test Paper Title",
        "authors": ["Alice Smith", "Bob Jones"],
        "abstract": "This is a test abstract.",
        "keywords": ["testing", "coverage"],
        "doi": "10.5281/zenodo.12345",
        "publication_date": "2024-01-15",
        "publisher": "Test Publisher",
        "repository_url": "https://github.com/test/repo",
    }
    defaults.update(overrides)
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


class TestFormatAuthorsApaFromCitations:
    def test_no_authors(self):
        assert format_authors_apa([]) == "Unknown Author"

    def test_single_author(self):
        assert format_authors_apa(["Smith"]) == "Smith"

    def test_two_authors(self):
        result = format_authors_apa(["Smith", "Jones"])
        assert "&" in result
        assert "Smith" in result
        assert "Jones" in result

    def test_three_plus_authors(self):
        result = format_authors_apa(["Smith", "Jones", "Lee"])
        assert "et al." in result
        assert "Smith" in result


class TestFormatAuthorsMlaFromCitations:
    def test_no_authors(self):
        assert format_authors_mla([]) == "Unknown Author"

    def test_single_author(self):
        assert format_authors_mla(["Smith"]) == "Smith"

    def test_two_authors(self):
        result = format_authors_mla(["Smith", "Jones"])
        assert " and " in result

    def test_three_plus_authors(self):
        result = format_authors_mla(["Smith", "Jones", "Lee"])
        assert "et al." in result


class TestGenerateCitationBibtexFromCitations:
    def test_basic(self):
        meta = _make_metadata()
        result = generate_citation_bibtex(meta)
        assert "@software{" in result
        assert "Test Paper Title" in result
        assert "doi" in result

    def test_no_doi(self):
        meta = _make_metadata(doi=None)
        result = generate_citation_bibtex(meta)
        assert "doi" not in result

    def test_no_authors(self):
        meta = _make_metadata(authors=[])
        result = generate_citation_bibtex(meta)
        assert "unknown" in result

    def test_no_date(self):
        meta = _make_metadata(publication_date=None)
        result = generate_citation_bibtex(meta)
        assert "2024" in result


class TestGenerateCitationApaFromCitations:
    def test_with_doi(self):
        meta = _make_metadata()
        result = generate_citation_apa(meta)
        assert "doi.org" in result
        assert "2024" in result

    def test_without_doi(self):
        meta = _make_metadata(doi=None)
        result = generate_citation_apa(meta)
        assert "doi.org" not in result


class TestGenerateCitationMlaFromCitations:
    def test_with_repo(self):
        meta = _make_metadata()
        result = generate_citation_mla(meta)
        assert "github.com" in result

    def test_without_repo(self):
        meta = _make_metadata(repository_url=None)
        result = generate_citation_mla(meta)
        assert "github" not in result


class TestGenerateCitationsMarkdown:
    def test_full_markdown(self):
        meta = _make_metadata()
        result = generate_citations_markdown(meta)
        assert "# Citation" in result
        assert "BibTeX" in result
        assert "APA" in result
        assert "MLA" in result
        assert "Plain Text" in result
        assert "doi.org" in result

    def test_without_doi(self):
        meta = _make_metadata(doi=None)
        result = generate_citations_markdown(meta)
        assert "doi.org" not in result


class TestExtractCitationsFromMarkdownFromCitations:
    def test_latex_cite(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(r"See \cite{smith2020} and \cite{jones2021}.")
        result = extract_citations_from_markdown([md])
        assert "smith2020" in result
        assert "jones2021" in result

    def test_citep(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(r"Results \citep{ref2020} show.")
        result = extract_citations_from_markdown([md])
        assert "ref2020" in result

    def test_numeric_bracket(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("As shown in [1] and [2].")
        result = extract_citations_from_markdown([md])
        assert "1" in result
        assert "2" in result

    def test_numeric_paren(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("Results (3) confirm (4).")
        result = extract_citations_from_markdown([md])
        assert "3" in result

    def test_no_citations(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("No citations in this text.")
        result = extract_citations_from_markdown([md])
        assert result == []

    def test_unreadable_file(self, tmp_path):
        md = tmp_path / "bad.md"
        md.write_bytes(b"\x80\x81\x82")
        result = extract_citations_from_markdown([md])
        assert result == []

    def test_multiple_files(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text(r"\cite{alpha}")
        f2.write_text(r"\cite{beta}")
        result = extract_citations_from_markdown([f1, f2])
        assert "alpha" in result
        assert "beta" in result
