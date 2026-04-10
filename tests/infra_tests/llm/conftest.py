import threading

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig

from tests.infra_tests.llm.ollama_stub_server import build_chat_handler


@pytest.fixture
def ollama_test_server():
    """Local HTTP test server mimicking Ollama API endpoints (real HTTP, no mocks)."""
    server = HTTPServer()
    server.start()

    server.expect_request("/api/chat", method="POST").respond_with_handler(build_chat_handler())

    # Mock /api/tags endpoint (model list)
    server.expect_request("/api/tags").respond_with_json(
        {
            "models": [
                {"name": "gemma3:4b", "size": "4.7GB"},
                {"name": "llama3:8b", "size": "4.7GB"},
            ]
        }
    )

    try:
        yield server
    finally:
        # Under heavy load (e.g., coverage runs) server shutdown can occasionally
        # block long enough to trip the repo-wide pytest-timeout. Make teardown
        # best-effort and bounded.
        stopper = threading.Thread(target=server.stop, daemon=True)
        stopper.start()
        stopper.join(timeout=2.0)


@pytest.fixture
def test_config(ollama_test_server):
    """Create a real OllamaClientConfig pointing to test server."""
    config = OllamaClientConfig(auto_inject_system_prompt=False)
    config.base_url = ollama_test_server.url_for("/")
    config.default_model = "llama3:latest"
    config.fallback_models = ["llama3:8b"]
    return config


@pytest.fixture
def test_client(test_config):
    """Create a real LLMClient using test server."""
    return LLMClient(test_config)


@pytest.fixture
def default_config():
    """Create a default OllamaClientConfig for testing with auto_inject disabled."""
    return OllamaClientConfig(auto_inject_system_prompt=False)


@pytest.fixture
def config_with_system_prompt():
    """Create OllamaClientConfig with custom system prompt."""
    return OllamaClientConfig(
        system_prompt="You are a helpful research assistant.",
        auto_inject_system_prompt=True,
    )


@pytest.fixture
def generation_options():
    """Create GenerationOptions for testing."""
    from infrastructure.llm.core.config import GenerationOptions

    return GenerationOptions(temperature=0.5, max_tokens=500, seed=42, stop=["END"])


@pytest.fixture
def clean_llm_env(monkeypatch):
    """Clean LLM-related environment variables for testing."""
    # Remove LLM-related env vars
    env_vars_to_remove = ["OLLAMA_HOST", "OLLAMA_MODEL", "LLM_MAX_INPUT_LENGTH"]
    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)
    yield
    # Cleanup happens automatically


@pytest.fixture(autouse=True)
def patch_llm_client_for_tests(request, ollama_test_server, monkeypatch):
    """Redirect LLMClient to test server via environment variables.

    Sets OLLAMA_HOST to the test server URL so that OllamaClientConfig.from_env()
    naturally discovers the test server. No class patching required —
    fully compliant with the zero-mocks policy.

    Skips environment redirection if test is marked with 'no_patch_llm_client'
    to allow testing real default configuration.
    """
    # Check if test needs real default behavior
    if request.node.get_closest_marker("no_patch_llm_client"):
        return  # Skip — test will use real default config

    # Set environment variables so OllamaClientConfig.from_env() picks up test server
    monkeypatch.setenv("OLLAMA_HOST", ollama_test_server.url_for("/"))
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:4b")
    # Disable auto system prompt injection for predictable test behavior
    monkeypatch.setenv("LLM_AUTO_INJECT_SYSTEM_PROMPT", "false")
