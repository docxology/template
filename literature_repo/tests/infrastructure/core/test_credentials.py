"""Tests for infrastructure.core.credentials module.

Comprehensive tests for CredentialManager including .env file loading,
YAML config loading, and credential retrieval from multiple sources.
"""

import os
import yaml
from pathlib import Path
import pytest
import tempfile

from infrastructure.core.credentials import CredentialManager


class TestCredentialManagerInitialization:
    """Test CredentialManager initialization."""

    def test_init_without_files(self):
        """Test initialization without any files."""
        manager = CredentialManager()
        
        assert manager.config == {}
        # Should not raise any errors

    def test_init_with_env_file(self, tmp_path):
        """Test initialization with .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY=test_value\nANOTHER_KEY=another_value\n")
        
        manager = CredentialManager(env_file=env_file)
        
        assert manager.config == {}
        # Environment variables should be loaded (if dotenv available)
        # We can't directly test this without checking os.getenv, but initialization should succeed

    def test_init_with_nonexistent_env_file(self, tmp_path):
        """Test initialization with non-existent .env file."""
        env_file = tmp_path / "nonexistent.env"
        
        manager = CredentialManager(env_file=env_file)
        
        assert manager.config == {}
        # Should handle gracefully

    def test_init_with_yaml_config(self, tmp_path):
        """Test initialization with YAML config file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "zenodo": {
                "token": "test_token",
                "sandbox": True
            },
            "github": {
                "token": "github_token",
                "repo": "user/repo"
            }
        }
        config_file.write_text(yaml.dump(config_data))
        
        manager = CredentialManager(config_file=config_file)
        
        assert "zenodo" in manager.config
        assert manager.config["zenodo"]["token"] == "test_token"
        assert "github" in manager.config

    def test_init_with_both_files(self, tmp_path):
        """Test initialization with both .env and YAML config."""
        env_file = tmp_path / ".env"
        env_file.write_text("ENV_VAR=env_value\n")
        
        config_file = tmp_path / "config.yaml"
        config_data = {"key": "value"}
        config_file.write_text(yaml.dump(config_data))
        
        manager = CredentialManager(env_file=env_file, config_file=config_file)
        
        assert "key" in manager.config
        assert manager.config["key"] == "value"


