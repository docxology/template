"""Tests for infrastructure.literature.config module.

Tests pure logic configuration without network access.
"""
import os
import pytest
from pathlib import Path

from infrastructure.literature.core import LiteratureConfig


class TestLiteratureConfig:
    """Test LiteratureConfig class."""

    def test_config_initialization(self):
        """Test basic config initialization."""
        config = LiteratureConfig()
        assert config is not None
        assert hasattr(config, "download_dir")
        assert hasattr(config, "max_results")
        assert hasattr(config, "timeout")

    def test_config_defaults(self):
        """Test config default values."""
        config = LiteratureConfig()
        assert config.default_limit == 25  # Increased for better coverage
        assert config.max_results == 100
        assert config.timeout == 2
        assert config.arxiv_delay == 3.0
        assert config.semanticscholar_delay == 1.5
        assert config.retry_attempts == 3
        assert config.retry_delay == 5.0
        assert config.download_dir == "data/pdfs"
        assert config.bibtex_file == "data/references.bib"
        assert "arxiv" in config.sources
        assert "semanticscholar" in config.sources

    def test_config_custom_values(self, tmp_path):
        """Test config with custom values."""
        download_dir = str(tmp_path / "downloads")
        config = LiteratureConfig(download_dir=download_dir, max_results=50)
        assert config.download_dir == download_dir
        assert config.max_results == 50

    def test_config_bibtex_file(self, tmp_path):
        """Test config bibtex file setting."""
        bibtex = str(tmp_path / "refs.bib")
        config = LiteratureConfig(bibtex_file=bibtex)
        assert config.bibtex_file == bibtex

    def test_config_sources_list(self):
        """Test config sources are properly initialized."""
        config = LiteratureConfig()
        assert isinstance(config.sources, list)
        assert len(config.sources) > 0
        assert "arxiv" in config.sources
        assert "semanticscholar" in config.sources


