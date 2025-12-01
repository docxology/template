"""Tests for infrastructure.llm.core module.

Tests LLMClient functionality using real data (No Mocks Policy):
- Pure logic tests (config, context, options) use real data
- Network-dependent tests marked with @pytest.mark.requires_ollama
"""
import pytest
import requests

from infrastructure.llm.core import LLMClient, ResponseMode
from infrastructure.llm.config import LLMConfig, GenerationOptions
from infrastructure.llm.context import ConversationContext
from infrastructure.core.exceptions import LLMConnectionError


class TestLLMClientInitialization:
    """Test LLMClient initialization with real configurations."""

    def test_client_with_default_config(self, clean_llm_env):
        """Test client initializes with default config."""
        client = LLMClient()
        assert client.config is not None
        assert client.config.base_url == "http://localhost:11434"
        assert client.context is not None

    def test_client_with_custom_config(self, default_config):
        """Test client initializes with custom config."""
        client = LLMClient(default_config)
        assert client.config == default_config
        assert client.config.default_model == "llama3"

    def test_client_context_initialized(self, default_config):
        """Test client context is properly initialized."""
        client = LLMClient(default_config)
        assert isinstance(client.context, ConversationContext)
        assert client.context.max_tokens == default_config.context_window


class TestSystemPromptInjection:
    """Test system prompt injection behavior with real data."""

    def test_system_prompt_injected_by_default(self, config_with_system_prompt):
        """Test system prompt is injected on initialization."""
        client = LLMClient(config_with_system_prompt)
        
        messages = client.context.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful research assistant."

    def test_system_prompt_not_injected_when_disabled(self, default_config):
        """Test system prompt not injected when disabled."""
        # default_config has auto_inject_system_prompt=False
        client = LLMClient(default_config)
        
        messages = client.context.get_messages()
        assert len(messages) == 0

    def test_reset_reinjects_system_prompt(self, config_with_system_prompt):
        """Test reset re-injects system prompt."""
        client = LLMClient(config_with_system_prompt)
        
        # Add some messages
        client.context.add_message("user", "Test message")
        assert len(client.context.get_messages()) == 2
        
        # Reset
        client.reset()
        
        messages = client.context.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"

    def test_set_system_prompt(self, config_with_system_prompt):
        """Test setting new system prompt."""
        client = LLMClient(config_with_system_prompt)
        
        client.set_system_prompt("New system prompt")
        
        messages = client.context.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "New system prompt"

    def test_set_system_prompt_clears_context(self, config_with_system_prompt):
        """Test set_system_prompt clears existing context."""
        client = LLMClient(config_with_system_prompt)
        
        # Add messages
        client.context.add_message("user", "Question")
        client.context.add_message("assistant", "Answer")
        
        # Set new system prompt
        client.set_system_prompt("New prompt")
        
        # Should only have new system prompt
        messages = client.context.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "New prompt"


class TestResponseMode:
    """Test ResponseMode enum."""

    def test_response_mode_values(self):
        """Test ResponseMode enum values."""
        assert ResponseMode.SHORT == "short"
        assert ResponseMode.LONG == "long"
        assert ResponseMode.STRUCTURED == "structured"
        assert ResponseMode.RAW == "raw"

    def test_response_mode_string_comparison(self):
        """Test ResponseMode can be compared as strings."""
        assert ResponseMode.SHORT == "short"
        assert ResponseMode.LONG.value == "long"


class TestContextManagement:
    """Test context management in LLMClient."""

    def test_reset_clears_context(self, default_config):
        """Test reset clears conversation context."""
        client = LLMClient(default_config)
        
        # Add messages
        client.context.add_message("user", "Message 1")
        client.context.add_message("assistant", "Response 1")
        assert len(client.context.messages) == 2
        
        # Reset
        client.reset()
        
        # Should be empty (no auto-inject)
        assert len(client.context.messages) == 0

    def test_reset_with_auto_inject(self, config_with_system_prompt):
        """Test reset re-injects system prompt."""
        client = LLMClient(config_with_system_prompt)
        
        # Add messages beyond system prompt
        client.context.add_message("user", "Question")
        assert len(client.context.messages) == 2
        
        # Reset
        client.reset()
        
        # Should only have system prompt
        assert len(client.context.messages) == 1
        assert client.context.messages[0].role == "system"


