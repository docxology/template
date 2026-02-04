"""Edge case tests for publishing module.

This test suite validates edge cases including DOI validation, minimal
metadata handling, and publication readiness scenarios.
"""

from pathlib import Path

import pytest

from infrastructure.publishing import core as publishing


class TestPublishingEdgeCases:
    """Edge case tests for publishing module."""

    def test_validate_doi_edge_cases(self):
        """Test DOI validation with various edge cases."""
        # Empty string
        assert publishing.validate_doi("") == False

        # Invalid format (too short)
        assert publishing.validate_doi("10.5281") == False

        # Invalid format (missing parts)
        assert publishing.validate_doi("10.") == False

        # Valid but unusual format
        assert publishing.validate_doi("10.1000/182") == True

    def test_generate_citation_with_minimal_metadata(self):
        """Test citation generation with minimal metadata."""
        metadata = publishing.PublicationMetadata(
            title="Minimal", authors=["Author"], abstract="Abstract", keywords=[]
        )

        bibtex = publishing.generate_citation_bibtex(metadata)
        apa = publishing.generate_citation_apa(metadata)
        mla = publishing.generate_citation_mla(metadata)

        assert "Minimal" in bibtex
        assert "Author" in apa
        assert "Minimal" in mla

    def test_validate_publication_readiness_edge_cases(self, tmp_path):
        """Test publication readiness with edge cases."""
        # Empty document
        md_file = tmp_path / "empty.md"
        md_file.write_text("")

        readiness = publishing.validate_publication_readiness([md_file], [])

        assert readiness["ready_for_publication"] == False
        assert readiness["completeness_score"] < 50

    def test_extract_citations_from_markdown_various_formats(self, tmp_path):
        """Test citation extraction with various formats."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            r"""
        References include \cite{ref1}, [2], (Smith, 2024), and \cite{ref3,ref4}.
        """
        )

        citations = publishing.extract_citations_from_markdown([md_file])

        assert "ref1" in citations
        assert "2" in citations
        # Combined citation ref3,ref4 is extracted as a single string
        assert "ref3,ref4" in citations or ("ref3" in citations and "ref4" in citations)
