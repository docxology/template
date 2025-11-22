"""Tests for infrastructure.literature.config module."""
import pytest
from pathlib import Path

from infrastructure.literature.config import LiteratureConfig


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
        # Verify reasonable defaults
        assert config.max_results >= 10
        assert config.timeout >= 10
        assert isinstance(config.download_dir, str)
        assert isinstance(config.bibtex_file, str)

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
        assert "arxiv" in config.sources or "semanticscholar" in config.sources