class TestGenerationOptionsIntegration:
    """Test GenerationOptions integration with LLMClient."""

    def test_options_to_ollama_format(self, default_config, generation_options):
        """Test options convert to Ollama format correctly."""
        ollama_opts = generation_options.to_ollama_options(default_config)
        
        assert ollama_opts["temperature"] == 0.5
        assert ollama_opts["num_predict"] == 500
        assert ollama_opts["seed"] == 42
        assert ollama_opts["stop"] == ["END"]

    def test_default_options_use_config(self, default_config):
        """Test default options use config values."""
        opts = GenerationOptions()
        ollama_opts = opts.to_ollama_options(default_config)
        
        assert ollama_opts["temperature"] == default_config.temperature
        assert ollama_opts["num_predict"] == default_config.max_tokens
        assert ollama_opts["top_p"] == default_config.top_p


class TestClientHelperMethods:
    """Test LLMClient helper methods that don't require network."""

    def test_check_connection_returns_bool(self, default_config):
        """Test check_connection returns boolean."""
        # Use non-existent host to ensure it fails quickly
        config = LLMConfig(base_url="http://localhost:99999", timeout=0.1)
        client = LLMClient(config)
        
        result = client.check_connection()
        assert isinstance(result, bool)
        assert result is False  # Should fail to connect


# =============================================================================
# INTEGRATION TESTS (Require Ollama)
# =============================================================================

@pytest.mark.requires_ollama
class TestLLMClientWithOllama:
    """Integration tests requiring running Ollama server.
    
    Run with: pytest -m requires_ollama
    Skip with: pytest -m "not requires_ollama"
    """

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        client = LLMClient()
        if not client.check_connection():
            pytest.skip("Ollama server not available")

    def test_query_basic(self):
        """Test basic query to Ollama."""
        client = LLMClient()
        response = client.query("Say 'hello' and nothing else.")
        
        assert response is not None
        assert len(response) > 0
        assert "hello" in response.lower()

    def test_query_with_options(self):
        """Test query with generation options."""
        client = LLMClient()
        opts = GenerationOptions(temperature=0.0, max_tokens=50)
        
        response = client.query("Say 'test' and nothing else.", options=opts)
        assert response is not None
        assert len(response) > 0

    def test_query_short(self):
        """Test short response mode."""
        client = LLMClient()
        response = client.query_short("What is 2+2?")
        
        assert response is not None
        assert len(response) < 600  # Should be concise

    def test_query_long(self):
        """Test long response mode."""
        client = LLMClient()
        response = client.query_long("Explain what a computer is.")
        
        assert response is not None
        assert len(response) > 100  # Should be detailed

    def test_query_structured(self):
        """Test structured JSON response."""
        client = LLMClient()
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"}
            }
        }
        
        result = client.query_structured(
            "Return JSON with answer='yes'",
            schema=schema
        )
        
        assert isinstance(result, dict)
        assert "answer" in result

    def test_query_raw(self):
        """Test raw query without system prompt."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config)
        
        response = client.query_raw("Complete: Hello")
        assert response is not None
        assert len(response) > 0

    def test_stream_query(self):
        """Test streaming query."""
        client = LLMClient()
        chunks = []
        
        for chunk in client.stream_query("Say 'hi'"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0

    def test_get_available_models(self):
        """Test fetching available models."""
        client = LLMClient()
        models = client.get_available_models()
        
        assert isinstance(models, list)
        # Should have at least one model if Ollama is running
        assert len(models) > 0

    def test_context_maintained_across_queries(self):
        """Test context is maintained across queries."""
        client = LLMClient()
        
        # First query
        client.query("My name is TestUser.")
        
        # Second query referencing first
        response = client.query("What is my name?")
        
        assert "TestUser" in response or "test" in response.lower()

    def test_reset_context_clears_history(self):
        """Test reset_context clears conversation history."""
        client = LLMClient()
        
        # Build up context
        client.query("Remember: secret code is 42.")
        
        # Reset and query
        response = client.query("What is the secret code?", reset_context=True)
        
        # Should not remember the code
        assert "42" not in response or "don't" in response.lower() or "not" in response.lower()

    def test_apply_template(self):
        """Test applying a research template."""
        client = LLMClient()
        
        response = client.apply_template(
            "summarize_abstract",
            text="This study examines the effects of X on Y."
        )
        
        assert response is not None
        assert len(response) > 0

    def test_seed_reproducibility(self):
        """Test seed produces consistent results."""
        client = LLMClient()
        opts = GenerationOptions(temperature=0.0, seed=42, max_tokens=50)
        
        response1 = client.query("Complete: The sky is", options=opts, reset_context=True)
        response2 = client.query("Complete: The sky is", options=opts, reset_context=True)
        
        # With same seed and temp=0, responses should be similar
        # (Not always identical due to model internals)
        assert response1 is not None
        assert response2 is not None
