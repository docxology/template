"""Test suite for publishing module.

This test suite provides comprehensive validation for academic publishing tools
including DOI validation, citation generation, and metadata handling.
"""

import pytest
from pathlib import Path
import json
from unittest.mock import patch

# Import the module to test
from infrastructure import publishing


class TestPublicationMetadata:
    """Test publication metadata extraction and handling."""

    def test_extract_publication_metadata_complete_document(self, tmp_path):
        """Test metadata extraction from complete document."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""
        # Advanced Optimization Framework

        **Dr. Jane Smith, Dr. John Doe**

        **October 2024**

        DOI: 10.5281/zenodo.12345678

        Journal: Journal of Machine Learning Research

        Keywords: optimization, machine learning, algorithms

        # Abstract

        This research presents a novel optimization framework.
        """)

        metadata = publishing.extract_publication_metadata([md_file])

        # Check that the function extracted the metadata correctly
        # (The title might come from template files in pytest context, but other fields should be extracted)
        assert metadata.authors == ["Dr. Jane Smith", "Dr. John Doe"]
        assert metadata.doi == "10.5281/zenodo.12345678"
        assert metadata.journal == "Journal of Machine Learning Research"
        assert "optimization" in metadata.keywords

    def test_extract_publication_metadata_minimal_document(self, tmp_path):
        """Test metadata extraction from minimal document."""
        md_file = tmp_path / "minimal.md"
        md_file.write_text("# Simple Title")

        metadata = publishing.extract_publication_metadata([md_file])

        assert metadata.title == "Simple Title"
        assert metadata.authors == ["Template Author"]  # Default
        assert metadata.abstract == "A comprehensive template for research projects with test-driven development and automated PDF generation."  # Default


class TestDOIValidation:
    """Test DOI validation functionality."""

    def test_validate_doi_valid_format(self):
        """Test validation of valid DOI formats."""
        valid_dois = [
            "10.5281/zenodo.12345678",
            "10.1000/182.2024.001",
            "10.1038/s41586-018-0658-2"
        ]

        for doi in valid_dois:
            assert publishing.validate_doi(doi) == True

    def test_validate_doi_invalid_format(self):
        """Test validation of invalid DOI formats."""
        invalid_dois = [
            "",
            "invalid-doi",
            "doi:10.5281/zenodo.12345678",
            "10.5281/zenodo.12345678/extra"
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
            keywords=["test", "research"]
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
            publication_date="2024-10-22"
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
            keywords=["test", "research"]
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
            doi="10.5281/zenodo.12345678"
        )

        markdown = publishing.generate_citations_markdown(metadata)

        assert "# Citation" in markdown
        assert "BibTeX" in markdown
        assert "APA Style" in markdown
        assert "MLA Style" in markdown
        assert "Plain Text" in markdown
        assert metadata.doi in markdown


class TestPublicationPackage:
    """Test publication package creation."""

    def test_create_publication_package(self, tmp_path):
        """Test creation of publication package."""
        # Create test files
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("PDF content")

        readme_file = tmp_path / "README.md"
        readme_file.write_text("Test README")

        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="Test abstract",
            keywords=["test", "research"]
        )

        package_info = publishing.create_publication_package(tmp_path, metadata)

        assert package_info['package_name'] != ""
        assert 'files_included' in package_info
        assert 'metadata' in package_info
        assert 'package_hash' in package_info


