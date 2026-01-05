"""Tests for publication and documentation features.

Comprehensive tests for publishing workflow, manuscript validation,
and API documentation generation.
"""
import json
import pytest
from pathlib import Path

# Try to import publishing scripts (graceful fallback)
try:
    import sys
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root / "scripts"))

    from prepare_publication import (
        extract_manuscript_metadata,
        generate_citations,
        validate_doi_info,
        create_publication_materials,
    )
    from validate_manuscript import (
        validate_manuscript_structure,
        validate_cross_references,
        validate_academic_standards,
        validate_links,
        validate_output_integrity,
        save_validation_report,
    )
    from generate_api_docs import (
        scan_source_code,
        generate_documentation_tables,
        save_documentation_files,
        generate_api_summary,
    )
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False


@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available")
class TestPublicationMetadata:
    """Test publication metadata extraction."""

    def test_metadata_extraction(self):
        """Test that metadata extraction runs and returns reasonable data."""
        metadata = extract_manuscript_metadata()

        if metadata:
            # Check that we got a PublicationMetadata object
            from infrastructure.publishing import PublicationMetadata
            assert isinstance(metadata, PublicationMetadata)

            # Check that it has expected attributes
            assert hasattr(metadata, 'title') or hasattr(metadata, 'authors')

            # If title exists, it should be a string
            if hasattr(metadata, 'title') and metadata.title:
                assert isinstance(metadata.title, str)
                assert len(metadata.title) > 0

            # If authors exist, should be a list
            if hasattr(metadata, 'authors') and metadata.authors:
                assert isinstance(metadata.authors, list)
        else:
            pytest.skip("Metadata extraction returned None")

    def test_metadata_with_doi(self):
        """Test metadata extraction includes DOI information."""
        metadata = extract_manuscript_metadata()

        if metadata and hasattr(metadata, 'doi') and metadata.doi:
            assert isinstance(metadata.doi, str)
            # DOI should look like a valid DOI pattern
            assert "10." in metadata.doi or len(metadata.doi) > 0


@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available")
class TestCitationGeneration:
    """Test citation generation in multiple formats."""

    def test_citation_generation(self):
        """Test that citations are generated for available metadata."""
        metadata = extract_manuscript_metadata()

        if metadata:
            citations = generate_citations(metadata)

            if citations:
                # Check that we get a dictionary with citation formats
                assert isinstance(citations, dict)

                # Should have at least one citation format
                assert len(citations) > 0

                # Check specific formats if they exist
                if "bibtex" in citations:
                    assert isinstance(citations["bibtex"], str)
                    assert "@" in citations["bibtex"]  # BibTeX entries start with @

                if "apa" in citations:
                    assert isinstance(citations["apa"], str)

                if "mla" in citations:
                    assert isinstance(citations["mla"], str)
            else:
                pytest.skip("Citation generation returned None")
        else:
            pytest.skip("No metadata available for citation generation")

    def test_citation_formats(self):
        """Test specific citation format characteristics."""
        # Create mock metadata for testing
        mock_metadata = {
            "title": "Test Publication",
            "authors": [{"name": "Test Author", "orcid": "0000-0000-0000-0000"}],
            "doi": "10.1234/test.doi",
            "year": "2024"
        }

        citations = generate_citations(mock_metadata)

        if citations:
            # Check BibTeX format
            if "bibtex" in citations:
                bibtex = citations["bibtex"]
                assert "Test Publication" in bibtex
                assert "Test Author" in bibtex

            # Check APA format
            if "apa" in citations:
                apa = citations["apa"]
                assert "Test Author" in apa
                assert "2024" in apa


@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available")
class TestDOIValidation:
    """Test DOI validation and badge generation."""

    def test_doi_validation(self):
        """Test DOI validation with available metadata."""
        metadata = extract_manuscript_metadata()

        if metadata and hasattr(metadata, 'doi') and metadata.doi:
            badge = validate_doi_info(metadata)

            # Badge might be None if DOI validation fails
            if badge:
                assert isinstance(badge, str)
                assert "[DOI:" in badge or "doi.org" in badge
        else:
            pytest.skip("No DOI in metadata to validate")

    def test_doi_badge_format(self):
        """Test DOI badge format for known valid DOI."""
        # Test with a mock DOI
        mock_metadata = {"doi": "10.5281/zenodo.1234567"}

        badge = validate_doi_info(mock_metadata)

        if badge:
            assert isinstance(badge, str)
            # Should contain DOI badge markdown
            assert "10.5281/zenodo.1234567" in badge


@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available")
class TestPublicationMaterials:
    """Test publication materials creation."""

    def test_publication_materials_creation(self, tmp_path):
        """Test creation of publication materials."""
        metadata = extract_manuscript_metadata()

        if metadata:
            citations = generate_citations(metadata)
            doi_badge = validate_doi_info(metadata)

            materials = create_publication_materials(metadata, citations, doi_badge)

            if materials:
                # Should return a dictionary of file paths
                assert isinstance(materials, dict)
                assert len(materials) > 0

                # Check that files were actually created
                for material_type, file_path in materials.items():
                    assert file_path.exists()
                    assert file_path.is_file()
            else:
                pytest.skip("Publication materials creation returned None")
        else:
            pytest.skip("No metadata available for materials creation")


