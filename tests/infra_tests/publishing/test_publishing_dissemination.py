"""Test suite for publishing module using real implementations.

This test suite provides comprehensive validation for academic publishing tools
including DOI validation, citation generation, and metadata handling.

Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure import publishing


class TestDissemination:
    """Test dissemination capabilities."""

    def test_publish_to_zenodo(self, tmp_path, zenodo_test_server):
        """Test the Zenodo client workflow against a real local HTTP server."""
        from infrastructure.publishing.api import ZenodoClient
        from infrastructure.publishing.api import ZenodoConfig

        # Create test PDF file
        file_path = tmp_path / "paper.pdf"
        file_path.write_text("%PDF-1.4\nTest PDF content for Zenodo upload test")

        client = ZenodoClient(ZenodoConfig(access_token="test-token", base_url=zenodo_test_server.url_for("")))

        # Test metadata
        metadata = {
            "title": "Test Publication for Automated Testing",
            "upload_type": "publication",
            "publication_type": "article",
            "description": "Hermetic Zenodo client workflow test.",
            "creators": [{"name": "Test Author"}],
        }

        deposition = client.create_deposition(metadata)
        assert deposition.deposition_id == "12345"

        client.upload_file(deposition.bucket_url, str(file_path))

        doi = client.publish(deposition.deposition_id)
        assert doi == "10.5281/zenodo.12345"

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
        (manuscript_dir / "main.tex").write_text(r"\documentclass{article}")
        (manuscript_dir / "ref.bib").touch()
        (manuscript_dir / "ignored.txt").touch()

        # A title-derived BBL is deliberately ignored; only a BBL matching the
        # selected TeX root is valid for arXiv processing.
        (pdf_dir / "Test_Paper.bbl").touch()

        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            keywords=["key"],
        )

        tar_path = publishing.prepare_arxiv_submission(output_dir, metadata)

        assert tar_path.exists()
        assert tar_path.name.endswith(".tar.gz")

    def test_create_github_release_alt(self, tmp_path, github_test_server):
        """Test GitHub release creation against a local pytest-httpserver.

        Uses the shared ``github_test_server`` fixture (no live GitHub API,
        no parallel-run tag collisions, no wall-clock-derived names).
        """
        # Deterministic, parallel-safe tag derived from the per-test tmp_path
        # (each test gets a unique tmp_path even under pytest-xdist).
        tag = f"test-alt-{tmp_path.name}"

        # Create test artifact
        asset = tmp_path / "asset.pdf"
        asset.write_text("%PDF-1.4\nTest asset for GitHub release")

        url = publishing.create_github_release(
            tag,
            "Test Release Alt",
            "Test Description",
            [asset],
            "fake-token",
            "testuser/testrepo",
            base_url=github_test_server.url_for("").rstrip("/"),
        )

        assert url is not None
        assert "github.com" in url
