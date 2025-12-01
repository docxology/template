"""Tests for infrastructure.llm.config module.

Tests configuration loading, environment variable support,
and generation options using real data (No Mocks Policy).
"""
import os
import pytest

from infrastructure.llm.config import LLMConfig, GenerationOptions


class TestLLMConfig:
    """Test LLMConfig class with real data."""

    def test_config_initialization(self):
        """Test basic config initialization."""
        config = LLMConfig()
        assert config is not None
        assert config.base_url == "http://localhost:11434"
        assert config.default_model == "llama3"

    def test_config_defaults(self):
        """Test config default values."""
        config = LLMConfig()
        assert config.base_url == "http://localhost:11434"
        assert config.default_model == "llama3"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.context_window == 4096
        assert config.timeout == 60.0
        assert config.top_p == 0.9
        assert config.seed is None
        assert config.num_ctx is None

    def test_config_custom_values(self):
        """Test config with custom values."""
        config = LLMConfig(
            base_url="http://custom:11434",
            default_model="mistral",
            temperature=0.3,
            max_tokens=512,
            seed=42,
            num_ctx=8192,
        )
        assert config.base_url == "http://custom:11434"
        assert config.default_model == "mistral"
        assert config.temperature == 0.3
        assert config.max_tokens == 512
        assert config.seed == 42
        assert config.num_ctx == 8192

    def test_config_fallback_models(self):
        """Test fallback models configuration."""
        config = LLMConfig()
        assert len(config.fallback_models) > 0
        assert isinstance(config.fallback_models, list)
        assert "mistral" in config.fallback_models

    def test_config_system_prompt(self):
        """Test system prompt configuration."""
        config = LLMConfig()
        assert "research assistant" in config.system_prompt.lower()
        
        custom_config = LLMConfig(system_prompt="Custom prompt")
        assert custom_config.system_prompt == "Custom prompt"

    def test_config_temperature_range(self):
        """Test temperature parameter accepts valid range."""
        config_low = LLMConfig(temperature=0.0)
        assert config_low.temperature == 0.0
        
        config_mid = LLMConfig(temperature=1.0)
        assert config_mid.temperature == 1.0
        
        config_high = LLMConfig(temperature=2.0)
        assert config_high.temperature == 2.0

    def test_config_context_window(self):
        """Test context window configuration."""
        config = LLMConfig(context_window=8192)
        assert config.context_window == 8192

    def test_config_timeout(self):
        """Test timeout configuration."""
        config = LLMConfig()
        assert config.timeout == 60.0
        
        config_custom = LLMConfig(timeout=30.0)
        assert config_custom.timeout == 30.0

    def test_config_response_mode_defaults(self):
        """Test response mode default token limits."""
        config = LLMConfig()
        assert config.short_max_tokens == 200
        assert config.long_min_tokens == 500
        assert config.long_max_tokens == 4096

    def test_config_auto_inject_system_prompt(self):
        """Test auto_inject_system_prompt configuration."""
        config = LLMConfig()
        assert config.auto_inject_system_prompt is True
        
        config_disabled = LLMConfig(auto_inject_system_prompt=False)
        assert config_disabled.auto_inject_system_prompt is False


