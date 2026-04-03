"""Expanded tests for infrastructure/llm/core/config.py.

Covers: GenerationOptions.to_ollama_options, OllamaClientConfig.__init__ edge cases,
OllamaClientConfig.from_env with env vars, with_overrides, create_options,
module-level accessors.

No mocks used -- all tests use real config instances and monkeypatch for env vars.
"""

from __future__ import annotations

import pytest

from infrastructure.llm.core.config import (
    GenerationOptions,
    OllamaClientConfig,
    ResponseMode,
    get_max_input_length,
)


class TestGenerationOptions:
    """Test GenerationOptions dataclass and to_ollama_options."""

    def test_default_values(self):
        opts = GenerationOptions()
        assert opts.temperature is None
        assert opts.max_tokens is None
        assert opts.top_p is None
        assert opts.format_json is False

    def test_to_ollama_options_uses_config_defaults(self):
        """When GenerationOptions fields are None, config defaults are used."""
        config = OllamaClientConfig(temperature=0.5, max_tokens=1024, top_p=0.8, context_window=4096)
        opts = GenerationOptions()
        result = opts.to_ollama_options(config)

        assert result["temperature"] == 0.5
        assert result["num_predict"] == 1024
        assert result["top_p"] == 0.8
        assert result["num_ctx"] == 4096

    def test_to_ollama_options_overrides_config(self):
        """GenerationOptions values override config defaults."""
        config = OllamaClientConfig(temperature=0.5, max_tokens=1024)
        opts = GenerationOptions(temperature=0.1, max_tokens=256)
        result = opts.to_ollama_options(config)

        assert result["temperature"] == 0.1
        assert result["num_predict"] == 256

    def test_to_ollama_options_top_k(self):
        opts = GenerationOptions(top_k=40)
        config = OllamaClientConfig()
        result = opts.to_ollama_options(config)
        assert result["top_k"] == 40

    def test_to_ollama_options_no_top_k(self):
        opts = GenerationOptions()
        config = OllamaClientConfig()
        result = opts.to_ollama_options(config)
        assert "top_k" not in result

    def test_to_ollama_options_seed_from_opts(self):
        opts = GenerationOptions(seed=42)
        config = OllamaClientConfig()
        result = opts.to_ollama_options(config)
        assert result["seed"] == 42

    def test_to_ollama_options_seed_from_config(self):
        opts = GenerationOptions()
        config = OllamaClientConfig(seed=99)
        result = opts.to_ollama_options(config)
        assert result["seed"] == 99

    def test_to_ollama_options_no_seed(self):
        opts = GenerationOptions()
        config = OllamaClientConfig()
        result = opts.to_ollama_options(config)
        assert "seed" not in result

    def test_to_ollama_options_stop_sequences(self):
        opts = GenerationOptions(stop=["###", "END"])
        config = OllamaClientConfig()
        result = opts.to_ollama_options(config)
        assert result["stop"] == ["###", "END"]

    def test_to_ollama_options_no_stop(self):
        opts = GenerationOptions()
        config = OllamaClientConfig()
        result = opts.to_ollama_options(config)
        assert "stop" not in result

    def test_to_ollama_options_repeat_penalty(self):
        opts = GenerationOptions(repeat_penalty=1.2)
        config = OllamaClientConfig()
        result = opts.to_ollama_options(config)
        assert result["repeat_penalty"] == 1.2

    def test_to_ollama_options_num_ctx_override(self):
        opts = GenerationOptions(num_ctx=2048)
        config = OllamaClientConfig(context_window=131072)
        result = opts.to_ollama_options(config)
        assert result["num_ctx"] == 2048


class TestOllamaClientConfigInit:
    """Test OllamaClientConfig.__init__ edge cases."""

    def test_num_ctx_alias(self):
        """num_ctx kwarg should map to context_window."""
        config = OllamaClientConfig(num_ctx=8192)
        assert config.context_window == 8192

    def test_num_ctx_with_context_window_raises(self):
        """If both num_ctx and context_window given, num_ctx remains unknown and raises."""
        with pytest.raises(ValueError, match="unknown keyword arguments"):
            OllamaClientConfig(num_ctx=8192, context_window=16384)

    def test_unknown_kwargs_raises(self):
        with pytest.raises(ValueError, match="unknown keyword arguments"):
            OllamaClientConfig(nonexistent_param=42)

    def test_default_factory_fields(self):
        """fallback_models uses default_factory; verify it creates a fresh list."""
        c1 = OllamaClientConfig()
        c2 = OllamaClientConfig()
        assert c1.fallback_models == c2.fallback_models
        assert c1.fallback_models is not c2.fallback_models


