"""Test suite for publishing module using real implementations.

This test suite provides comprehensive validation for academic publishing tools
including DOI validation, citation generation, and metadata handling.

Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure import publishing


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
            keywords=["test", "research"],
        )

        package_info = publishing.create_publication_package(tmp_path, metadata)

        assert package_info["package_name"] != ""
        assert "files_included" in package_info
        assert "metadata" in package_info
        assert "package_hash" in package_info


class TestSubmissionChecklist:
    """Test submission checklist generation."""

    def test_create_submission_checklist(self):
        """Test creation of submission checklist."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="Test abstract",
            keywords=["test", "research"],
        )

        checklist = publishing.create_submission_checklist(metadata)

        assert metadata.title in checklist
        assert "Dr. Jane Smith" in checklist
        assert "PDF Format" in checklist
        assert "Abstract" in checklist
        assert "Keywords" in checklist


class TestPublicationSummary:
    """Test publication summary generation."""

    def test_generate_publication_summary(self):
        """Test generation of publication summary."""
        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Dr. Jane Smith"],
            abstract="This is a test abstract for the research paper.",
            keywords=["test", "research"],
            doi="10.5281/zenodo.12345678",
        )

        summary = publishing.generate_publication_summary(metadata)

        assert metadata.title in summary
        assert "Dr. Jane Smith" in summary
        assert metadata.abstract[:50] in summary  # First part of abstract
        assert metadata.doi in summary