class TestYAMLConfigLoading:
    """Test YAML config loading and environment variable substitution."""

    def test_load_simple_yaml_config(self, tmp_path):
        """Test loading simple YAML config."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "token": "simple_token",
            "url": "https://example.com"
        }
        config_file.write_text(yaml.dump(config_data))
        
        manager = CredentialManager(config_file=config_file)
        
        assert manager.config["token"] == "simple_token"
        assert manager.config["url"] == "https://example.com"

    def test_load_nested_yaml_config(self, tmp_path):
        """Test loading nested YAML config."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "services": {
                "zenodo": {
                    "token": "zenodo_token",
                    "base_url": "https://zenodo.org"
                },
                "github": {
                    "token": "github_token"
                }
            }
        }
        config_file.write_text(yaml.dump(config_data))
        
        manager = CredentialManager(config_file=config_file)
        
        assert manager.config["services"]["zenodo"]["token"] == "zenodo_token"
        assert manager.config["services"]["github"]["token"] == "github_token"

    def test_env_var_substitution_in_yaml(self, tmp_path):
        """Test environment variable substitution in YAML."""
        # Set environment variable
        os.environ["TEST_TOKEN"] = "substituted_value"
        
        try:
            config_file = tmp_path / "config.yaml"
            config_data = {
                "token": "${TEST_TOKEN}",
                "other": "literal_value"
            }
            config_file.write_text(yaml.dump(config_data))
            
            manager = CredentialManager(config_file=config_file)
            
            assert manager.config["token"] == "substituted_value"
            assert manager.config["other"] == "literal_value"
        finally:
            # Clean up
            if "TEST_TOKEN" in os.environ:
                del os.environ["TEST_TOKEN"]

    def test_env_var_substitution_nested(self, tmp_path):
        """Test environment variable substitution in nested structures."""
        os.environ["ZENODO_TOKEN"] = "zenodo_env_token"
        
        try:
            config_file = tmp_path / "config.yaml"
            config_data = {
                "zenodo": {
                    "token": "${ZENODO_TOKEN}",
                    "url": "https://zenodo.org"
                }
            }
            config_file.write_text(yaml.dump(config_data))
            
            manager = CredentialManager(config_file=config_file)
            
            assert manager.config["zenodo"]["token"] == "zenodo_env_token"
            assert manager.config["zenodo"]["url"] == "https://zenodo.org"
        finally:
            if "ZENODO_TOKEN" in os.environ:
                del os.environ["ZENODO_TOKEN"]

    def test_env_var_substitution_in_list(self, tmp_path):
        """Test environment variable substitution in list values."""
        os.environ["ITEM1"] = "first"
        os.environ["ITEM2"] = "second"
        
        try:
            config_file = tmp_path / "config.yaml"
            config_data = {
                "items": ["${ITEM1}", "${ITEM2}", "literal"]
            }
            config_file.write_text(yaml.dump(config_data))
            
            manager = CredentialManager(config_file=config_file)
            
            assert manager.config["items"][0] == "first"
            assert manager.config["items"][1] == "second"
            assert manager.config["items"][2] == "literal"
        finally:
            if "ITEM1" in os.environ:
                del os.environ["ITEM1"]
            if "ITEM2" in os.environ:
                del os.environ["ITEM2"]

    def test_env_var_substitution_missing_var(self, tmp_path):
        """Test substitution when environment variable is missing."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "token": "${MISSING_VAR}"
        }
        config_file.write_text(yaml.dump(config_data))
        
        manager = CredentialManager(config_file=config_file)
        
        # Should return the original string if env var not found
        assert manager.config["token"] == "${MISSING_VAR}"


class TestCredentialRetrieval:
    """Test credential retrieval methods."""

    def test_get_credential_from_env(self):
        """Test getting credential from environment variable."""
        os.environ["TEST_CREDENTIAL"] = "env_value"
        
        try:
            manager = CredentialManager()
            value = manager._get_credential("TEST_CREDENTIAL")
            
            assert value == "env_value"
        finally:
            if "TEST_CREDENTIAL" in os.environ:
                del os.environ["TEST_CREDENTIAL"]

    def test_get_credential_from_config(self, tmp_path):
        """Test getting credential from config file."""
        config_file = tmp_path / "config.yaml"
        config_data = {"token": "config_value"}
        config_file.write_text(yaml.dump(config_data))
        
        manager = CredentialManager(config_file=config_file)
        value = manager._get_credential("token")
        
        assert value == "config_value"

    def test_get_credential_env_priority(self, tmp_path):
        """Test that environment variables take priority over config."""
        os.environ["PRIORITY_KEY"] = "env_value"
        
        try:
            config_file = tmp_path / "config.yaml"
            config_data = {"priority_key": "config_value"}
            config_file.write_text(yaml.dump(config_data))
            
            manager = CredentialManager(config_file=config_file)
            value = manager._get_credential("PRIORITY_KEY")
            
            # Environment should take priority
            assert value == "env_value"
        finally:
            if "PRIORITY_KEY" in os.environ:
                del os.environ["PRIORITY_KEY"]

    def test_get_credential_nested_key(self, tmp_path):
        """Test getting credential with nested key (e.g., 'zenodo.token')."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "zenodo": {
                "token": "nested_token"
            }
        }
        config_file.write_text(yaml.dump(config_data))
        
        manager = CredentialManager(config_file=config_file)
        value = manager._get_credential("zenodo.token")
        
        assert value == "nested_token"

    def test_get_credential_default_value(self):
        """Test getting credential with default value."""
        manager = CredentialManager()
        value = manager._get_credential("NONEXISTENT_KEY", default="default_value")
        
        assert value == "default_value"

    def test_get_credential_nonexistent(self):
        """Test getting non-existent credential."""
        manager = CredentialManager()
        value = manager._get_credential("NONEXISTENT_KEY")
        
        assert value is None