class TestLiteratureConfigFromEnv:
    """Test LiteratureConfig.from_env() method."""

    def test_from_env_default_values(self, monkeypatch):
        """Test from_env with no environment variables set."""
        # Clear any existing literature env vars
        for key in list(os.environ.keys()):
            if key.startswith("LITERATURE_") or key == "SEMANTICSCHOLAR_API_KEY":
                monkeypatch.delenv(key, raising=False)
        
        config = LiteratureConfig.from_env()
        
        assert config.default_limit == 25  # Increased default
        assert config.max_results == 100
        assert config.arxiv_delay == 3.0
        assert config.semanticscholar_delay == 1.5
        assert config.retry_attempts == 3
        assert config.retry_delay == 5.0
        assert config.semanticscholar_api_key is None
        assert config.sources == ["arxiv", "semanticscholar", "biorxiv", "pubmed", 
                                  "europepmc", "crossref", "openalex", "dblp"]

    def test_from_env_custom_limit(self, monkeypatch):
        """Test from_env reads LITERATURE_DEFAULT_LIMIT."""
        monkeypatch.setenv("LITERATURE_DEFAULT_LIMIT", "25")
        
        config = LiteratureConfig.from_env()
        
        assert config.default_limit == 25

    def test_from_env_max_results(self, monkeypatch):
        """Test from_env reads LITERATURE_MAX_RESULTS."""
        monkeypatch.setenv("LITERATURE_MAX_RESULTS", "200")
        
        config = LiteratureConfig.from_env()
        
        assert config.max_results == 200

    def test_from_env_arxiv_delay(self, monkeypatch):
        """Test from_env reads LITERATURE_ARXIV_DELAY."""
        monkeypatch.setenv("LITERATURE_ARXIV_DELAY", "5.5")
        
        config = LiteratureConfig.from_env()
        
        assert config.arxiv_delay == 5.5

    def test_from_env_semanticscholar_delay(self, monkeypatch):
        """Test from_env reads LITERATURE_SEMANTICSCHOLAR_DELAY."""
        monkeypatch.setenv("LITERATURE_SEMANTICSCHOLAR_DELAY", "2.5")
        
        config = LiteratureConfig.from_env()
        
        assert config.semanticscholar_delay == 2.5

    def test_from_env_retry_attempts(self, monkeypatch):
        """Test from_env reads LITERATURE_RETRY_ATTEMPTS."""
        monkeypatch.setenv("LITERATURE_RETRY_ATTEMPTS", "5")
        
        config = LiteratureConfig.from_env()
        
        assert config.retry_attempts == 5

    def test_from_env_retry_delay(self, monkeypatch):
        """Test from_env reads LITERATURE_RETRY_DELAY."""
        monkeypatch.setenv("LITERATURE_RETRY_DELAY", "10.0")
        
        config = LiteratureConfig.from_env()
        
        assert config.retry_delay == 10.0

    def test_from_env_semanticscholar_api_key(self, monkeypatch):
        """Test from_env reads SEMANTICSCHOLAR_API_KEY."""
        monkeypatch.setenv("SEMANTICSCHOLAR_API_KEY", "my-api-key-123")
        
        config = LiteratureConfig.from_env()
        
        assert config.semanticscholar_api_key == "my-api-key-123"

    def test_from_env_download_dir(self, monkeypatch):
        """Test from_env reads LITERATURE_DOWNLOAD_DIR."""
        monkeypatch.setenv("LITERATURE_DOWNLOAD_DIR", "/custom/downloads")
        
        config = LiteratureConfig.from_env()
        
        assert config.download_dir == "/custom/downloads"

    def test_from_env_timeout(self, monkeypatch):
        """Test from_env reads LITERATURE_TIMEOUT."""
        monkeypatch.setenv("LITERATURE_TIMEOUT", "60")
        
        config = LiteratureConfig.from_env()
        
        assert config.timeout == 60

    def test_from_env_bibtex_file(self, monkeypatch):
        """Test from_env reads LITERATURE_BIBTEX_FILE."""
        monkeypatch.setenv("LITERATURE_BIBTEX_FILE", "/custom/refs.bib")
        
        config = LiteratureConfig.from_env()
        
        assert config.bibtex_file == "/custom/refs.bib"

    def test_from_env_sources_comma_separated(self, monkeypatch):
        """Test from_env parses LITERATURE_SOURCES as comma-separated."""
        monkeypatch.setenv("LITERATURE_SOURCES", "arxiv,semanticscholar,crossref")
        
        config = LiteratureConfig.from_env()
        
        assert config.sources == ["arxiv", "semanticscholar", "crossref"]

    def test_from_env_sources_with_whitespace(self, monkeypatch):
        """Test from_env strips whitespace from sources."""
        monkeypatch.setenv("LITERATURE_SOURCES", "arxiv , semanticscholar , pubmed")
        
        config = LiteratureConfig.from_env()
        
        assert config.sources == ["arxiv", "semanticscholar", "pubmed"]

    def test_from_env_user_agent(self, monkeypatch):
        """Test from_env reads LITERATURE_USER_AGENT."""
        monkeypatch.setenv("LITERATURE_USER_AGENT", "CustomBot/1.0")
        
        config = LiteratureConfig.from_env()
        
        assert config.user_agent == "CustomBot/1.0"

    def test_from_env_all_values(self, monkeypatch):
        """Test from_env with all environment variables set."""
        monkeypatch.setenv("LITERATURE_DEFAULT_LIMIT", "15")
        monkeypatch.setenv("LITERATURE_MAX_RESULTS", "150")
        monkeypatch.setenv("LITERATURE_USER_AGENT", "TestBot/2.0")
        monkeypatch.setenv("LITERATURE_ARXIV_DELAY", "2.0")
        monkeypatch.setenv("LITERATURE_SEMANTICSCHOLAR_DELAY", "3.0")
        monkeypatch.setenv("SEMANTICSCHOLAR_API_KEY", "test-key")
        monkeypatch.setenv("LITERATURE_RETRY_ATTEMPTS", "5")
        monkeypatch.setenv("LITERATURE_RETRY_DELAY", "10.0")
        monkeypatch.setenv("LITERATURE_DOWNLOAD_DIR", "/tmp/pdfs")
        monkeypatch.setenv("LITERATURE_TIMEOUT", "45")
        monkeypatch.setenv("LITERATURE_BIBTEX_FILE", "/tmp/refs.bib")
        monkeypatch.setenv("LITERATURE_SOURCES", "arxiv")
        
        config = LiteratureConfig.from_env()
        
        assert config.default_limit == 15
        assert config.max_results == 150
        assert config.user_agent == "TestBot/2.0"
        assert config.arxiv_delay == 2.0
        assert config.semanticscholar_delay == 3.0
        assert config.semanticscholar_api_key == "test-key"
        assert config.retry_attempts == 5
        assert config.retry_delay == 10.0
        assert config.download_dir == "/tmp/pdfs"
        assert config.timeout == 45
        assert config.bibtex_file == "/tmp/refs.bib"
        assert config.sources == ["arxiv"]


