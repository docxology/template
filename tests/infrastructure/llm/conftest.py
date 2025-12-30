import pytest
import json
import os
from pytest_httpserver import HTTPServer
from infrastructure.llm.core.config import LLMConfig
from infrastructure.llm.core.client import LLMClient

@pytest.fixture
def ollama_test_server():
    """Local HTTP test server mimicking Ollama API endpoints."""
    server = HTTPServer()
    server.start()

    # Mock /api/chat endpoint (what the client actually uses)
    def handle_chat_request(request):
        """Handle chat requests, supporting both streaming and non-streaming."""
        import json

        # Parse the request JSON
        try:
            request_data = json.loads(request.body)
            is_stream = request_data.get("stream", False)
        except:
            is_stream = False

        if is_stream:
            # Return streaming response (SSE format)
            streaming_chunks = [
                {"model": "gemma3:4b", "created_at": "2024-01-01T00:00:00Z", "message": {"role": "assistant", "content": "Test"}, "done": False},
                {"model": "gemma3:4b", "created_at": "2024-01-01T00:00:01Z", "message": {"role": "assistant", "content": " response"}, "done": False},
                {"model": "gemma3:4b", "created_at": "2024-01-01T00:00:02Z", "message": {"role": "assistant", "content": ""}, "done": True}
            ]

            response_lines = []
            for chunk in streaming_chunks:
                response_lines.append(f"data: {json.dumps(chunk)}")
                response_lines.append("")  # Empty line between SSE events

            return "\n".join(response_lines)
        else:
            # Return regular response
            return json.dumps({
                "model": "gemma3:4b",
                "created_at": "2024-01-01T00:00:00Z",
                "message": {"role": "assistant", "content": "Test response"},
                "done": True
            })

    server.expect_request("/api/chat", method="POST").respond_with_handler(handle_chat_request)

    # Mock /api/tags endpoint (model list)
    server.expect_request("/api/tags").respond_with_json({
        "models": [
            {"name": "gemma3:4b", "size": "4.7GB"},
            {"name": "llama3:8b", "size": "4.7GB"}
        ]
    })

    yield server

    server.stop()

@pytest.fixture
def test_config(ollama_test_server):
    """Create a real LLMConfig pointing to test server."""
    config = LLMConfig(auto_inject_system_prompt=False)
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


@pytest.fixture(autouse=True)
def patch_llm_client_for_tests(request, ollama_test_server, monkeypatch):
    """Patch LLMClient to use test server by default when no config provided.

    Uses real HTTP server (pytest-httpserver) - compliant with no-mocks policy.
    Skips patching if test is marked with 'no_patch_llm_client' to allow
    testing real default configuration.
    """
    # Check if test needs real default behavior
    if request.node.get_closest_marker("no_patch_llm_client"):
        return  # Skip patching - test will use real default config

    from infrastructure.llm import LLMClient, LLMConfig

    original_init = LLMClient.__init__

    def patched_init(self, config=None):
        if config is None:
            # Create config pointing to real HTTP test server
            config = LLMConfig(auto_inject_system_prompt=False)
            config.base_url = ollama_test_server.url_for("/")
            config.default_model = "gemma3:4b"
            config.fallback_models = ["llama3:8b"]
        original_init(self, config)

    monkeypatch.setattr(LLMClient, "__init__", patched_init)
