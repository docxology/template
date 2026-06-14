"""Tests for infrastructure.core.credentials.CredentialManager.

Consolidated suite (merged from the former test_credentials.py +
test_credentials_module.py) covering initialization, YAML config loading,
environment-variable substitution, credential retrieval, and the per-service
helpers for Zenodo, GitHub, and arXiv.

No mocks: real temp files and real environment variables. ``monkeypatch`` is
used for env isolation so changes auto-revert; "missing credential" tests pass
an empty ``env_file`` so they never autoload the repository's real ``.env``.
"""

import os

from infrastructure.core.credentials import (
    CredentialManager,
    _load_dotenv_fallback,
    ensure_dotenv_loaded,
)


class TestCredentialManagerInit:
    """Initialization and YAML config loading."""

    def test_init_without_files(self):
        """Initialization without any files yields an empty config."""
        manager = CredentialManager()

        assert manager.config == {}

    def test_init_with_env_file(self, tmp_path):
        """Initialization with a populated .env file succeeds (config stays empty)."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY=test_value\nANOTHER_KEY=another_value\n")

        manager = CredentialManager(env_file=env_file)

        assert manager.config == {}

    def test_init_with_nonexistent_env_file(self, tmp_path):
        """A non-existent env file is handled gracefully."""
        fake_env = tmp_path / "nonexistent.env"
        manager = CredentialManager(env_file=fake_env)

        assert manager.config == {}

    def test_init_with_nonexistent_config_file(self, tmp_path):
        """A non-existent config file is handled gracefully."""
        fake_config = tmp_path / "nonexistent.yaml"
        manager = CredentialManager(config_file=fake_config)

        assert manager.config == {}

    def test_init_with_yaml_config(self, tmp_path):
        """A valid YAML config is loaded into ``config``."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
zenodo:
  token: test_token
github:
  token: gh_token
"""
        )
        manager = CredentialManager(config_file=config_file)

        assert manager.config["zenodo"]["token"] == "test_token"
        assert manager.config["github"]["token"] == "gh_token"

    def test_init_with_both_files(self, tmp_path):
        """Initialization with both .env and YAML config loads the config keys."""
        env_file = tmp_path / ".env"
        env_file.write_text("ENV_VAR=env_value\n")
        config_file = tmp_path / "config.yaml"
        config_file.write_text("key: value\n")

        manager = CredentialManager(env_file=env_file, config_file=config_file)

        assert manager.config["key"] == "value"

    def test_load_simple_yaml_config(self, tmp_path):
        """A flat YAML config loads each key verbatim."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("token: simple_token\nurl: https://example.com\n")

        manager = CredentialManager(config_file=config_file)

        assert manager.config["token"] == "simple_token"
        assert manager.config["url"] == "https://example.com"

    def test_load_nested_yaml_config(self, tmp_path):
        """A nested YAML config preserves structure."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
services:
  zenodo:
    token: zenodo_token
    base_url: https://zenodo.org
  github:
    token: github_token
"""
        )
        manager = CredentialManager(config_file=config_file)

        assert manager.config["services"]["zenodo"]["token"] == "zenodo_token"
        assert manager.config["services"]["github"]["token"] == "github_token"