class TestLiteratureConfigUnpaywall:
    """Test Unpaywall and download retry configuration options."""

    def test_unpaywall_defaults(self):
        """Test Unpaywall config default values."""
        config = LiteratureConfig()
        assert config.use_unpaywall is True
        assert config.unpaywall_email == "research@4dresearch.com"

    def test_unpaywall_custom_values(self):
        """Test Unpaywall config with custom values."""
        config = LiteratureConfig(
            use_unpaywall=True,
            unpaywall_email="test@example.com"
        )
        assert config.use_unpaywall is True
        assert config.unpaywall_email == "test@example.com"

    def test_from_env_unpaywall_enabled(self, monkeypatch):
        """Test from_env reads LITERATURE_USE_UNPAYWALL."""
        monkeypatch.setenv("LITERATURE_USE_UNPAYWALL", "true")
        monkeypatch.setenv("UNPAYWALL_EMAIL", "user@university.edu")
        
        config = LiteratureConfig.from_env()
        
        assert config.use_unpaywall is True
        assert config.unpaywall_email == "user@university.edu"

    def test_from_env_unpaywall_disabled(self, monkeypatch):
        """Test from_env with LITERATURE_USE_UNPAYWALL=false."""
        monkeypatch.setenv("LITERATURE_USE_UNPAYWALL", "false")
        
        config = LiteratureConfig.from_env()
        
        assert config.use_unpaywall is False

    def test_from_env_unpaywall_yes(self, monkeypatch):
        """Test from_env accepts 'yes' for boolean."""
        monkeypatch.setenv("LITERATURE_USE_UNPAYWALL", "yes")
        
        config = LiteratureConfig.from_env()
        
        assert config.use_unpaywall is True

    def test_from_env_unpaywall_1(self, monkeypatch):
        """Test from_env accepts '1' for boolean."""
        monkeypatch.setenv("LITERATURE_USE_UNPAYWALL", "1")
        
        config = LiteratureConfig.from_env()
        
        assert config.use_unpaywall is True


class TestLiteratureConfigDownloadRetry:
    """Test download retry configuration options."""

    def test_download_retry_defaults(self):
        """Test download retry config default values."""
        config = LiteratureConfig()
        assert config.download_retry_attempts == 2
        assert config.download_retry_delay == 2.0
        assert config.use_browser_user_agent is True

    def test_download_retry_custom_values(self):
        """Test download retry config with custom values."""
        config = LiteratureConfig(
            download_retry_attempts=5,
            download_retry_delay=3.0,
            use_browser_user_agent=False
        )
        assert config.download_retry_attempts == 5
        assert config.download_retry_delay == 3.0
        assert config.use_browser_user_agent is False

    def test_from_env_download_retry_attempts(self, monkeypatch):
        """Test from_env reads LITERATURE_DOWNLOAD_RETRY_ATTEMPTS."""
        monkeypatch.setenv("LITERATURE_DOWNLOAD_RETRY_ATTEMPTS", "4")
        
        config = LiteratureConfig.from_env()
        
        assert config.download_retry_attempts == 4

    def test_from_env_download_retry_delay(self, monkeypatch):
        """Test from_env reads LITERATURE_DOWNLOAD_RETRY_DELAY."""
        monkeypatch.setenv("LITERATURE_DOWNLOAD_RETRY_DELAY", "5.5")
        
        config = LiteratureConfig.from_env()
        
        assert config.download_retry_delay == 5.5

    def test_from_env_browser_user_agent_false(self, monkeypatch):
        """Test from_env reads LITERATURE_USE_BROWSER_USER_AGENT."""
        monkeypatch.setenv("LITERATURE_USE_BROWSER_USER_AGENT", "false")
        
        config = LiteratureConfig.from_env()
        
        assert config.use_browser_user_agent is False

    def test_from_env_browser_user_agent_default_true(self, monkeypatch):
        """Test browser User-Agent defaults to true."""
        # Clear the env var to test default
        monkeypatch.delenv("LITERATURE_USE_BROWSER_USER_AGENT", raising=False)
        
        config = LiteratureConfig.from_env()
        
        assert config.use_browser_user_agent is True


class TestBrowserUserAgents:
    """Test browser User-Agent constants."""

    def test_browser_user_agents_exist(self):
        """Test BROWSER_USER_AGENTS is defined and non-empty."""
        from infrastructure.literature.core import BROWSER_USER_AGENTS
        
        assert BROWSER_USER_AGENTS is not None
        assert len(BROWSER_USER_AGENTS) > 0

    def test_browser_user_agents_are_strings(self):
        """Test all browser User-Agents are strings."""
        from infrastructure.literature.core import BROWSER_USER_AGENTS
        
        for ua in BROWSER_USER_AGENTS:
            assert isinstance(ua, str)
            assert len(ua) > 0
            # Should contain browser identifiers
            assert "Mozilla" in ua or "Safari" in ua or "Chrome" in ua