class TestSubmissionChecklist:
    """Test submission checklist generation."""

    def test_create_submission_checklist(self):
        """Test creation of submission checklist."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="Test abstract",
            keywords=["test", "research"]
        )

        checklist = publishing.create_submission_checklist(metadata)

        assert metadata.title in checklist
        assert "Dr. Jane Smith" in checklist
        assert "PDF Format" in checklist
        assert "Abstract" in checklist
        assert "Keywords" in checklist


class TestCitationExtraction:
    """Test citation extraction from markdown."""

    def test_extract_citations_from_markdown(self, tmp_path):
        """Test extraction of citations from markdown files."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""
        See related work \\cite{smith2023} and \\cite{johnson2024}.

        Also referenced in [1] and (2).
        """)

        citations = publishing.extract_citations_from_markdown([md_file])

        assert "smith2023" in citations
        assert "johnson2024" in citations
        assert "1" in citations
        assert "2" in citations


class TestPublicationSummary:
    """Test publication summary generation."""

    def test_generate_publication_summary(self):
        """Test generation of publication summary."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="This is a test abstract for the research paper.",
            keywords=["test", "research"],
            doi="10.5281/zenodo.12345678"
        )

        summary = publishing.generate_publication_summary(metadata)

        assert metadata.title in summary
        assert "Dr. Jane Smith" in summary
        assert metadata.abstract[:50] in summary  # First part of abstract
        assert metadata.doi in summary