class TestSubstituteEnvVars:
    """Environment-variable substitution within loaded config."""

    def test_substitute_simple_string(self, tmp_path, monkeypatch):
        """A ``${VAR}`` placeholder is replaced with the env value."""
        monkeypatch.setenv("TEST_VAR", "test_value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("token: ${TEST_VAR}")

        manager = CredentialManager(config_file=config_file)

        assert manager.config["token"] == "test_value"

    def test_substitute_nested_dict(self, tmp_path, monkeypatch):
        """Substitution descends into nested dictionaries."""
        monkeypatch.setenv("NESTED_VAR", "nested_value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
outer:
  inner:
    value: ${NESTED_VAR}
"""
        )
        manager = CredentialManager(config_file=config_file)

        assert manager.config["outer"]["inner"]["value"] == "nested_value"

    def test_substitute_in_list(self, tmp_path, monkeypatch):
        """Substitution descends into list values."""
        monkeypatch.setenv("LIST_VAR", "list_value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
items:
  - ${LIST_VAR}
  - static_value
"""
        )
        manager = CredentialManager(config_file=config_file)

        assert manager.config["items"][0] == "list_value"
        assert manager.config["items"][1] == "static_value"

    def test_missing_env_var_keeps_placeholder(self, tmp_path):
        """A missing env var leaves the original ``${VAR}`` placeholder intact."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("token: ${NONEXISTENT_VAR_12345}")

        manager = CredentialManager(config_file=config_file)

        assert manager.config["token"] == "${NONEXISTENT_VAR_12345}"

    def test_non_string_values_unchanged(self, tmp_path):
        """Non-string scalars pass through substitution unchanged."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
integer: 42
float: 3.14
boolean: true
null_value: null
"""
        )
        manager = CredentialManager(config_file=config_file)

        assert manager.config["integer"] == 42
        assert manager.config["float"] == 3.14
        assert manager.config["boolean"] is True
        assert manager.config["null_value"] is None


class TestGetCredential:
    """The ``_get_credential`` lookup (env first, then config)."""

    def test_get_from_environment(self, monkeypatch):
        """A credential is read from the environment when present."""
        monkeypatch.setenv("TEST_CRED", "env_value")

        manager = CredentialManager()
        value = manager._get_credential("TEST_CRED")

        assert value == "env_value"

    def test_get_from_config(self, tmp_path):
        """A dotted key resolves from config when not in the environment."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
test:
  credential: config_value
"""
        )
        manager = CredentialManager(config_file=config_file)
        value = manager._get_credential("test.credential")

        assert value == "config_value"

    def test_env_takes_precedence(self, tmp_path, monkeypatch):
        """An environment variable takes precedence over a config value."""
        monkeypatch.setenv("PRIORITY_TEST", "env_value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("priority_test: config_value")

        manager = CredentialManager(config_file=config_file)
        value = manager._get_credential("PRIORITY_TEST")

        assert value == "env_value"

    def test_get_nested_key(self, tmp_path):
        """A dotted key resolves into nested config structure."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
zenodo:
  token: nested_token
"""
        )
        manager = CredentialManager(config_file=config_file)

        assert manager._get_credential("zenodo.token") == "nested_token"

    def test_get_with_default(self):
        """A missing credential returns the supplied default."""
        manager = CredentialManager()
        value = manager._get_credential("NONEXISTENT_KEY", default="default_val")

        assert value == "default_val"

    def test_get_missing_returns_none(self):
        """A missing credential without a default returns None."""
        manager = CredentialManager()
        value = manager._get_credential("COMPLETELY_NONEXISTENT_KEY")

        assert value is None


class TestZenodoCredentials:
    """Zenodo credential helpers."""

    def test_get_zenodo_sandbox_credentials(self, monkeypatch):
        """Sandbox mode returns the sandbox token and base URL."""
        monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", "sandbox_token_123")

        manager = CredentialManager()
        creds = manager.get_zenodo_credentials(use_sandbox=True)

        assert creds["token"] == "sandbox_token_123"
        assert creds["use_sandbox"] is True
        assert "sandbox.zenodo.org" in creds["base_url"]

    def test_get_zenodo_prod_credentials(self, monkeypatch):
        """Production mode returns the prod token and non-sandbox URL."""
        monkeypatch.setenv("ZENODO_PROD_TOKEN", "prod_token_456")

        manager = CredentialManager()
        creds = manager.get_zenodo_credentials(use_sandbox=False)

        assert creds["token"] == "prod_token_456"
        assert creds["use_sandbox"] is False
        assert "sandbox" not in creds["base_url"]

    def test_get_zenodo_credentials_missing(self, tmp_path, monkeypatch):
        """With no token set, Zenodo creds default to no token / sandbox mode."""
        monkeypatch.delenv("ZENODO_SANDBOX_TOKEN", raising=False)
        monkeypatch.delenv("ZENODO_PROD_TOKEN", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("")

        manager = CredentialManager(env_file=env_file)
        creds = manager.get_zenodo_credentials()

        assert creds["token"] is None
        assert creds["use_sandbox"] is True

    def test_has_zenodo_credentials_true(self, monkeypatch):
        """``has_zenodo_credentials`` is True when a token exists."""
        monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", "some_token")

        manager = CredentialManager()

        assert manager.has_zenodo_credentials(use_sandbox=True) is True

    def test_has_zenodo_credentials_false(self):
        """``has_zenodo_credentials`` is False when no token exists."""
        os.environ.pop("ZENODO_SANDBOX_TOKEN", None)

        manager = CredentialManager()

        assert manager.has_zenodo_credentials(use_sandbox=True) is False


class TestGitHubCredentials:
    """GitHub credential helpers."""

    def test_get_github_credentials(self, monkeypatch):
        """Both token and repo are returned alongside the API URL."""
        monkeypatch.setenv("GITHUB_TOKEN", "gh_token_789")
        monkeypatch.setenv("GITHUB_REPO", "user/repo")

        manager = CredentialManager()
        creds = manager.get_github_credentials()

        assert creds["token"] == "gh_token_789"
        assert creds["repository"] == "user/repo"
        assert creds["api_url"] == "https://api.github.com"

    def test_get_github_credentials_missing(self, tmp_path, monkeypatch):
        """With nothing set, token and repository come back None.

        An empty ``env_file`` skips the repo ``.env`` autoload and ``delenv``
        clears any inherited values (real isolation, no mocks).
        """
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_REPO", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("")

        manager = CredentialManager(env_file=env_file)
        creds = manager.get_github_credentials()

        assert creds["token"] is None
        assert creds["repository"] is None

    def test_has_github_credentials_true(self, monkeypatch):
        """True only when both token and repo are present."""
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        monkeypatch.setenv("GITHUB_REPO", "repo")

        manager = CredentialManager()

        assert manager.has_github_credentials() is True

    def test_has_github_credentials_false_no_token(self, tmp_path, monkeypatch):
        """False when the token is missing even if the repo is set."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_REPO", "repo")
        env_file = tmp_path / ".env"
        env_file.write_text("")

        manager = CredentialManager(env_file=env_file)

        assert manager.has_github_credentials() is False

    def test_has_github_credentials_false_no_repo(self, tmp_path, monkeypatch):
        """False when the repo is missing even if the token is set."""
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        monkeypatch.delenv("GITHUB_REPO", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("")

        manager = CredentialManager(env_file=env_file)

        assert manager.has_github_credentials() is False


class TestArxivCredentials:
    """arXiv credential helpers."""

    def test_get_arxiv_credentials(self, monkeypatch):
        """Username and password are returned and ``enabled`` is True."""
        monkeypatch.setenv("ARXIV_USERNAME", "arxiv_user")
        monkeypatch.setenv("ARXIV_PASSWORD", "arxiv_pass")

        manager = CredentialManager()
        creds = manager.get_arxiv_credentials()

        assert creds["username"] == "arxiv_user"
        assert creds["password"] == "arxiv_pass"
        assert creds["enabled"] is True

    def test_get_arxiv_credentials_missing(self, tmp_path, monkeypatch):
        """With nothing set, arXiv creds are None and ``enabled`` is False."""
        monkeypatch.delenv("ARXIV_USERNAME", raising=False)
        monkeypatch.delenv("ARXIV_PASSWORD", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("")

        manager = CredentialManager(env_file=env_file)
        creds = manager.get_arxiv_credentials()

        assert creds["username"] is None
        assert creds["password"] is None
        assert creds["enabled"] is False

    def test_has_arxiv_credentials_true(self, monkeypatch):
        """True when a username is present."""
        monkeypatch.setenv("ARXIV_USERNAME", "user")

        manager = CredentialManager()

        assert manager.has_arxiv_credentials() is True

    def test_has_arxiv_credentials_false(self):
        """False when no username is present."""
        os.environ.pop("ARXIV_USERNAME", None)

        manager = CredentialManager()

        assert manager.has_arxiv_credentials() is False


class TestDotenvFallback:
    """Graceful behavior regardless of python-dotenv availability."""

    def test_init_without_dotenv(self):
        """Initialization succeeds whether or not dotenv is installed."""
        manager = CredentialManager()

        assert manager.config == {}


class TestCredentialManagerIntegration:
    """End-to-end credential-management workflows."""

    def test_full_workflow(self, tmp_path, monkeypatch):
        """Env tokens plus a YAML config drive the full helper surface."""
        monkeypatch.setenv("ZENODO_SANDBOX_TOKEN", "zenodo_test")
        monkeypatch.setenv("GITHUB_TOKEN", "github_test")
        monkeypatch.setenv("GITHUB_REPO", "test/repo")
        monkeypatch.delenv("ARXIV_USERNAME", raising=False)

        config_file = tmp_path / "credentials.yaml"
        config_file.write_text(
            """
settings:
  timeout: 30
  retry_count: 3
"""
        )

        manager = CredentialManager(config_file=config_file)

        assert manager.has_zenodo_credentials(use_sandbox=True)
        assert manager.has_github_credentials()
        assert not manager.has_arxiv_credentials()
        assert manager.config["settings"]["timeout"] == 30

    def test_env_file_loading(self, tmp_path):
        """Loading from a .env file initializes without error."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_FROM_ENV_FILE=env_file_value\n")

        manager = CredentialManager(env_file=env_file)

        assert manager.config == {}


class TestEnsureDotenvLoaded:
    """ensure_dotenv_loaded() / fallback parser used by CLI entrypoints.

    The fallback parser is exercised directly so the behaviour is verified
    regardless of whether the optional python-dotenv extra is installed.
    """

    def test_fallback_loads_token_into_environ(self, tmp_path, monkeypatch):
        """A KEY=VALUE token in .env becomes available via os.getenv."""
        env_file = tmp_path / ".env"
        env_file.write_text("ZENODO_PROD_TOKEN=tok_from_dotenv\n")
        monkeypatch.delenv("ZENODO_PROD_TOKEN", raising=False)

        _load_dotenv_fallback(env_file)

        assert os.getenv("ZENODO_PROD_TOKEN") == "tok_from_dotenv"

    def test_fallback_does_not_override_existing_env(self, tmp_path, monkeypatch):
        """An explicit export always wins over the .env value."""
        env_file = tmp_path / ".env"
        env_file.write_text("ZENODO_PROD_TOKEN=from_file\n")
        monkeypatch.setenv("ZENODO_PROD_TOKEN", "from_export")

        _load_dotenv_fallback(env_file)

        assert os.getenv("ZENODO_PROD_TOKEN") == "from_export"

    def test_fallback_handles_export_prefix_and_quotes(self, tmp_path, monkeypatch):
        """`export KEY="value"` lines parse to the unquoted value."""
        env_file = tmp_path / ".env"
        env_file.write_text('export GITHUB_TOKEN="ghp_quoted"\n# comment\nGITHUB_REPO=owner/repo\n')
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_REPO", raising=False)

        _load_dotenv_fallback(env_file)

        assert os.getenv("GITHUB_TOKEN") == "ghp_quoted"
        assert os.getenv("GITHUB_REPO") == "owner/repo"

    def test_fallback_ignores_blank_and_comment_lines(self, tmp_path, monkeypatch):
        """Blank lines, comments, and keyless lines are skipped without error."""
        env_file = tmp_path / ".env"
        env_file.write_text("\n# just a comment\nnot_a_pair_line\nOK_KEY=ok\n")
        monkeypatch.delenv("OK_KEY", raising=False)

        _load_dotenv_fallback(env_file)

        assert os.getenv("OK_KEY") == "ok"

    def test_ensure_dotenv_loaded_with_explicit_file(self, tmp_path, monkeypatch):
        """ensure_dotenv_loaded(env_file=...) loads the targeted file."""
        env_file = tmp_path / ".env"
        env_file.write_text("ENSURE_DOTENV_KEY=present\n")
        monkeypatch.delenv("ENSURE_DOTENV_KEY", raising=False)

        ensure_dotenv_loaded(env_file)

        assert os.getenv("ENSURE_DOTENV_KEY") == "present"

    def test_ensure_dotenv_loaded_missing_file_is_safe(self, tmp_path):
        """A non-existent explicit .env path is a graceful no-op."""
        ensure_dotenv_loaded(tmp_path / "does-not-exist.env")  # must not raise
