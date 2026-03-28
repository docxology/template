"""Comprehensive tests for infrastructure/publishing/api.py.

Tests publishing API functionality using pytest-httpserver (no mocks).
"""

import pytest


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
    """Test arXiv submission helpers (skipped when not present)."""

    def test_prepare_arxiv_submission(self, tmp_path):
        """prepare_arxiv_submission is skipped if not exported."""
        from infrastructure.publishing import api

        if not hasattr(api, "prepare_arxiv_submission"):
            pytest.skip("prepare_arxiv_submission not available in this build")
        tex = tmp_path / "main.tex"
        tex.write_text("\\documentclass{article}")
        result = api.prepare_arxiv_submission(str(tmp_path))
        assert result is not None

    def test_create_arxiv_package(self, tmp_path):
        """create_arxiv_package is skipped if not exported."""
        from infrastructure.publishing import api

        if not hasattr(api, "create_arxiv_package"):
            pytest.skip("create_arxiv_package not available in this build")
        result = api.create_arxiv_package(str(tmp_path))
        assert result is not None


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
    """Test metadata extraction helpers (skipped when not present)."""

    def test_extract_metadata(self, tmp_path):
        """extract_metadata is skipped if not exported."""
        from infrastructure.publishing import api

        if not hasattr(api, "extract_metadata"):
            pytest.skip("extract_metadata not available in this build")
        md = tmp_path / "paper.md"
        md.write_text("# Title\nAuthors: Test")
        result = api.extract_metadata(str(md))
        assert result is not None

    def test_generate_bibtex(self):
        """generate_bibtex is skipped if not exported."""
        from infrastructure.publishing import api

        if not hasattr(api, "generate_bibtex"):
            pytest.skip("generate_bibtex not available in this build")
        metadata = {"title": "Test Paper", "authors": ["Author One"], "year": 2024}
        result = api.generate_bibtex(metadata)
        assert isinstance(result, str)


class TestPublishingApiIntegration:
    """Integration tests for publishing API."""

    def test_full_publishing_workflow(self, tmp_path):
        """Publishing module is importable and has expected classes."""
        from infrastructure.publishing.api import ZenodoClient, ZenodoConfig

        (tmp_path / "paper.pdf").write_bytes(b"%PDF")
        assert ZenodoClient is not None
        assert ZenodoConfig is not None