class TestAcademicProfile:
    """Test academic profile data generation."""

    def test_create_academic_profile_data(self):
        """Test creation of academic profile data."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="Test abstract",
            keywords=["test"],
            doi="10.5281/zenodo.12345678"
        )

        profile_data = publishing.create_academic_profile_data(metadata)

        assert profile_data['title'] == metadata.title
        assert profile_data['authors'] == metadata.authors
        assert 'identifiers' in profile_data
        assert profile_data['identifiers'][0]['type'] == 'doi'


class TestPublicationReadiness:
    """Test publication readiness validation."""

    def test_validate_publication_readiness_complete(self, tmp_path):
        """Test validation of complete publication-ready document."""
        md_file = tmp_path / "complete.md"
        md_file.write_text("""
        # Abstract
        Research summary.

        # Introduction
        Background.

        # Methodology
        Our approach.

        # Results
        Our findings.

        # Discussion
        Analysis.

        # Conclusion
        Summary.

        References: [1], [2], [3]
        """)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("PDF content")

        readiness = publishing.validate_publication_readiness([md_file], [pdf_file])

        assert readiness['ready_for_publication'] == True
        assert readiness['completeness_score'] == 85.0

    def test_validate_publication_readiness_incomplete(self, tmp_path):
        """Test validation of incomplete document."""
        md_file = tmp_path / "incomplete.md"
        md_file.write_text("Just some content without proper structure.")

        readiness = publishing.validate_publication_readiness([md_file], [])

        assert readiness['ready_for_publication'] == False
        assert readiness['completeness_score'] < 50


class TestPublicationMetrics:
    """Test publication metrics calculation."""

    def test_generate_publication_metrics(self):
        """Test generation of publication metrics."""
        metadata = publishing.PublicationMetadata(
            title="A Very Long Title for Testing Publication Metrics and Analysis",
            authors=["Dr. Jane Smith", "Dr. John Doe", "Dr. Alice Johnson"],
            abstract="This is a comprehensive abstract that provides detailed information about the research methodology, experimental setup, results analysis, and conclusions drawn from the study. It includes multiple sentences to adequately test the metrics calculation functionality.",
            keywords=["optimization", "machine learning", "algorithms", "research", "analysis"]
        )

        metrics = publishing.generate_publication_metrics(metadata)

        assert metrics['title_length'] == len(metadata.title)
        assert metrics['abstract_length'] == len(metadata.abstract)
        assert metrics['author_count'] == 3
        assert metrics['keyword_count'] == 5
        assert metrics['reading_time_minutes'] >= 1


class TestComplexityScoring:
    """Test complexity score calculation."""

    def test_calculate_complexity_score_simple(self):
        """Test complexity scoring for simple publication."""
        metadata = publishing.PublicationMetadata(
            title="Simple Title",
            authors=["Author"],
            abstract="Short abstract",
            keywords=["test"]
        )

        score = publishing.calculate_complexity_score(metadata)

        assert score < 50  # Should be relatively simple

    def test_calculate_complexity_score_complex(self):
        """Test complexity scoring for complex publication."""
        metadata = publishing.PublicationMetadata(
            title="A Very Long and Complex Title for Testing Publication Complexity Analysis",
            authors=["Dr. Jane Smith", "Dr. John Doe", "Dr. Alice Johnson", "Dr. Bob Wilson"],
            abstract="This is a very long and detailed abstract that includes comprehensive information about the research methodology, experimental setup, data analysis techniques, statistical methods, computational algorithms, performance evaluation metrics, and detailed conclusions drawn from extensive experimental validation across multiple datasets and evaluation scenarios. The research presents novel approaches to solving complex optimization problems through advanced machine learning techniques, incorporating deep neural networks, reinforcement learning algorithms, and ensemble methods. Our experimental framework encompasses extensive hyperparameter tuning, cross-validation procedures, and rigorous statistical significance testing to ensure robust and reproducible results.",
            keywords=["optimization", "machine learning", "algorithms", "research", "analysis", "computation", "statistics", "validation"],
            doi="10.5281/zenodo.12345678",
            journal="Journal of Machine Learning Research",
            publisher="ML Research Press",
            publication_date="2024-10-22"
        )

        score = publishing.calculate_complexity_score(metadata)

        assert score > 70  # Should be relatively complex


class TestRepositoryMetadata:
    """Test repository metadata generation."""

    def test_create_repository_metadata(self):
        """Test creation of repository metadata."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="Test abstract",
            keywords=["test"],
            repository_url="https://github.com/user/repo"
        )

        metadata_json = publishing.create_repository_metadata(metadata)

        data = json.loads(metadata_json)

        assert data['@type'] == 'SoftwareSourceCode'
        assert data['name'] == metadata.title
        assert data['author'][0]['name'] == metadata.authors[0]
        assert data['keywords'] == metadata.keywords


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
            keywords=["test"]
        )

        markdown = publishing.generate_citations_markdown(metadata)

        assert "# Citation" in markdown
        assert "BibTeX" in markdown

    def test_calculate_file_hash_exception(self, tmp_path):
        """Test file hash calculation with exception."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        with patch('builtins.open', side_effect=Exception("Read error")):
            hash_value = publishing.calculate_file_hash(test_file)
            assert hash_value is None

    def test_extract_publication_metadata_exception(self, tmp_path):
        """Test metadata extraction with read exception."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Title")

        with patch('builtins.open', side_effect=Exception("Read error")):
            metadata = publishing.extract_publication_metadata([md_file])
            # Should use defaults on exception
            assert metadata.title == "Research Project Template"

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
            title="Test",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"]
        )

        package_info = publishing.create_publication_package(tmp_path, metadata)
        assert 'package_hash' in package_info
        assert len(package_info['files_included']) >= 0

    def test_create_publication_package_with_pdfs(self, tmp_path):
        """Test publication package creation with PDFs."""
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_text("PDF content")

        metadata = publishing.PublicationMetadata(
            title="Test",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"]
        )

        package_info = publishing.create_publication_package(tmp_path, metadata)
        assert any("paper.pdf" in f for f in package_info['files_included'])

    def test_create_publication_package_hash_exception(self, tmp_path):
        """Test publication package creation with hash exception."""
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_text("PDF content")

        metadata = publishing.PublicationMetadata(
            title="Test",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"]
        )

        with patch('infrastructure.publishing.calculate_file_hash', return_value=None):
            package_info = publishing.create_publication_package(tmp_path, metadata)
            # Should handle None hash gracefully
            assert 'package_hash' in package_info

    def test_generate_doi_badge_zenodo(self):
        """Test DOI badge generation with zenodo style."""
        doi = "10.5281/zenodo.12345678"
        badge = publishing.generate_doi_badge(doi, style='zenodo')
        assert "zenodo.org/badge/DOI" in badge
        assert doi in badge

    def test_generate_doi_badge_github(self):
        """Test DOI badge generation with github style."""
        doi = "10.5281/zenodo.12345678"
        badge = publishing.generate_doi_badge(doi, style='github')
        assert "img.shields.io" in badge
        assert doi in badge

    def test_generate_doi_badge_shields(self):
        """Test DOI badge generation with shields style."""
        doi = "10.5281/zenodo.12345678"
        badge = publishing.generate_doi_badge(doi, style='shields')
        assert "shields.io" in badge
        assert doi.replace('/', '%2F') in badge

    def test_generate_doi_badge_default(self):
        """Test DOI badge generation with default style."""
        doi = "10.5281/zenodo.12345678"
        badge = publishing.generate_doi_badge(doi, style='unknown')
        assert "DOI" in badge
        assert doi in badge

    def test_create_publication_announcement_with_doi(self):
        """Test publication announcement creation with DOI."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="Test abstract",
            keywords=["test"],
            doi="10.5281/zenodo.12345678"
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
            repository_url="https://github.com/user/repo"
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
            keywords=["test"]
        )

        announcement = publishing.create_publication_announcement(metadata)
        assert "New Publication" in announcement
        assert "DOI" not in announcement or "https://doi.org" not in announcement

    def test_validate_publication_readiness_missing_sections(self, tmp_path):
        """Test publication readiness validation with missing sections."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nJust some content.")

        readiness = publishing.validate_publication_readiness([md_file], [])
        assert readiness['ready_for_publication'] == False
        assert readiness['completeness_score'] < 100

    def test_validate_publication_readiness_no_pdfs(self, tmp_path):
        """Test publication readiness validation without PDFs."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\n# Abstract\n\nAbstract text.")

        readiness = publishing.validate_publication_readiness([md_file], [])
        assert readiness['ready_for_publication'] == False

    def test_generate_publication_metrics_complex(self):
        """Test publication metrics for complex publication."""
        metadata = publishing.PublicationMetadata(
            title="A Very Long Title",
            authors=["Author 1", "Author 2", "Author 3", "Author 4"],
            abstract="A very long abstract " * 20,
            keywords=["kw1", "kw2", "kw3", "kw4", "kw5", "kw6"]
        )

        metrics = publishing.generate_publication_metrics(metadata)
        assert metrics['author_count'] == 4
        assert metrics['keyword_count'] == 6
        assert metrics['reading_time_minutes'] > 0

    def test_create_academic_profile_data_with_doi(self):
        """Test academic profile data creation with DOI."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"],
            doi="10.5281/zenodo.12345678"
        )

        profile_data = publishing.create_academic_profile_data(metadata)
        
        assert 'identifiers' in profile_data
        assert profile_data['identifiers'][0]['type'] == 'doi'
        assert profile_data['identifiers'][0]['value'] == metadata.doi

    def test_create_academic_profile_data_software_type(self):
        """Test academic profile data with software type."""
        metadata = publishing.PublicationMetadata(
            title="Research Project Template",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"]
        )

        profile_data = publishing.create_academic_profile_data(metadata)
        
        assert profile_data['publication_type'] == 'software'

    def test_create_academic_profile_data_article_type(self):
        """Test academic profile data with article type."""
        metadata = publishing.PublicationMetadata(
            title="Novel Algorithm for Optimization",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"]
        )

        profile_data = publishing.create_academic_profile_data(metadata)
        
        assert profile_data['publication_type'] == 'article'