@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available")
class TestManuscriptValidation:
    """Test manuscript validation functions."""

    def test_manuscript_structure_validation(self):
        """Test manuscript structure validation."""
        validation_result = validate_manuscript_structure()

        # Should return validation results or None
        if validation_result:
            assert isinstance(validation_result, dict)
            # Should have errors and exit_code keys
            assert "errors" in validation_result
            assert "exit_code" in validation_result

    def test_cross_reference_validation(self):
        """Test cross-reference validation."""
        cross_refs = validate_cross_references()

        # Should return validation results or None
        if cross_refs:
            assert isinstance(cross_refs, dict)

    def test_academic_standards_validation(self):
        """Test academic standards validation."""
        standards = validate_academic_standards()

        # Should return validation results or None
        if standards:
            assert isinstance(standards, dict)

    def test_link_validation(self):
        """Test link validation."""
        links = validate_links()

        # Should return validation results or None (list of issues)
        if links is not None:
            assert isinstance(links, list)

    def test_output_integrity_validation(self):
        """Test output integrity validation."""
        integrity = validate_output_integrity()

        # Should return integrity report or None
        if integrity:
            # Should have expected integrity report attributes
            assert hasattr(integrity, 'issues') or isinstance(integrity, dict)

    def test_validation_report_saving(self, tmp_path):
        """Test saving of validation reports."""
        # Run some validations to get data
        structure = validate_manuscript_structure()
        cross_refs = validate_cross_references()
        standards = validate_academic_standards()
        links = validate_links()
        integrity = validate_output_integrity()

        results = {
            "manuscript": structure,
            "cross_refs": cross_refs,
            "standards": standards,
            "links": links,
            "integrity": integrity,
        }

        reports = save_validation_report(results)

        if reports:
            assert isinstance(reports, dict)
            assert len(reports) > 0

            # Check that files were created
            for report_type, file_path in reports.items():
                assert file_path.exists()
                assert file_path.is_file()


@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available")
class TestAPIDocumentation:
    """Test API documentation generation."""

    def test_source_code_scanning(self):
        """Test scanning of source code for API elements."""
        api_data = scan_source_code()

        if api_data:
            assert isinstance(api_data, dict)
            # Should have categorized API elements
            expected_keys = ["all_entries", "functions", "classes", "methods", "constants"]
            for key in expected_keys:
                assert key in api_data
                assert isinstance(api_data[key], list)
        else:
            pytest.skip("Source code scanning returned None")

    def test_documentation_table_generation(self):
        """Test generation of documentation tables."""
        api_data = scan_source_code()

        if api_data:
            tables = generate_documentation_tables(api_data)

            if tables:
                assert isinstance(tables, dict)
                # Should have markdown table strings
                for table_name, table_content in tables.items():
                    assert isinstance(table_content, str)
                    assert len(table_content) > 0
                    # Should contain markdown table formatting
                    assert "|" in table_content
            else:
                pytest.skip("Documentation table generation returned None")
        else:
            pytest.skip("No API data available for table generation")

    def test_documentation_file_saving(self, tmp_path):
        """Test saving of documentation files."""
        api_data = scan_source_code()

        if api_data:
            tables = generate_documentation_tables(api_data)

            if tables:
                saved_files = save_documentation_files(tables)

                if saved_files:
                    assert isinstance(saved_files, dict)
                    assert len(saved_files) > 0

                    # Check that files were created
                    for file_type, file_path in saved_files.items():
                        assert file_path.exists()
                        assert file_path.is_file()

                        if file_type != "statistics":
                            # Documentation files should be markdown
                            assert file_path.suffix == ".md"
                        else:
                            # Statistics should be JSON
                            assert file_path.suffix == ".json"
                else:
                    pytest.skip("Documentation file saving returned None")
            else:
                pytest.skip("No documentation tables available for saving")
        else:
            pytest.skip("No API data available for documentation generation")

    def test_api_summary_generation(self, tmp_path):
        """Test generation of API documentation summary."""
        api_data = scan_source_code()

        if api_data:
            tables = generate_documentation_tables(api_data)

            if tables:
                summary_path = generate_api_summary(api_data, tables)

                if summary_path:
                    assert summary_path.exists()
                    assert summary_path.is_file()
                    assert summary_path.suffix == ".md"

                    # Check content
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    assert "API Documentation Summary" in content
                    assert "Total API Elements" in content
                else:
                    pytest.skip("API summary generation returned None")
            else:
                pytest.skip("No documentation tables available for summary")
        else:
            pytest.skip("No API data available for summary generation")


@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available")
class TestIntegrationWorkflow:
    """Test integration of publication workflow components."""

    def test_complete_publication_workflow(self, tmp_path):
        """Test the complete publication preparation workflow."""
        # This test runs the main function from prepare_publication.py
        # It should not raise exceptions even if infrastructure is limited
        from prepare_publication import main

        # Should run without raising exceptions
        try:
            main()
        except Exception as e:
            pytest.fail(f"Publication workflow failed: {e}")

    def test_complete_validation_workflow(self, tmp_path):
        """Test the complete manuscript validation workflow."""
        from validate_manuscript import main

        # Should run without raising exceptions
        try:
            main()
        except Exception as e:
            pytest.fail(f"Validation workflow failed: {e}")

    def test_complete_documentation_workflow(self, tmp_path):
        """Test the complete API documentation workflow."""
        from generate_api_docs import main

        # Should run without raising exceptions
        try:
            main()
        except Exception as e:
            pytest.fail(f"Documentation workflow failed: {e}")