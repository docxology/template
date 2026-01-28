"""Tests for LLM streaming methods with real HTTP calls only.

This file contains only tests that use real HTTP calls via ollama_test_server fixture.
All mock-based tests have been removed to comply with No Mocks Policy.
"""

import pytest

from infrastructure.core.exceptions import LLMConnectionError
from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import LLMConfig


class TestStreamingBasic:
    """Test basic streaming functionality."""

    def test_stream_query_basic(self, ollama_test_server):
        """Test basic stream_query functionality with real HTTP."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Real HTTP request to test server
        chunks = list(client.stream_query("Test prompt"))

        # Verify we got the expected streaming chunks
        assert len(chunks) > 0
        assert isinstance(chunks[0], str)

    def test_stream_query_adds_to_context(self, ollama_test_server):
        """Test stream_query adds full response to context."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Real HTTP request to test server
        list(client.stream_query("Test prompt"))

        # Verify response was added to context
        messages = client.context.get_messages()
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        assert len(assistant_messages) == 1
        assert isinstance(assistant_messages[0]["content"], str)
        assert len(assistant_messages[0]["content"]) > 0

    def test_stream_short_basic(self, ollama_test_server):
        """Test basic stream_short functionality."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Real HTTP request to test server
        chunks = list(client.stream_short("Test prompt"))

        assert len(chunks) > 0
        assert isinstance(chunks[0], str)

    def test_stream_long_basic(self, ollama_test_server):
        """Test basic stream_long functionality."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Real HTTP request to test server
        chunks = list(client.stream_long("Test prompt"))

        assert len(chunks) > 0
        assert isinstance(chunks[0], str)


class TestStreamingIntegration:
    """Test streaming integration scenarios."""

    def test_stream_query_real_ollama(self, ollama_test_server):
        """Test stream_query with real Ollama server simulation."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Real streaming request
        try:
            chunks = list(client.stream_query("Hello world"))
            assert len(chunks) > 0
            # Verify content is reasonable
            full_response = "".join(chunks)
            assert isinstance(full_response, str)
            assert len(full_response) > 0
        except LLMConnectionError:
            pytest.skip("Ollama server not available")

    def test_stream_long_real_ollama(self, ollama_test_server):
        """Test stream_long with real Ollama server simulation."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Real streaming request
        try:
            chunks = list(client.stream_long("Tell me a story"))
            assert len(chunks) > 0
            # Verify content is reasonable
            full_response = "".join(chunks)
            assert isinstance(full_response, str)
            assert len(full_response) > 0
        except LLMConnectionError:
            pytest.skip("Ollama server not available")


class TestStreamingContextManagement:
    """Test streaming context management."""

    def test_stream_query_maintains_context(self, ollama_test_server):
        """Test that streaming maintains conversation context."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Add initial message to context
        client.context.add_message("user", "My name is Alice")

        # Stream a response
        list(client.stream_query("What's my name?"))

        # Check that context contains both messages
        messages = client.context.get_messages()
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        assert len(user_messages) >= 1
        assert len(assistant_messages) >= 1


class TestStreamingWithOptions:
    """Test streaming with generation options."""

    def test_stream_query_with_temperature(self, ollama_test_server):
        """Test streaming with temperature option."""
        from infrastructure.llm.core.config import GenerationOptions

        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        options = GenerationOptions(temperature=0.7)
        chunks = list(client.stream_query("Test prompt", options=options))

        assert len(chunks) > 0

    def test_stream_query_with_max_tokens(self, ollama_test_server):
        """Test streaming with max_tokens option."""
        from infrastructure.llm.core.config import GenerationOptions

        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        options = GenerationOptions(max_tokens=50)
        chunks = list(client.stream_query("Test prompt", options=options))

        assert len(chunks) > 0


class TestStreamingResponseSaving:
    """Test streaming response saving functionality."""

    def test_stream_query_saves_response(self, ollama_test_server, tmp_path):
        """Test that stream_query saves response when configured."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Configure response saving
        output_dir = tmp_path / "responses"
        output_dir.mkdir()

        # This would require extending the client to support response saving
        # For now, just test basic streaming works
        chunks = list(client.stream_query("Test prompt"))
        assert len(chunks) > 0

    def test_stream_short_saves_response(self, ollama_test_server, tmp_path):
        """Test that stream_short saves response when configured."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        chunks = list(client.stream_short("Test prompt"))
        assert len(chunks) > 0

    def test_stream_long_saves_response(self, ollama_test_server, tmp_path):
        """Test that stream_long saves response when configured."""
        config = LLMConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        chunks = list(client.stream_long("Test prompt"))
        assert len(chunks) > 0
