"""Tests for infrastructure.llm.config module."""
import pytest
from pathlib import Path

from infrastructure.llm.core.config import LLMConfig


class TestLLMConfig:
    """Test LLMConfig class."""

    def test_config_initialization(self):
        """Test basic config initialization."""
        config = LLMConfig()
        assert config is not None
        assert config.base_url == "http://localhost:11434"
        assert config.default_model == "gemma3:4b"

    def test_config_defaults(self):
        """Test config default values."""
        config = LLMConfig()
        # Verify reasonable defaults
        assert config.base_url == "http://localhost:11434"
        assert config.default_model == "gemma3:4b"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.context_window == 131072  # 128K context window (supports gemma3:4b)

    def test_config_custom_values(self):
        """Test config with custom values."""
        config = LLMConfig(
            base_url="http://custom:11434",
            default_model="mistral",
            temperature=0.3,
            max_tokens=512
        )
        assert config.base_url == "http://custom:11434"
        assert config.default_model == "mistral"
        assert config.temperature == 0.3
        assert config.max_tokens == 512

    def test_config_fallback_models(self):
        """Test fallback models configuration."""
        config = LLMConfig()
        assert len(config.fallback_models) > 0
        assert isinstance(config.fallback_models, list)

    def test_config_system_prompt(self):
        """Test system prompt configuration."""
        config = LLMConfig()
        assert "research assistant" in config.system_prompt.lower()

    def test_config_temperature_range(self):
        """Test temperature parameter validation."""
        # Valid temperatures
        config_low = LLMConfig(temperature=0.0)
        assert config_low.temperature == 0.0
        
        config_high = LLMConfig(temperature=2.0)
        assert config_high.temperature == 2.0

    def test_config_context_window(self):
        """Test context window configuration."""
        config = LLMConfig(context_window=8192)
        assert config.context_window == 8192

    def test_config_timeout(self):
        """Test timeout configuration."""
        config = LLMConfig()
        assert config.timeout > 0
        
        config_custom = LLMConfig(timeout=30.0)
        assert config_custom.timeout == 30.0

    def test_config_from_env(self):
        """Test creating config from environment."""
        config = LLMConfig.from_env()
        assert config is not None
        assert isinstance(config, LLMConfig)

