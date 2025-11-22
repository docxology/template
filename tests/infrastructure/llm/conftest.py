import pytest
from unittest.mock import MagicMock
from infrastructure.llm.config import LLMConfig
from infrastructure.llm.core import LLMClient

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

