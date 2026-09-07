"""Test suite for publishing module using real implementations.

This test suite provides comprehensive validation for academic publishing tools
including DOI validation, citation generation, and metadata handling.

Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure import publishing


class TestDOIValidation:
    """Test DOI validation functionality."""

    def test_validate_doi_valid_format(self):
        """Test validation of valid DOI formats."""
        valid_dois = [
            "10.5281/zenodo.12345678",
            "10.1000/182.2024.001",
            "10.1038/s41586-018-0658-2",
        ]

        for doi in valid_dois:
            assert publishing.validate_doi(doi) == True

    def test_validate_doi_invalid_format(self):
        """Test validation of invalid DOI formats."""
        invalid_dois = [
            "",
            "invalid-doi",
            "doi:10.5281/zenodo.12345678",
            "10.5281/zenodo.12345678/extra",
        ]

        for doi in invalid_dois:
            assert publishing.validate_doi(doi) == False


class TestCitationGeneration:
    """Test citation format generation."""

    def test_generate_citation_bibtex(self):
        """Test BibTeX citation generation."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith", "Dr. John Doe"],
            abstract="Test abstract",
            keywords=["test", "research"],
        )

        bibtex = publishing.generate_citation_bibtex(metadata)

        assert "@software" in bibtex
        assert "Dr. Jane Smith" in bibtex
        assert "Dr. John Doe" in bibtex
        assert "Test Paper" in bibtex

    def test_generate_citation_apa(self):
        """Test APA citation generation."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith", "Dr. John Doe"],
            abstract="Test abstract for APA citation",
            keywords=["test", "research"],
            publication_date="2024-10-22",
        )

        apa = publishing.generate_citation_apa(metadata)

        assert "Dr. Jane Smith" in apa
        assert "Dr. John Doe" in apa
        assert "Test Paper" in apa
        assert "2024" in apa

    def test_generate_citation_mla(self):
        """Test MLA citation generation."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith", "Dr. John Doe"],
            abstract="Test abstract for MLA citation",
            keywords=["test", "research"],
        )

        mla = publishing.generate_citation_mla(metadata)

        assert "Dr. Jane Smith" in mla
        assert "Dr. John Doe" in mla
        assert "Test Paper" in mla


class TestCitationMarkdown:
    """Test markdown citation section generation."""

    def test_generate_citations_markdown(self):
        """Test generation of complete citation markdown section."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="Test abstract",
            keywords=["test"],
            doi="10.5281/zenodo.12345678",
        )

        markdown = publishing.generate_citations_markdown(metadata)

        assert "# Citation" in markdown
        assert "BibTeX" in markdown
        assert "APA Style" in markdown
        assert "MLA Style" in markdown
        assert "Plain Text" in markdown
        assert metadata.doi in markdown


class TestCitationExtraction:
    """Test citation extraction from markdown."""

    def test_extract_citations_from_markdown(self, tmp_path):
        """Test extraction of citations from markdown files."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
        See related work \\cite{smith2023} and \\cite{johnson2024}.

        Also referenced in [1] and (2).
        """
        )

        citations = publishing.extract_citations_from_markdown([md_file])

        assert "smith2023" in citations
        assert "johnson2024" in citations
        assert "1" in citations
        assert "2" in citations