class TestLLMConfigFromEnv:
    """Test LLMConfig.from_env() with real environment variables."""

    def test_config_from_env_defaults(self, clean_llm_env):
        """Test from_env with no environment variables set."""
        config = LLMConfig.from_env()
        assert config is not None
        assert isinstance(config, LLMConfig)
        assert config.base_url == "http://localhost:11434"
        assert config.default_model == "llama3"
        assert config.temperature == 0.7

    def test_config_from_env_ollama_host(self, clean_llm_env):
        """Test OLLAMA_HOST environment variable."""
        os.environ["OLLAMA_HOST"] = "http://custom:8080"
        config = LLMConfig.from_env()
        assert config.base_url == "http://custom:8080"

    def test_config_from_env_ollama_model(self, clean_llm_env):
        """Test OLLAMA_MODEL environment variable."""
        os.environ["OLLAMA_MODEL"] = "mistral"
        config = LLMConfig.from_env()
        assert config.default_model == "mistral"

    def test_config_from_env_temperature(self, clean_llm_env):
        """Test LLM_TEMPERATURE environment variable."""
        os.environ["LLM_TEMPERATURE"] = "0.3"
        config = LLMConfig.from_env()
        assert config.temperature == 0.3

    def test_config_from_env_invalid_temperature(self, clean_llm_env):
        """Test invalid LLM_TEMPERATURE falls back to default."""
        os.environ["LLM_TEMPERATURE"] = "not_a_number"
        config = LLMConfig.from_env()
        assert config.temperature == 0.7  # Default

    def test_config_from_env_max_tokens(self, clean_llm_env):
        """Test LLM_MAX_TOKENS environment variable."""
        os.environ["LLM_MAX_TOKENS"] = "4096"
        config = LLMConfig.from_env()
        assert config.max_tokens == 4096

    def test_config_from_env_invalid_max_tokens(self, clean_llm_env):
        """Test invalid LLM_MAX_TOKENS falls back to default."""
        os.environ["LLM_MAX_TOKENS"] = "invalid"
        config = LLMConfig.from_env()
        assert config.max_tokens == 2048  # Default

    def test_config_from_env_seed(self, clean_llm_env):
        """Test LLM_SEED environment variable."""
        os.environ["LLM_SEED"] = "42"
        config = LLMConfig.from_env()
        assert config.seed == 42

    def test_config_from_env_num_ctx(self, clean_llm_env):
        """Test LLM_NUM_CTX environment variable."""
        os.environ["LLM_NUM_CTX"] = "8192"
        config = LLMConfig.from_env()
        assert config.num_ctx == 8192

    def test_config_from_env_context_window(self, clean_llm_env):
        """Test LLM_CONTEXT_WINDOW environment variable."""
        os.environ["LLM_CONTEXT_WINDOW"] = "16384"
        config = LLMConfig.from_env()
        assert config.context_window == 16384

    def test_config_from_env_timeout(self, clean_llm_env):
        """Test LLM_TIMEOUT environment variable."""
        os.environ["LLM_TIMEOUT"] = "120.0"
        config = LLMConfig.from_env()
        assert config.timeout == 120.0

    def test_config_from_env_system_prompt(self, clean_llm_env):
        """Test LLM_SYSTEM_PROMPT environment variable."""
        os.environ["LLM_SYSTEM_PROMPT"] = "Custom system prompt"
        config = LLMConfig.from_env()
        assert config.system_prompt == "Custom system prompt"

    def test_config_from_env_multiple_vars(self, clean_llm_env):
        """Test multiple environment variables together."""
        os.environ["OLLAMA_HOST"] = "http://test:11434"
        os.environ["OLLAMA_MODEL"] = "phi3"
        os.environ["LLM_TEMPERATURE"] = "0.5"
        os.environ["LLM_SEED"] = "123"
        
        config = LLMConfig.from_env()
        assert config.base_url == "http://test:11434"
        assert config.default_model == "phi3"
        assert config.temperature == 0.5
        assert config.seed == 123


class TestLLMConfigMethods:
    """Test LLMConfig methods."""

    def test_config_with_overrides(self):
        """Test creating config with overrides."""
        config = LLMConfig()
        new_config = config.with_overrides(
            temperature=0.0,
            timeout=30.0,
            seed=42
        )
        
        # New config has overrides
        assert new_config.temperature == 0.0
        assert new_config.timeout == 30.0
        assert new_config.seed == 42
        
        # Original unchanged
        assert config.temperature == 0.7
        assert config.timeout == 60.0
        assert config.seed is None

    def test_config_with_overrides_preserves_other_values(self):
        """Test with_overrides preserves non-overridden values."""
        config = LLMConfig(
            base_url="http://test:11434",
            default_model="mistral",
        )
        new_config = config.with_overrides(temperature=0.0)
        
        assert new_config.base_url == "http://test:11434"
        assert new_config.default_model == "mistral"
        assert new_config.temperature == 0.0

    def test_config_create_options(self):
        """Test creating GenerationOptions from config."""
        config = LLMConfig()
        opts = config.create_options(
            temperature=0.0,
            seed=42,
            stop=["END"]
        )
        
        assert isinstance(opts, GenerationOptions)
        assert opts.temperature == 0.0
        assert opts.seed == 42
        assert opts.stop == ["END"]

    def test_config_create_options_partial(self):
        """Test creating partial GenerationOptions."""
        config = LLMConfig()
        opts = config.create_options(temperature=0.5)
        
        assert opts.temperature == 0.5
        assert opts.seed is None
        assert opts.stop is None


