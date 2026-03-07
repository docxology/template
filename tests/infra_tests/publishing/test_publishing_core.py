"""Tests for infrastructure/publishing/core.py.

Tests create_publication_package and related functions with real temp files.
No mocks — uses actual file I/O and real PublicationMetadata objects.
"""

from __future__ import annotations

from infrastructure.publishing.package import create_publication_package
from infrastructure.publishing.models import PublicationMetadata
from infrastructure.core.file_operations import calculate_file_hash

def make_metadata(**kwargs) -> PublicationMetadata:
    """Create a minimal PublicationMetadata for testing."""
    defaults = dict(
        title="Test Research Paper",
        authors=["Alice Smith", "Bob Jones"],
        abstract="This paper tests the publishing infrastructure.",
        keywords=["testing", "infrastructure"],
        doi="10.5281/zenodo.99999",
        license="CC-BY-4.0",
    )
    defaults.update(kwargs)
    return PublicationMetadata(**defaults)

class TestCalculateFileHash:
    """Test calculate_file_hash (re-exported from file_operations)."""

    def test_hash_consistent_for_same_content(self, tmp_path):
        """Same file content produces the same hash on repeated calls."""
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h1 = calculate_file_hash(f)
        h2 = calculate_file_hash(f)
        assert h1 == h2

    def test_hash_differs_for_different_content(self, tmp_path):
        """Different content produces different hashes."""
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content A")
        f2.write_text("content B")
        assert calculate_file_hash(f1) != calculate_file_hash(f2)

    def test_hash_is_hex_string(self, tmp_path):
        """Hash is a non-empty hex string."""
        f = tmp_path / "file.txt"
        f.write_text("some data")
        h = calculate_file_hash(f)
        assert isinstance(h, str)
        assert len(h) > 0
        # Should be hex characters
        int(h, 16)

    def test_empty_file_produces_hash(self, tmp_path):
        """Empty file still produces a valid hash."""
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        h = calculate_file_hash(f)
        assert isinstance(h, str)
        assert len(h) > 0

class TestCreatePublicationPackage:
    """Test create_publication_package with real temp directories."""

    def test_returns_dict(self, tmp_path):
        """create_publication_package returns a dict."""
        metadata = make_metadata()
        result = create_publication_package(tmp_path, metadata)
        assert isinstance(result, dict)

    def test_result_has_expected_keys(self, tmp_path):
        """Result dict has expected top-level keys."""
        metadata = make_metadata()
        result = create_publication_package(tmp_path, metadata)
        assert "package_name" in result
        assert "files_included" in result
        assert "metadata" in result
        assert "created_at" in result

    def test_package_name_derived_from_title(self, tmp_path):
        """package_name is derived from the title (lowercased, underscored)."""
        metadata = make_metadata(title="My Test Paper")
        result = create_publication_package(tmp_path, metadata)
        assert "my_test_paper" in result["package_name"].lower()

    def test_files_included_is_list(self, tmp_path):
        """files_included is a list."""
        metadata = make_metadata()
        result = create_publication_package(tmp_path, metadata)
        assert isinstance(result["files_included"], list)

    def test_metadata_preserved_in_result(self, tmp_path):
        """Metadata fields are preserved in result."""
        metadata = make_metadata(title="Preserved Title", doi="10.1234/test")
        result = create_publication_package(tmp_path, metadata)
        assert result["metadata"]["title"] == "Preserved Title"
        assert result["metadata"]["doi"] == "10.1234/test"

    def test_pdf_files_included_when_present(self, tmp_path):
        """PDF files in output/pdf/ are included in the package."""
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        # Create fake PDF files
        (pdf_dir / "manuscript.pdf").write_bytes(b"%PDF-1.4 fake content")
        (pdf_dir / "supplement.pdf").write_bytes(b"%PDF-1.4 supplement")

        metadata = make_metadata()
        result = create_publication_package(tmp_path, metadata)
        # Should detect PDFs in pdf/ directory
        assert len(result["files_included"]) >= 2

    def test_empty_output_dir_still_returns_package(self, tmp_path):
        """Empty output directory produces a valid (minimal) package."""
        metadata = make_metadata()
        result = create_publication_package(tmp_path, metadata)
        assert isinstance(result, dict)
        assert "package_name" in result

    def test_created_at_is_iso_format(self, tmp_path):
        """created_at is an ISO 8601 datetime string."""
        metadata = make_metadata()
        result = create_publication_package(tmp_path, metadata)
        from datetime import datetime
        # Should parse without error
        dt = datetime.fromisoformat(result["created_at"])
        assert dt.year >= 2024
