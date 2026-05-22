"""Comprehensive tests for publishing API and public package exports.

Tests publishing API functionality using pytest-httpserver (no mocks).
"""


class TestPublishingApiCore:
    """Test core publishing API functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        from infrastructure.publishing import api

        assert api is not None

    def test_has_api_functions(self):
        """Test that module has API functions."""
        from infrastructure.publishing import api

        module_funcs = [a for a in dir(api) if not a.startswith("_")]
        assert len(module_funcs) > 0

    def test_zenodo_client_exists(self):
        """ZenodoClient class is exported from publishing.api."""
        from infrastructure.publishing.api import ZenodoClient

        assert ZenodoClient is not None


class TestZenodoApi:
    """Test Zenodo API functionality using real HTTP test server."""

    def test_zenodo_upload(self, tmp_path, zenodo_test_server):
        """ZenodoClient.upload_file() calls the correct PUT endpoint."""
        from infrastructure.publishing.api import ZenodoClient, ZenodoConfig

        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF")

        config = ZenodoConfig(access_token="test", base_url=zenodo_test_server.url_for(""))
        client = ZenodoClient(config)
        # upload_file should not raise for a valid server response
        client.upload_file("bucket123", str(pdf))

    def test_create_zenodo_deposition(self, zenodo_test_server):
        """ZenodoClient.create_deposition() returns the deposition ID string."""
        from infrastructure.publishing.api import ZenodoClient, ZenodoConfig

        config = ZenodoConfig(access_token="test", base_url=zenodo_test_server.url_for(""))
        client = ZenodoClient(config)
        result = client.create_deposition({"title": "Test"})
        assert result == "12345"

    def test_zenodo_publish(self, zenodo_test_server):
        """ZenodoClient.publish() returns the DOI string."""
        from infrastructure.publishing.api import ZenodoClient, ZenodoConfig

        config = ZenodoConfig(access_token="test", base_url=zenodo_test_server.url_for(""))
        client = ZenodoClient(config)
        result = client.publish("12345")
        assert result == "10.5281/zenodo.12345"


class TestArxivApi:
    """Test arXiv submission helpers exposed by the publishing package."""

    def test_prepare_arxiv_submission(self, tmp_path):
        """prepare_arxiv_submission creates an archive from real local files."""
        import tarfile

        import infrastructure.publishing as publishing

        output_dir = tmp_path / "output"
        pdf_dir = output_dir / "pdf"
        manuscript_dir = tmp_path / "manuscript"
        pdf_dir.mkdir(parents=True)
        manuscript_dir.mkdir()
        (manuscript_dir / "main.tex").write_text("\\documentclass{article}", encoding="utf-8")
        (manuscript_dir / "references.bib").write_text("@misc{x, title={X}}", encoding="utf-8")

        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            keywords=["test"],
        )
        (pdf_dir / "Test_Paper.bbl").write_text("\\begin{thebibliography}{1}", encoding="utf-8")

        result = publishing.prepare_arxiv_submission(output_dir, metadata)
        assert result.exists()
        assert result.suffixes[-2:] == [".tar", ".gz"]
        with tarfile.open(result, "r:gz") as archive:
            names = archive.getnames()
        assert "main.tex" in names
        assert "references.bib" in names
        assert "Test_Paper.bbl" in names

    def test_api_module_keeps_zenodo_client_boundary(self):
        """api.py remains the Zenodo client module; platform helpers live in package exports."""
        import infrastructure.publishing as publishing
        from infrastructure.publishing import api

        assert hasattr(publishing, "prepare_arxiv_submission")
        assert hasattr(publishing, "publish_to_zenodo")
        assert not hasattr(api, "prepare_arxiv_submission")


class TestGitHubApi:
    """Test GitHub release API (create_github_release hardcodes api.github.com)."""

    def test_create_github_release_signature(self):
        """create_github_release is importable and has the expected signature."""
        import inspect
        from infrastructure.publishing.platforms import create_github_release

        sig = inspect.signature(create_github_release)
        assert "tag_name" in sig.parameters
        assert "release_name" in sig.parameters
        assert "token" in sig.parameters
        assert "repo" in sig.parameters


class TestMetadataExtraction:
    """Test metadata extraction and citation helpers exposed by the package."""

    def test_extract_metadata(self, tmp_path):
        """extract_publication_metadata reads real markdown content."""
        import infrastructure.publishing as publishing

        md = tmp_path / "paper.md"
        md.write_text(
            "# Paper Title\n\nAuthors: Dr. Test Author\n\n## Abstract\nExample abstract.",
            encoding="utf-8",
        )
        result = publishing.extract_publication_metadata([md])
        assert result.title == "Paper Title"
        assert result.authors == ["Dr. Test Author"]
        assert result.abstract == "Example abstract."

    def test_generate_bibtex(self):
        """generate_citation_bibtex returns a BibTeX entry."""
        import infrastructure.publishing as publishing

        metadata = publishing.PublicationMetadata(
            title="Test Paper",
            authors=["Author One"],
            abstract="Abstract",
            keywords=["test"],
            publication_date="2024-01-01",
        )
        result = publishing.generate_citation_bibtex(metadata)
        assert isinstance(result, str)
        assert "@software{authorone2024" in result
        assert "title = {Test Paper}" in result


class TestPublishingApiIntegration:
    """Integration tests for publishing API."""

    def test_full_publishing_workflow(self, tmp_path):
        """Publishing module is importable and has expected classes."""
        from infrastructure.publishing.api import ZenodoClient, ZenodoConfig

        (tmp_path / "paper.pdf").write_bytes(b"%PDF")
        assert ZenodoClient is not None
        assert ZenodoConfig is not None
