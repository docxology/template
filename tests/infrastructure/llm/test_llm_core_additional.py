"""Additional tests for infrastructure/llm/core.py with real HTTP calls only.

This file contains only tests that use real HTTP calls via ollama_test_server fixture.
All mock-based tests have been removed to comply with No Mocks Policy.
"""

import pytest

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import LLMConfig
from infrastructure.core.exceptions import LLMConnectionError


class TestFallbackModel:
    """Test fallback model logic with real HTTP calls."""

    def test_fallback_on_connection_error(self, ollama_test_server):
        """Test fallback models on primary connection error."""
        # Configure test server to return failures for specific models
        config = LLMConfig(
            default_model="primary-model",
            fallback_models=["fallback1", "fallback2"],
            auto_inject_system_prompt=False
        )
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config)

        # Server returns 500 for "primary-model" and "fallback1", success for "fallback2"
        result = client.query("Test prompt")
        assert result == "Test response"  # Success from fallback2


class TestQueryStructuredJsonParsing:
    """Test query_structured JSON parsing with real HTTP calls."""

    def test_query_structured_valid_json(self, ollama_test_server):
        """Test query_structured with valid JSON response."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        config.default_model = "gemma3:4b"
        client = LLMClient(config=config)

        # Use real HTTP call to test server (returns JSON content for structured prompts)
        # Use native JSON mode (default) - should set format="json" in request
        result = client.query_structured("test structured prompt", use_native_json=True)

        assert result == {"key": "value", "number": 42}

    def test_query_structured_with_schema(self, ollama_test_server):
        """Test query_structured with schema."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }

        # The test server returns valid JSON when "test structured" is in the prompt
        result = client.query_structured("test structured prompt", schema=schema)

        # The test server returns {"key": "value", "number": 42}
        assert isinstance(result, dict)
        assert "key" in result


class TestStreamQuery:
    """Test streaming methods with real HTTP calls."""

    def test_stream_query_basic(self, ollama_test_server):
        """Test basic stream_query functionality."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        config.default_model = "gemma3:4b"
        client = LLMClient(config=config)

        # Use real streaming HTTP call to test server
        chunks = list(client.stream_query("Test prompt"))

        # Should get response chunks
        assert len(chunks) > 0
        assert "".join(chunks) == "Test response"

    def test_stream_query_adds_to_context(self, ollama_test_server):
        """Test stream_query adds full response to context."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Consume the iterator - test server returns streaming response
        list(client.stream_query("Test prompt"))

        # Check context
        messages = client.context.get_messages()
        assistant_messages = [m for m in messages if m.get('role') == 'assistant']

        assert len(assistant_messages) == 1
        assert assistant_messages[0]['content'] == "Test response"

    def test_stream_query_connection_error(self, ollama_test_server):
        """Test stream_query handles connection errors."""
        config = LLMConfig(auto_inject_system_prompt=False)
        # Point to a non-existent server to simulate connection error
        config.base_url = "http://nonexistent-server:9999"
        client = LLMClient(config=config)

        with pytest.raises(LLMConnectionError):
            list(client.stream_query("Test prompt"))


class TestGetAvailableModels:
    """Test get_available_models method with real HTTP calls."""

    def test_get_available_models_success(self, ollama_test_server):
        """Test successful model list retrieval."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Use real HTTP call to test server
        models = client.get_available_models()

        # Test server returns ["gemma3:4b", "llama3:8b"]
        assert "gemma3" in models
        assert "llama3" in models
        assert len(models) == 2  # Deduplicated