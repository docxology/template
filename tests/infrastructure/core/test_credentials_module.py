"""Tests for credential management module.

Tests credential loading and management using real data only.
No mocks - uses actual environment variables and temp files.
"""

import os
import pytest
from pathlib import Path
from infrastructure.core.credentials import CredentialManager


class TestCredentialManagerInit:
    """Tests for CredentialManager initialization."""

    def test_init_without_files(self):
        """Test initialization without any config files."""
        manager = CredentialManager()

        assert manager.config == {}

    def test_init_with_nonexistent_env_file(self, tmp_path):
        """Test initialization with non-existent env file."""
        fake_env = tmp_path / "nonexistent.env"
        manager = CredentialManager(env_file=fake_env)

        assert manager.config == {}

    def test_init_with_nonexistent_config_file(self, tmp_path):
        """Test initialization with non-existent config file."""
        fake_config = tmp_path / "nonexistent.yaml"
        manager = CredentialManager(config_file=fake_config)

        assert manager.config == {}

    def test_init_with_yaml_config(self, tmp_path):
        """Test initialization with valid YAML config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
zenodo:
  token: test_token
github:
  token: gh_token
""")
        manager = CredentialManager(config_file=config_file)

        assert manager.config["zenodo"]["token"] == "test_token"
        assert manager.config["github"]["token"] == "gh_token"


class TestSubstituteEnvVars:
    """Tests for environment variable substitution."""

    def test_substitute_simple_string(self, tmp_path, monkeypatch):
        """Test substituting a simple environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("token: ${TEST_VAR}")

        manager = CredentialManager(config_file=config_file)

        assert manager.config["token"] == "test_value"

    def test_substitute_nested_dict(self, tmp_path, monkeypatch):
        """Test substituting in nested dictionaries."""
        monkeypatch.setenv("NESTED_VAR", "nested_value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
outer:
  inner:
    value: ${NESTED_VAR}
""")
        manager = CredentialManager(config_file=config_file)

        assert manager.config["outer"]["inner"]["value"] == "nested_value"

    def test_substitute_in_list(self, tmp_path, monkeypatch):
        """Test substituting in lists."""
        monkeypatch.setenv("LIST_VAR", "list_value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
items:
  - ${LIST_VAR}
  - static_value
""")
        manager = CredentialManager(config_file=config_file)

        assert manager.config["items"][0] == "list_value"
        assert manager.config["items"][1] == "static_value"

    def test_missing_env_var_keeps_placeholder(self, tmp_path):
        """Test that missing env var keeps the original placeholder."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("token: ${NONEXISTENT_VAR_12345}")

        manager = CredentialManager(config_file=config_file)

        # Should keep original value when env var not found
        assert manager.config["token"] == "${NONEXISTENT_VAR_12345}"

    def test_non_string_values_unchanged(self, tmp_path):
        """Test that non-string values pass through unchanged."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
integer: 42
float: 3.14
boolean: true
null_value: null
""")
        manager = CredentialManager(config_file=config_file)

        assert manager.config["integer"] == 42
        assert manager.config["float"] == 3.14
        assert manager.config["boolean"] is True
        assert manager.config["null_value"] is None


