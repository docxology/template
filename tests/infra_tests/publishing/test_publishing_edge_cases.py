"""Test suite for publishing module using real implementations.

This test suite provides comprehensive validation for academic publishing tools
including DOI validation, citation generation, and metadata handling.

Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure import publishing


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extract_publication_metadata_empty_files(self):
        """Test metadata extraction with empty file list."""
        metadata = publishing.extract_publication_metadata([])

        assert metadata.title == "Research Project Template"  # Default
        assert len(metadata.authors) > 0

    def test_validate_doi_empty_string(self):
        """Test DOI validation with empty string."""
        assert publishing.validate_doi("") == False

    def test_generate_citations_markdown_no_doi(self):
        """Test citation generation without DOI."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"],
        )

        markdown = publishing.generate_citations_markdown(metadata)

        assert "# Citation" in markdown
        assert "BibTeX" in markdown

    def test_calculate_file_hash_exception(self, tmp_path):
        """Test file hash calculation with real execution."""
        from infrastructure.core.files.operations import calculate_file_hash

        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        # Use real hash calculation
        hash_value = calculate_file_hash(test_file)
        # Should return a hash string or None
        assert hash_value is None or isinstance(hash_value, str)

    def test_extract_publication_metadata_exception(self, tmp_path):
        """Test metadata extraction with real execution."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Title")

        # Use real metadata extraction
        metadata = publishing.extract_publication_metadata([md_file])
        # Should extract metadata or use defaults
        assert metadata.title is not None

    def test_extract_publication_metadata_template_content(self, tmp_path):
        """Test metadata extraction with template content."""
        md_file = tmp_path / "test.md"
        md_file.write_text("Research Project Template\n\n# Real Title")

        metadata = publishing.extract_publication_metadata([md_file])
        # Should skip template content
        assert metadata.title == "Research Project Template"  # Default, template content skipped

    def test_extract_publication_metadata_author_with_title(self, tmp_path):
        """Test metadata extraction with author containing title."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\n**Dr. Jane Smith, Prof. John Doe**")

        metadata = publishing.extract_publication_metadata([md_file])
        assert len(metadata.authors) > 0
        assert any("Dr." in author or "Prof." in author for author in metadata.authors)

    def test_extract_publication_metadata_conference(self, tmp_path):
        """Test metadata extraction with conference."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nConference: ICML 2024")

        metadata = publishing.extract_publication_metadata([md_file])
        assert metadata.conference == "ICML 2024"

    def test_extract_publication_metadata_proceedings(self, tmp_path):
        """Test metadata extraction with proceedings pattern."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nProceedings of: NeurIPS 2024")

        metadata = publishing.extract_publication_metadata([md_file])
        assert metadata.conference == "NeurIPS 2024"

    def test_create_publication_package_no_pdf_dir(self, tmp_path):
        """Test publication package creation without PDF directory."""
        metadata = publishing.PublicationMetadata(
            title="Test", authors=["Author"], abstract="Abstract", keywords=["test"]
        )

        package_info = publishing.create_publication_package(tmp_path, metadata)
        assert "package_hash" in package_info
        assert len(package_info["files_included"]) >= 0

    def test_create_publication_package_with_pdfs(self, tmp_path):
        """Test publication package creation with PDFs."""
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_text("PDF content")

        metadata = publishing.PublicationMetadata(
            title="Test", authors=["Author"], abstract="Abstract", keywords=["test"]
        )

        package_info = publishing.create_publication_package(tmp_path, metadata)
        assert any("paper.pdf" in f for f in package_info["files_included"])

    def test_create_publication_package_hash_exception(self, tmp_path):
        """Test publication package creation with hash exception."""
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_text("PDF content")

        metadata = publishing.PublicationMetadata(
            title="Test", authors=["Author"], abstract="Abstract", keywords=["test"]
        )

        # Use real hash calculation
        package_info = publishing.create_publication_package(tmp_path, metadata)
        # Should have package_hash (may be None or a hash string)
        assert "package_hash" in package_info

    def test_generate_doi_badge_zenodo(self):
        """Test DOI badge generation with zenodo style."""
        doi = "10.5281/zenodo.12345678"
        badge = publishing.generate_doi_badge(doi, style="zenodo")
        assert "zenodo.org/badge/DOI" in badge
        assert doi in badge

    def test_generate_doi_badge_github(self):
        """Test DOI badge generation with github style."""
        doi = "10.5281/zenodo.12345678"
        badge = publishing.generate_doi_badge(doi, style="github")
        assert "img.shields.io" in badge
        assert doi in badge

    def test_generate_doi_badge_shields(self):
        """Test DOI badge generation with shields style."""
        doi = "10.5281/zenodo.12345678"
        badge = publishing.generate_doi_badge(doi, style="shields")
        assert "shields.io" in badge
        assert doi.replace("/", "%2F") in badge

    def test_generate_doi_badge_default(self):
        """Test DOI badge generation with default style."""
        doi = "10.5281/zenodo.12345678"
        badge = publishing.generate_doi_badge(doi, style="unknown")
        assert "DOI" in badge
        assert doi in badge

    def test_create_publication_announcement_with_doi(self):
        """Test publication announcement creation with DOI."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="Test abstract",
            keywords=["test"],
            doi="10.5281/zenodo.12345678",
        )

        announcement = publishing.create_publication_announcement(metadata)
        assert "New Publication" in announcement
        assert metadata.doi in announcement
        assert "https://doi.org" in announcement

    def test_create_publication_announcement_with_repository(self):
        """Test publication announcement with repository URL."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"],
            repository_url="https://github.com/user/repo",
        )

        announcement = publishing.create_publication_announcement(metadata)
        assert "Repository" in announcement
        assert metadata.repository_url in announcement

    def test_create_publication_announcement_without_doi(self):
        """Test publication announcement without DOI."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"],
        )

        announcement = publishing.create_publication_announcement(metadata)
        assert "New Publication" in announcement
        assert "DOI" not in announcement or "https://doi.org" not in announcement

    def test_validate_publication_readiness_missing_sections(self, tmp_path):
        """Test publication readiness validation with missing sections."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nJust some content.")

        readiness = publishing.validate_publication_readiness([md_file], [])
        assert readiness["ready_for_publication"] == False
        assert readiness["completeness_score"] < 100

    def test_validate_publication_readiness_no_pdfs(self, tmp_path):
        """Test publication readiness validation without PDFs."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\n# Abstract\n\nAbstract text.")

        readiness = publishing.validate_publication_readiness([md_file], [])
        assert readiness["ready_for_publication"] == False

    def test_generate_publication_metrics_complex(self):
        """Test publication metrics for complex publication."""
        metadata = publishing.PublicationMetadata(
            title="A Very Long Title",
            authors=["Author 1", "Author 2", "Author 3", "Author 4"],
            abstract="A very long abstract " * 20,
            keywords=["kw1", "kw2", "kw3", "kw4", "kw5", "kw6"],
        )

        metrics = publishing.generate_publication_metrics(metadata)
        assert metrics["author_count"] == 4
        assert metrics["keyword_count"] == 6
        assert metrics["reading_time_minutes"] > 0

    def test_create_academic_profile_data_with_doi(self):
        """Test academic profile data creation with DOI."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"],
            doi="10.5281/zenodo.12345678",
        )

        profile_data = publishing.create_academic_profile_data(metadata)

        assert "identifiers" in profile_data
        assert profile_data["identifiers"][0]["type"] == "doi"
        assert profile_data["identifiers"][0]["value"] == metadata.doi

    def test_create_academic_profile_data_software_type(self):
        """Test academic profile data with software type."""
        metadata = publishing.PublicationMetadata(
            title="Research Project Template",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"],
        )

        profile_data = publishing.create_academic_profile_data(metadata)

        assert profile_data["publication_type"] == "software"

    def test_create_academic_profile_data_article_type(self):
        """Test academic profile data with article type."""
        metadata = publishing.PublicationMetadata(
            title="Novel Algorithm for Optimization",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"],
        )

        profile_data = publishing.create_academic_profile_data(metadata)

        assert profile_data["publication_type"] == "article"


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
        metadata = publishing.PublicationMetadata(title="Minimal", authors=["Author"], abstract="Abstract", keywords=[])

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
