"""Tests for infrastructure.llm.core.config."""

from __future__ import annotations

import pytest

from infrastructure.llm.core.config import (
    GenerationOptions,
    OllamaClientConfig,
    ResponseMode,
    get_max_input_length,
)


class TestGenerationOptions:
    def test_default_values(self):
        opts = GenerationOptions()
        assert opts.temperature is None
        assert opts.max_tokens is None
        assert opts.top_p is None
        assert opts.format_json is False

    def test_to_ollama_options_uses_config_defaults(self):
        config = OllamaClientConfig(temperature=0.5, max_tokens=1024, top_p=0.8, context_window=4096)
        result = GenerationOptions().to_ollama_options(config)
        assert result["temperature"] == 0.5
        assert result["num_predict"] == 1024
        assert result["top_p"] == 0.8
        assert result["num_ctx"] == 4096

    def test_to_ollama_options_overrides_config(self):
        config = OllamaClientConfig(temperature=0.5, max_tokens=1024)
        opts = GenerationOptions(temperature=0.1, max_tokens=256)
        result = opts.to_ollama_options(config)
        assert result["temperature"] == 0.1
        assert result["num_predict"] == 256

    @pytest.mark.parametrize(
        ("opts_kwargs", "config_kwargs", "expected_key", "expected_value", "absent"),
        [
            ({"top_k": 40}, {}, "top_k", 40, False),
            ({}, {}, "top_k", None, True),
            ({"seed": 42}, {}, "seed", 42, False),
            ({}, {"seed": 99}, "seed", 99, False),
            ({}, {}, "seed", None, True),
            ({"stop": ["###", "END"]}, {}, "stop", ["###", "END"], False),
            ({}, {}, "stop", None, True),
            ({"repeat_penalty": 1.2}, {}, "repeat_penalty", 1.2, False),
            ({"num_ctx": 2048}, {"context_window": 131072}, "num_ctx", 2048, False),
        ],
    )
    def test_to_ollama_options_optional_fields(
        self, opts_kwargs, config_kwargs, expected_key, expected_value, absent
    ):
        opts = GenerationOptions(**opts_kwargs)
        config = OllamaClientConfig(**config_kwargs)
        result = opts.to_ollama_options(config)
        if absent:
            assert expected_key not in result
        else:
            assert result[expected_key] == expected_value


class TestOllamaClientConfig:
    def test_config_initialization(self):
        config = OllamaClientConfig()
        assert config.base_url == "http://localhost:11434"
        assert config.default_model == "gemma3:4b"

    def test_config_defaults(self):
        config = OllamaClientConfig()
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.context_window == 131072

    def test_config_custom_values(self):
        config = OllamaClientConfig(
            base_url="http://custom:11434",
            default_model="mistral",
            temperature=0.3,
            max_tokens=512,
        )
        assert config.base_url == "http://custom:11434"
        assert config.default_model == "mistral"
        assert config.temperature == 0.3
        assert config.max_tokens == 512

    def test_config_fallback_models(self):
        config = OllamaClientConfig()
        assert len(config.fallback_models) > 0
        assert isinstance(config.fallback_models, list)

    def test_config_system_prompt(self):
        config = OllamaClientConfig()
        assert "research assistant" in config.system_prompt.lower()

    @pytest.mark.parametrize("temperature", [0.0, 2.0])
    def test_config_temperature_range(self, temperature):
        config = OllamaClientConfig(temperature=temperature)
        assert config.temperature == temperature

    def test_config_context_window(self):
        config = OllamaClientConfig(context_window=8192)
        assert config.context_window == 8192

    def test_config_timeout(self):
        config = OllamaClientConfig()
        assert config.timeout > 0
        assert OllamaClientConfig(timeout=30.0).timeout == 30.0

    def test_num_ctx_alias(self):
        config = OllamaClientConfig(num_ctx=8192)
        assert config.context_window == 8192

    def test_num_ctx_with_context_window_raises(self):
        with pytest.raises(ValueError, match="unknown keyword arguments"):
            OllamaClientConfig(num_ctx=8192, context_window=16384)

    def test_unknown_kwargs_raises(self):
        with pytest.raises(ValueError, match="unknown keyword arguments"):
            OllamaClientConfig(nonexistent_param=42)

    def test_default_factory_fields(self):
        c1 = OllamaClientConfig()
        c2 = OllamaClientConfig()
        assert c1.fallback_models == c2.fallback_models
        assert c1.fallback_models is not c2.fallback_models

    def test_config_from_env(self):
        config = OllamaClientConfig.from_env()
        assert isinstance(config, OllamaClientConfig)

    @pytest.mark.parametrize(
        ("env", "attr", "expected"),
        [
            ({"OLLAMA_HOST": "http://remote:11434"}, "base_url", "http://remote:11434"),
            ({"OLLAMA_MODEL": "llama3"}, "default_model", "llama3"),
            ({"LLM_MAX_TOKENS": "4096"}, "max_tokens", 4096),
            ({"LLM_TEMPERATURE": "0.3"}, "temperature", 0.3),
            ({"LLM_NUM_CTX": "65536"}, "context_window", 65536),
            ({"LLM_REVIEW_TIMEOUT": "600.0"}, "review_timeout", 600.0),
            ({"LLM_SEED": "42"}, "seed", 42),
        ],
    )
    def test_from_env_mappings(self, monkeypatch, env, attr, expected):
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        config = OllamaClientConfig.from_env()
        assert getattr(config, attr) == expected

    def test_from_env_invalid_value_uses_default(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_TOKENS", "not_a_number")
        config = OllamaClientConfig.from_env()
        assert config.max_tokens == 2048

    def test_from_env_num_ctx_ignored_when_context_window_set(self, monkeypatch):
        monkeypatch.setenv("LLM_CONTEXT_WINDOW", "32768")
        monkeypatch.setenv("LLM_NUM_CTX", "65536")
        config = OllamaClientConfig.from_env()
        assert config.context_window == 32768

    def test_from_env_invalid_num_ctx_uses_default(self, monkeypatch):
        monkeypatch.setenv("LLM_NUM_CTX", "bad")
        config = OllamaClientConfig.from_env()
        assert config.context_window == 131072

    def test_with_overrides_basic(self):
        config = OllamaClientConfig(temperature=0.7)
        new_config = config.with_overrides(temperature=0.3, default_model="mistral")
        assert new_config.temperature == 0.3
        assert new_config.default_model == "mistral"
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
        assert config.create_options().seed == 99


class TestModuleLevelAccessors:
    def test_get_max_input_length_default(self):
        assert get_max_input_length() == 500000

    def test_get_max_input_length_from_env(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_INPUT_LENGTH", "100000")
        assert get_max_input_length() == 100000


class TestResponseMode:
    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (ResponseMode.SHORT, "short"),
            (ResponseMode.LONG, "long"),
            (ResponseMode.STRUCTURED, "structured"),
            (ResponseMode.RAW, "raw"),
            (ResponseMode.STANDARD, "standard"),
        ],
    )
    def test_enum_values(self, member, value):
        assert member == value
        assert value == member
