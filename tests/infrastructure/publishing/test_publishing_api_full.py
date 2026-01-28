"""Comprehensive tests for infrastructure/publishing/api.py.

Tests publishing API functionality comprehensively.
"""

from pathlib import Path

# No mock imports needed - using real HTTP server
import pytest

from infrastructure.publishing import api
from infrastructure.publishing.api import ZenodoClient, ZenodoConfig


class TestPublishingApiImport:
    """Test module import."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert api is not None

    def test_module_attributes(self):
        """Test module has expected attributes."""
        module_attrs = [a for a in dir(api) if not a.startswith("_")]
        assert len(module_attrs) > 0


class TestZenodoConfig:
    """Test ZenodoConfig dataclass."""

    def test_sandbox_url(self):
        """Test sandbox URL."""
        config = ZenodoConfig(access_token="test", sandbox=True)
        assert "sandbox" in config.api_base_url

    def test_production_url(self):
        """Test production URL."""
        config = ZenodoConfig(access_token="test", sandbox=False)
        assert "sandbox" not in config.api_base_url

    def test_access_token(self):
        """Test access token is stored."""
        config = ZenodoConfig(access_token="my_token")
        assert config.access_token == "my_token"


class TestZenodoClient:
    """Test ZenodoClient class."""

    def test_init(self):
        """Test client initialization."""
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)

        assert client.config == config
        assert "Bearer test" in client.headers["Authorization"]

    def test_create_deposition_success(self, zenodo_test_server, monkeypatch):
        """Test successful deposition creation."""
        config = ZenodoConfig(access_token="test")

        # Override the base_url property for testing
        monkeypatch.setattr(config, "base_url", zenodo_test_server.url_for(""))
        client = ZenodoClient(config)

        result = client.create_deposition({"title": "Test"})

        assert result == "12345"

    def test_create_deposition_failure(self):
        """Test deposition creation failure."""
        from infrastructure.core.exceptions import PublishingError

        # Use invalid URL to simulate network error
        config = ZenodoConfig(access_token="test", base_url="http://invalid-host:9999/")
        client = ZenodoClient(config)

        with pytest.raises(PublishingError):
            client.create_deposition({"title": "Test"})

    def test_upload_file_success(self, tmp_path, zenodo_test_server, monkeypatch):
        """Test successful file upload."""
        config = ZenodoConfig(access_token="test")

        # Override the base_url property for testing
        monkeypatch.setattr(config, "base_url", zenodo_test_server.url_for(""))
        client = ZenodoClient(config)

        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF content")

        # Should not raise
        client.upload_file("bucket123", str(test_file))

    def test_upload_file_not_found(self, tmp_path):
        """Test upload with missing file."""
        from infrastructure.core.exceptions import UploadError

        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)

        with pytest.raises(UploadError):
            client.upload_file("123", str(tmp_path / "missing.pdf"))

    def test_publish_success(self, zenodo_test_server):
        """Test successful publication."""
        config = ZenodoConfig(
            access_token="test", base_url=zenodo_test_server.url_for("")
        )
        client = ZenodoClient(config)

        # Use real HTTP request to test server
        result = client.publish("12345")

        assert result == "10.5281/zenodo.12345"

    def test_publish_failure(self):
        """Test publication failure."""
        from infrastructure.core.exceptions import PublishingError

        # Use invalid URL to simulate network error
        config = ZenodoConfig(access_token="test", base_url="http://invalid-host:9999/")
        client = ZenodoClient(config)

        with pytest.raises(PublishingError):
            client.publish("12345")


class TestPublishingApiIntegration:
    """Integration tests for publishing API."""

    def test_module_structure(self):
        """Test module has expected structure."""
        # Should have ZenodoClient
        assert hasattr(api, "ZenodoClient")
        assert hasattr(api, "ZenodoConfig")

    def test_full_workflow(self, tmp_path, zenodo_test_server):
        """Test complete publishing workflow."""
        config = ZenodoConfig(
            access_token="test", base_url=zenodo_test_server.url_for("")
        )
        client = ZenodoClient(config)

        # Create test file
        test_file = tmp_path / "paper.pdf"
        test_file.write_bytes(b"%PDF content")

        # Use real HTTP requests to test server
        dep_id = client.create_deposition({"title": "Test"})
        client.upload_file("bucket123", str(test_file))
        doi = client.publish(dep_id)

        assert dep_id == "12345"
        assert "10.5281" in doi