class TestZenodoCredentials:
    """Test Zenodo credential retrieval."""

    def test_get_zenodo_credentials_sandbox(self):
        """Test getting Zenodo sandbox credentials."""
        os.environ["ZENODO_SANDBOX_TOKEN"] = "sandbox_token"
        
        try:
            manager = CredentialManager()
            creds = manager.get_zenodo_credentials(use_sandbox=True)
            
            assert creds["token"] == "sandbox_token"
            assert creds["use_sandbox"] is True
            assert "sandbox.zenodo.org" in creds["base_url"]
        finally:
            if "ZENODO_SANDBOX_TOKEN" in os.environ:
                del os.environ["ZENODO_SANDBOX_TOKEN"]

    def test_get_zenodo_credentials_production(self):
        """Test getting Zenodo production credentials."""
        os.environ["ZENODO_PROD_TOKEN"] = "prod_token"
        
        try:
            manager = CredentialManager()
            creds = manager.get_zenodo_credentials(use_sandbox=False)
            
            assert creds["token"] == "prod_token"
            assert creds["use_sandbox"] is False
            assert "zenodo.org" in creds["base_url"]
            assert "sandbox" not in creds["base_url"]
        finally:
            if "ZENODO_PROD_TOKEN" in os.environ:
                del os.environ["ZENODO_PROD_TOKEN"]

    def test_get_zenodo_credentials_missing(self):
        """Test getting Zenodo credentials when not available."""
        manager = CredentialManager()
        creds = manager.get_zenodo_credentials()
        
        assert creds["token"] is None
        assert creds["use_sandbox"] is True

    def test_has_zenodo_credentials(self):
        """Test checking if Zenodo credentials are available."""
        manager = CredentialManager()
        
        # Without token
        assert manager.has_zenodo_credentials() is False
        
        # With token
        os.environ["ZENODO_SANDBOX_TOKEN"] = "test_token"
        try:
            assert manager.has_zenodo_credentials() is True
        finally:
            if "ZENODO_SANDBOX_TOKEN" in os.environ:
                del os.environ["ZENODO_SANDBOX_TOKEN"]


class TestGitHubCredentials:
    """Test GitHub credential retrieval."""

    def test_get_github_credentials(self):
        """Test getting GitHub credentials."""
        os.environ["GITHUB_TOKEN"] = "github_token"
        os.environ["GITHUB_REPO"] = "user/repo"
        
        try:
            manager = CredentialManager()
            creds = manager.get_github_credentials()
            
            assert creds["token"] == "github_token"
            assert creds["repository"] == "user/repo"
            assert creds["api_url"] == "https://api.github.com"
        finally:
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]
            if "GITHUB_REPO" in os.environ:
                del os.environ["GITHUB_REPO"]

    def test_get_github_credentials_missing(self):
        """Test getting GitHub credentials when not available."""
        manager = CredentialManager()
        creds = manager.get_github_credentials()
        
        assert creds["token"] is None
        assert creds["repository"] is None

    def test_has_github_credentials(self):
        """Test checking if GitHub credentials are available."""
        manager = CredentialManager()
        
        # Without credentials
        assert manager.has_github_credentials() is False
        
        # With partial credentials (missing repo)
        os.environ["GITHUB_TOKEN"] = "token"
        try:
            assert manager.has_github_credentials() is False
            
            # With both
            os.environ["GITHUB_REPO"] = "user/repo"
            assert manager.has_github_credentials() is True
        finally:
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]
            if "GITHUB_REPO" in os.environ:
                del os.environ["GITHUB_REPO"]


class TestArxivCredentials:
    """Test arXiv credential retrieval."""

    def test_get_arxiv_credentials(self):
        """Test getting arXiv credentials."""
        os.environ["ARXIV_USERNAME"] = "arxiv_user"
        os.environ["ARXIV_PASSWORD"] = "arxiv_pass"
        
        try:
            manager = CredentialManager()
            creds = manager.get_arxiv_credentials()
            
            assert creds["username"] == "arxiv_user"
            assert creds["password"] == "arxiv_pass"
            assert creds["enabled"] is True
        finally:
            if "ARXIV_USERNAME" in os.environ:
                del os.environ["ARXIV_USERNAME"]
            if "ARXIV_PASSWORD" in os.environ:
                del os.environ["ARXIV_PASSWORD"]

    def test_get_arxiv_credentials_missing(self):
        """Test getting arXiv credentials when not available."""
        manager = CredentialManager()
        creds = manager.get_arxiv_credentials()
        
        assert creds["username"] is None
        assert creds["password"] is None
        assert creds["enabled"] is False

    def test_has_arxiv_credentials(self):
        """Test checking if arXiv credentials are available."""
        manager = CredentialManager()
        
        # Without credentials
        assert manager.has_arxiv_credentials() is False
        
        # With credentials
        os.environ["ARXIV_USERNAME"] = "user"
        try:
            assert manager.has_arxiv_credentials() is True
        finally:
            if "ARXIV_USERNAME" in os.environ:
                del os.environ["ARXIV_USERNAME"]


class TestDotenvFallback:
    """Test graceful fallback when dotenv is not available."""

    def test_init_without_dotenv(self):
        """Test that initialization works even if dotenv is not available."""
        # This test verifies that the optional dependency handling works
        # The actual behavior depends on whether dotenv is installed
        manager = CredentialManager()
        
        # Should not raise any errors
        assert manager.config == {}