class TestGenerationOptions:
    """Test GenerationOptions class with real data."""

    def test_options_default_initialization(self):
        """Test default options initialization."""
        opts = GenerationOptions()
        
        assert opts.temperature is None
        assert opts.max_tokens is None
        assert opts.top_p is None
        assert opts.top_k is None
        assert opts.seed is None
        assert opts.stop is None
        assert opts.format_json is False
        assert opts.repeat_penalty is None
        assert opts.num_ctx is None

    def test_options_custom_values(self):
        """Test options with custom values."""
        opts = GenerationOptions(
            temperature=0.0,
            max_tokens=1000,
            top_p=0.8,
            top_k=40,
            seed=42,
            stop=["END", "STOP"],
            format_json=True,
            repeat_penalty=1.2,
            num_ctx=8192,
        )
        
        assert opts.temperature == 0.0
        assert opts.max_tokens == 1000
        assert opts.top_p == 0.8
        assert opts.top_k == 40
        assert opts.seed == 42
        assert opts.stop == ["END", "STOP"]
        assert opts.format_json is True
        assert opts.repeat_penalty == 1.2
        assert opts.num_ctx == 8192

    def test_options_to_ollama_with_defaults(self):
        """Test converting options to Ollama format with config defaults."""
        config = LLMConfig(temperature=0.7, max_tokens=2048, top_p=0.9)
        opts = GenerationOptions()  # All None
        
        ollama_opts = opts.to_ollama_options(config)
        
        assert ollama_opts["temperature"] == 0.7
        assert ollama_opts["num_predict"] == 2048
        assert ollama_opts["top_p"] == 0.9

    def test_options_to_ollama_with_overrides(self):
        """Test converting options with overrides take precedence."""
        config = LLMConfig(temperature=0.7, max_tokens=2048, top_p=0.9)
        opts = GenerationOptions(
            temperature=0.0,
            max_tokens=500,
            seed=42,
            stop=["END"]
        )
        
        ollama_opts = opts.to_ollama_options(config)
        
        assert ollama_opts["temperature"] == 0.0
        assert ollama_opts["num_predict"] == 500
        assert ollama_opts["seed"] == 42
        assert ollama_opts["stop"] == ["END"]
        # top_p from config
        assert ollama_opts["top_p"] == 0.9

    def test_options_num_ctx_override(self):
        """Test num_ctx option overrides config."""
        config = LLMConfig(num_ctx=4096)
        opts = GenerationOptions(num_ctx=8192)
        
        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts["num_ctx"] == 8192

    def test_options_num_ctx_from_config(self):
        """Test num_ctx falls back to config when not specified."""
        config = LLMConfig(num_ctx=4096)
        opts = GenerationOptions()
        
        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts["num_ctx"] == 4096

    def test_options_repeat_penalty(self):
        """Test repeat_penalty option."""
        config = LLMConfig()
        opts = GenerationOptions(repeat_penalty=1.2)
        
        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts["repeat_penalty"] == 1.2

    def test_options_top_k(self):
        """Test top_k option."""
        config = LLMConfig()
        opts = GenerationOptions(top_k=40)
        
        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts["top_k"] == 40

    def test_options_top_p_override(self):
        """Test top_p option overrides config."""
        config = LLMConfig(top_p=0.9)
        opts = GenerationOptions(top_p=0.5)
        
        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts["top_p"] == 0.5

    def test_options_format_json_not_in_ollama_opts(self):
        """Test format_json flag doesn't appear in options dict."""
        config = LLMConfig()
        opts = GenerationOptions(format_json=True)
        
        ollama_opts = opts.to_ollama_options(config)
        # format_json is used separately for the format field
        assert "format_json" not in ollama_opts
        assert "format" not in ollama_opts

    def test_options_partial_overrides(self):
        """Test partial option overrides."""
        config = LLMConfig(temperature=0.7, max_tokens=2048)
        
        # Only override temperature
        opts = GenerationOptions(temperature=0.0)
        ollama_opts = opts.to_ollama_options(config)
        
        assert ollama_opts["temperature"] == 0.0
        assert ollama_opts["num_predict"] == 2048  # From config

    def test_options_empty_stop_not_included(self):
        """Test None stop sequences not included in output."""
        config = LLMConfig()
        opts = GenerationOptions(stop=None)
        
        ollama_opts = opts.to_ollama_options(config)
        assert "stop" not in ollama_opts

    def test_options_empty_list_stop(self):
        """Test empty list stop sequences."""
        config = LLMConfig()
        opts = GenerationOptions(stop=[])
        
        ollama_opts = opts.to_ollama_options(config)
        # Empty list is still included
        assert ollama_opts.get("stop") == []
