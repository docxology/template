"""Tests for infrastructure.publishing.citations — comprehensive coverage."""


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


class TestFormatAuthorsMla:
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


class TestGenerateCitationBibtex:
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


class TestGenerateCitationApa:
    def test_with_doi(self):
        meta = _make_metadata()
        result = generate_citation_apa(meta)
        assert "doi.org" in result
        assert "2024" in result

    def test_without_doi(self):
        meta = _make_metadata(doi=None)
        result = generate_citation_apa(meta)
        assert "doi.org" not in result


class TestGenerateCitationMla:
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


class TestExtractCitationsFromMarkdown:
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
