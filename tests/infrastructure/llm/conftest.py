import pytest
import os
from unittest.mock import MagicMock, patch
from infrastructure.llm.core.config import LLMConfig
from infrastructure.llm.core.client import LLMClient

@pytest.fixture
def mock_config():
    config = LLMConfig()
    config.base_url = "http://mock-ollama"
    config.default_model = "test-model"
    config.fallback_models = ["fallback-model"]
    return config

@pytest.fixture
def mock_client(mock_config, mocker):
    mocker.patch("requests.post")
    return LLMClient(mock_config)

@pytest.fixture
def mock_requests_post(mocker):
    return mocker.patch("requests.post")

@pytest.fixture
def default_config():
    """Create a default LLMConfig for testing with auto_inject disabled."""
    return LLMConfig(auto_inject_system_prompt=False)

@pytest.fixture
def config_with_system_prompt():
    """Create LLMConfig with custom system prompt."""
    return LLMConfig(
        system_prompt="You are a helpful research assistant.",
        auto_inject_system_prompt=True
    )

@pytest.fixture
def generation_options():
    """Create GenerationOptions for testing."""
    from infrastructure.llm.core.config import GenerationOptions
    return GenerationOptions(
        temperature=0.5,
        max_tokens=500,
        seed=42,
        stop=["END"]
    )

@pytest.fixture
def clean_llm_env(monkeypatch):
    """Clean LLM-related environment variables for testing."""
    # Remove LLM-related env vars
    env_vars_to_remove = ['OLLAMA_HOST', 'OLLAMA_MODEL', 'LLM_MAX_INPUT_LENGTH']
    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)
    yield
    # Cleanup happens automatically