class TestOllamaClientConfigFromEnv:
    """Test from_env with monkeypatched environment variables."""

    def test_from_env_ollama_host(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_HOST", "http://remote:11434")
        config = OllamaClientConfig.from_env()
        assert config.base_url == "http://remote:11434"

    def test_from_env_ollama_model(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_MODEL", "llama3")
        config = OllamaClientConfig.from_env()
        assert config.default_model == "llama3"

    def test_from_env_int_mapping(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_TOKENS", "4096")
        config = OllamaClientConfig.from_env()
        assert config.max_tokens == 4096

    def test_from_env_float_mapping(self, monkeypatch):
        monkeypatch.setenv("LLM_TEMPERATURE", "0.3")
        config = OllamaClientConfig.from_env()
        assert config.temperature == 0.3

    def test_from_env_invalid_value_uses_default(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_TOKENS", "not_a_number")
        config = OllamaClientConfig.from_env()
        assert config.max_tokens == 2048  # default

    def test_from_env_num_ctx_alternative(self, monkeypatch):
        monkeypatch.setenv("LLM_NUM_CTX", "65536")
        config = OllamaClientConfig.from_env()
        assert config.context_window == 65536

    def test_from_env_num_ctx_ignored_when_context_window_set(self, monkeypatch):
        monkeypatch.setenv("LLM_CONTEXT_WINDOW", "32768")
        monkeypatch.setenv("LLM_NUM_CTX", "65536")
        config = OllamaClientConfig.from_env()
        assert config.context_window == 32768

    def test_from_env_invalid_num_ctx_uses_default(self, monkeypatch):
        monkeypatch.setenv("LLM_NUM_CTX", "bad")
        config = OllamaClientConfig.from_env()
        assert config.context_window == 131072  # default

    def test_from_env_review_timeout(self, monkeypatch):
        monkeypatch.setenv("LLM_REVIEW_TIMEOUT", "600.0")
        config = OllamaClientConfig.from_env()
        assert config.review_timeout == 600.0

    def test_from_env_seed(self, monkeypatch):
        monkeypatch.setenv("LLM_SEED", "42")
        config = OllamaClientConfig.from_env()
        assert config.seed == 42


class TestOllamaClientConfigMethods:
    """Test with_overrides and create_options."""

    def test_with_overrides_basic(self):
        config = OllamaClientConfig(temperature=0.7)
        new_config = config.with_overrides(temperature=0.3, default_model="mistral")
        assert new_config.temperature == 0.3
        assert new_config.default_model == "mistral"
        # Original unchanged
        assert config.temperature == 0.7

    def test_with_overrides_preserves_other_values(self):
        config = OllamaClientConfig(base_url="http://test:1234", max_tokens=512)
        new_config = config.with_overrides(temperature=0.1)
        assert new_config.base_url == "http://test:1234"
        assert new_config.max_tokens == 512
        assert new_config.temperature == 0.1

    def test_create_options_defaults(self):
        config = OllamaClientConfig(temperature=0.7, max_tokens=2048, top_p=0.9)
        opts = config.create_options()
        assert opts.temperature == 0.7
        assert opts.max_tokens == 2048
        assert opts.top_p == 0.9

    def test_create_options_with_overrides(self):
        config = OllamaClientConfig(temperature=0.7)
        opts = config.create_options(temperature=0.0, seed=42)
        assert opts.temperature == 0.0
        assert opts.seed == 42

    def test_create_options_inherits_seed(self):
        config = OllamaClientConfig(seed=99)
        opts = config.create_options()
        assert opts.seed == 99


class TestModuleLevelAccessors:
    """Test module-level config accessor functions."""

    def test_get_max_input_length_default(self):
        result = get_max_input_length()
        assert result == 500000

    def test_get_max_input_length_from_env(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_INPUT_LENGTH", "100000")
        result = get_max_input_length()
        assert result == 100000


class TestResponseMode:
    """Test ResponseMode enum."""

    def test_enum_values(self):
        assert ResponseMode.SHORT == "short"
        assert ResponseMode.LONG == "long"
        assert ResponseMode.STRUCTURED == "structured"
        assert ResponseMode.RAW == "raw"
        assert ResponseMode.STANDARD == "standard"

    def test_string_comparison(self):
        assert ResponseMode.SHORT == "short"
        assert "long" == ResponseMode.LONG