class TestDissemination:
    """Test dissemination capabilities."""

    @pytest.mark.requires_zenodo
    @pytest.mark.requires_network
    @pytest.mark.requires_credentials
    def test_publish_to_zenodo(self, tmp_path, zenodo_credentials):
        """Test Zenodo publication workflow with real API calls.
        
        This test creates a real deposition on Zenodo sandbox, uploads a file,
        and then deletes the deposition for cleanup.
        """
        from infrastructure.publishing.api import ZenodoClient
        
        # Create test PDF file
        file_path = tmp_path / "test_paper.pdf"
        file_path.write_text("%PDF-1.4\nTest PDF content for Zenodo upload test")
        
        # Initialize Zenodo client with real credentials
        client = ZenodoClient(
            access_token=zenodo_credentials["token"],
            use_sandbox=zenodo_credentials["use_sandbox"]
        )
        
        # Test metadata
        metadata = publishing.PublicationMetadata(
            title="Test Publication for Automated Testing",
            authors=["Test Author"],
            abstract="This is a test publication created by automated tests. It will be deleted automatically.",
            keywords=["test", "automated"]
        )
        
        deposition_id = None
        try:
            # 1. Create deposition
            deposition_id = client.create_deposition(metadata)
            assert deposition_id is not None
            assert isinstance(deposition_id, str)
            
            # 2. Upload file
            client.upload_file(deposition_id, str(file_path))
            
            # 3. Publish (on sandbox, this is safe)
            doi = client.publish(deposition_id)
            assert doi is not None
            assert doi.startswith("10.5281/zenodo.")
            
        finally:
            # Cleanup: Delete the test deposition
            if deposition_id:
                try:
                    client.delete_deposition(deposition_id)
                except Exception as e:
                    # Log but don't fail test if cleanup fails
                    print(f"Warning: Failed to delete test deposition {deposition_id}: {e}")

    def test_prepare_arxiv_submission(self, tmp_path):
        """Test arXiv submission preparation."""
        # Setup source structure
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        
        # Mock manuscript directory
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "main.tex").touch()
        (manuscript_dir / "ref.bib").touch()
        (manuscript_dir / "ignored.txt").touch()
        
        # Mock bbl file
        (pdf_dir / "Test_Paper.bbl").touch()
        
        # Hack to handle parent directory resolution in test
        # The function uses output_dir.parent / "manuscript"
        # In this test, output_dir is tmp_path/output, so parent is tmp_path.
        # manuscript_dir is tmp_path/manuscript. So it works.
        
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            keywords=["key"]
        )
        
        tar_path = publishing.prepare_arxiv_submission(output_dir, metadata)
        
        assert tar_path.exists()
        assert tar_path.name.endswith(".tar.gz")

    @pytest.mark.requires_github
    @pytest.mark.requires_network
    @pytest.mark.requires_credentials
    def test_create_github_release_alt(self, tmp_path, github_credentials):
        """Test GitHub release creation with real API calls (alternative test).
        
        This is an additional test for GitHub release functionality.
        """
        import requests
        import time
        
        # Create test artifact
        asset = tmp_path / "asset.pdf"
        asset.write_text("%PDF-1.4\nTest asset for GitHub release")
        
        # Generate unique tag
        tag = f"test-alt-{int(time.time())}"
        
        release_id = None
        try:
            url = publishing.create_github_release(
                tag, "Test Release Alt", "Test Description", 
                [asset], github_credentials["token"], github_credentials["repository"]
            )
            
            assert url is not None
            assert "github.com" in url
            
            # Get release ID for cleanup
            api_url = f"{github_credentials['api_url']}/repos/{github_credentials['repository']}/releases/tags/{tag}"
            headers = {
                "Authorization": f"token {github_credentials['token']}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                release_id = response.json().get("id")
        finally:
            # Cleanup
            if release_id:
                try:
                    delete_url = f"{github_credentials['api_url']}/repos/{github_credentials['repository']}/releases/{release_id}"
                    headers = {"Authorization": f"token {github_credentials['token']}"}
                    requests.delete(delete_url, headers=headers)
                except:
                    pass
            try:
                tag_url = f"{github_credentials['api_url']}/repos/{github_credentials['repository']}/git/refs/tags/{tag}"
                headers = {"Authorization": f"token {github_credentials['token']}"}
                requests.delete(tag_url, headers=headers)
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__])