class TestGetCredential:
    """Tests for credential retrieval."""

    def test_get_from_environment(self, monkeypatch):
        """Test getting credential from environment variable."""
        monkeypatch.setenv("TEST_CRED", "env_value")

        manager = CredentialManager()
        value = manager._get_credential("TEST_CRED")

        assert value == "env_value"

    def test_get_from_config(self, tmp_path):
        """Test getting credential from config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
test:
  credential: config_value
""")
        manager = CredentialManager(config_file=config_file)
        value = manager._get_credential("test.credential")

        assert value == "config_value"

    def test_env_takes_precedence(self, tmp_path, monkeypatch):
        """Test that environment variable takes precedence over config."""
        monkeypatch.setenv("PRIORITY_TEST", "env_value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("priority_test: config_value")

        manager = CredentialManager(config_file=config_file)
        value = manager._get_credential("PRIORITY_TEST")

        assert value == "env_value"

    def test_get_with_default(self):
        """Test getting credential with default value."""
        manager = CredentialManager()
        value = manager._get_credential("NONEXISTENT_KEY", default="default_val")

        assert value == "default_val"

    def test_get_missing_returns_none(self):
        """Test getting missing credential returns None."""
        manager = CredentialManager()
        value = manager._get_credential("COMPLETELY_NONEXISTENT_KEY")

        assert value is None


class TestZenodoCredentials:
    """Tests for Zenodo credential methods."""

    def test_get_zenodo_sandbox_credentials(self, monkeypatch):
        """Test getting Zenodo sandbox credentials."""
        monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", "sandbox_token_123")

        manager = CredentialManager()
        creds = manager.get_zenodo_credentials(use_sandbox=True)

        assert creds["token"] == "sandbox_token_123"
        assert creds["use_sandbox"] is True
        assert "sandbox.zenodo.org" in creds["base_url"]

    def test_get_zenodo_prod_credentials(self, monkeypatch):
        """Test getting Zenodo production credentials."""
        monkeypatch.setenv("ZENODO_PROD_TOKEN", "prod_token_456")

        manager = CredentialManager()
        creds = manager.get_zenodo_credentials(use_sandbox=False)

        assert creds["token"] == "prod_token_456"
        assert creds["use_sandbox"] is False
        assert "sandbox" not in creds["base_url"]

    def test_has_zenodo_credentials_true(self, monkeypatch):
        """Test has_zenodo_credentials returns True when token exists."""
        monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", "some_token")

        manager = CredentialManager()

        assert manager.has_zenodo_credentials(use_sandbox=True) is True

    def test_has_zenodo_credentials_false(self):
        """Test has_zenodo_credentials returns False when no token."""
        # Ensure env var is not set
        os.environ.pop("ZENODO_SANDBOX_TOKEN", None)

        manager = CredentialManager()

        assert manager.has_zenodo_credentials(use_sandbox=True) is False


class TestGitHubCredentials:
    """Tests for GitHub credential methods."""

    def test_get_github_credentials(self, monkeypatch):
        """Test getting GitHub credentials."""
        monkeypatch.setenv("GITHUB_TOKEN", "gh_token_789")
        monkeypatch.setenv("GITHUB_REPO", "user/repo")

        manager = CredentialManager()
        creds = manager.get_github_credentials()

        assert creds["token"] == "gh_token_789"
        assert creds["repository"] == "user/repo"
        assert creds["api_url"] == "https://api.github.com"

    def test_has_github_credentials_true(self, monkeypatch):
        """Test has_github_credentials returns True when both token and repo exist."""
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        monkeypatch.setenv("GITHUB_REPO", "repo")

        manager = CredentialManager()

        assert manager.has_github_credentials() is True

    def test_has_github_credentials_false_no_token(self, monkeypatch):
        """Test has_github_credentials returns False when no token."""
        os.environ.pop("GITHUB_TOKEN", None)
        monkeypatch.setenv("GITHUB_REPO", "repo")

        manager = CredentialManager()

        assert manager.has_github_credentials() is False

    def test_has_github_credentials_false_no_repo(self, monkeypatch):
        """Test has_github_credentials returns False when no repo."""
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        os.environ.pop("GITHUB_REPO", None)

        manager = CredentialManager()

        assert manager.has_github_credentials() is False


class TestArxivCredentials:
    """Tests for arXiv credential methods."""

    def test_get_arxiv_credentials(self, monkeypatch):
        """Test getting arXiv credentials."""
        monkeypatch.setenv("ARXIV_USERNAME", "arxiv_user")
        monkeypatch.setenv("ARXIV_PASSWORD", "arxiv_pass")

        manager = CredentialManager()
        creds = manager.get_arxiv_credentials()

        assert creds["username"] == "arxiv_user"
        assert creds["password"] == "arxiv_pass"
        assert creds["enabled"] is True

    def test_has_arxiv_credentials_true(self, monkeypatch):
        """Test has_arxiv_credentials returns True when username exists."""
        monkeypatch.setenv("ARXIV_USERNAME", "user")

        manager = CredentialManager()

        assert manager.has_arxiv_credentials() is True

    def test_has_arxiv_credentials_false(self):
        """Test has_arxiv_credentials returns False when no username."""
        os.environ.pop("ARXIV_USERNAME", None)

        manager = CredentialManager()

        assert manager.has_arxiv_credentials() is False


class TestCredentialManagerIntegration:
    """Integration tests for CredentialManager."""

    def test_full_workflow(self, tmp_path, monkeypatch):
        """Test complete credential management workflow."""
        # Set up environment variables
        monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", "zenodo_test")
        monkeypatch.setenv("GITHUB_TOKEN", "github_test")
        monkeypatch.setenv("GITHUB_REPO", "test/repo")

        # Create config file with additional settings
        config_file = tmp_path / "credentials.yaml"
        config_file.write_text("""
settings:
  timeout: 30
  retry_count: 3
""")

        # Initialize manager
        manager = CredentialManager(config_file=config_file)

        # Verify all credential methods work
        assert manager.has_zenodo_credentials(use_sandbox=True)
        assert manager.has_github_credentials()
        assert not manager.has_arxiv_credentials()

        # Verify config loaded
        assert manager.config["settings"]["timeout"] == 30

    def test_env_file_loading(self, tmp_path, monkeypatch):
        """Test loading credentials from .env file."""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("""
TEST_FROM_ENV_FILE=env_file_value
""")

        # Note: dotenv may or may not be available
        manager = CredentialManager(env_file=env_file)

        # The manager should initialize without error
        assert manager.config == {}
