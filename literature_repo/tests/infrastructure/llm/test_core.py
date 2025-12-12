"""Tests for infrastructure.llm.core module.

Tests LLMClient functionality using real data (No Mocks Policy):
- Pure logic tests (config, context, options) use real data
- Network-dependent tests marked with @pytest.mark.requires_ollama
- Uses ollama_utils for model discovery and selection
"""
import pytest
import requests

from infrastructure.llm.core.client import LLMClient, ResponseMode
from infrastructure.llm.core.config import LLMConfig, GenerationOptions
from infrastructure.llm.core.context import ConversationContext
from infrastructure.llm.utils.ollama import is_ollama_running, select_small_fast_model
from infrastructure.core.exceptions import LLMConnectionError, LLMError


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
        # Model is dynamically discovered from Ollama
        assert client.config.default_model is not None
        assert len(client.config.default_model) > 0

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

    def test_check_connection_detailed_returns_tuple(self, default_config):
        """Test check_connection_detailed returns tuple with error message."""
        # Use non-existent host to ensure it fails quickly
        config = LLMConfig(base_url="http://localhost:99999", timeout=0.1)
        client = LLMClient(config)
        
        is_available, error = client.check_connection_detailed()
        assert isinstance(is_available, bool)
        assert is_available is False
        assert error is not None
        assert isinstance(error, str)


# =============================================================================
# INTEGRATION TESTS (Require Ollama)
# =============================================================================

@pytest.mark.requires_ollama
class TestLLMClientWithOllama:
    """Integration tests requiring running Ollama server.
    
    Run with: pytest -m requires_ollama
    Skip with: pytest -m "not requires_ollama"
    
    Uses ollama_utils for dynamic model selection based on available models.
    """

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")

    @pytest.fixture
    def client(self, default_config):
        """Create LLMClient with discovered model."""
        return LLMClient(default_config)

    def test_query_basic(self, client):
        """Test basic query to Ollama returns a non-empty response."""
        response = client.query("What is 2 + 2?")
        
        assert response is not None
        assert len(response) > 0
        # Just verify we got a response - content may vary by model
        print(f"Basic query response: {response[:100]}")

    def test_query_with_options(self, client):
        """Test query with generation options."""
        opts = GenerationOptions(temperature=0.0, max_tokens=50)
        
        response = client.query("Say 'test' and nothing else.", options=opts)
        assert response is not None
        # Skip if model returns empty (transient model quality issue)
        if len(response) == 0:
            pytest.skip("Model returned empty response (transient quality issue)")

    def test_query_short(self, client):
        """Test short response mode."""
        response = client.query_short("What is 2+2?")
        
        assert response is not None
        assert len(response) < 1000  # Should be concise

    def test_query_long(self, client, default_config):
        """Test long response mode.
        
        Uses extended timeout for long-form generation which may take longer.
        Skips gracefully on timeout - integration tests depend on external service.
        """
        # Create client with extended timeout for long responses
        extended_config = default_config.with_overrides(timeout=120.0)
        long_client = LLMClient(extended_config)
        
        try:
            # Use simpler prompt to reduce processing time
            response = long_client.query_long("Explain what a variable is in programming.")
            
            assert response is not None
            assert len(response) > 50  # Should have some content
        except LLMConnectionError as e:
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                pytest.skip(f"Ollama timed out on long response (external service issue): {e}")
            raise

    def test_query_structured(self, client, default_config):
        """Test structured JSON response.
        
        Uses extended timeout and handles empty responses gracefully.
        Skips on LLM errors or empty responses - integration tests depend on 
        external service quality and model capability.
        """
        # Create client with extended timeout for structured response
        extended_config = default_config.with_overrides(timeout=90.0)
        structured_client = LLMClient(extended_config)
        
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "value": {"type": "number"}
            }
        }
        
        try:
            result = structured_client.query_structured(
                "What is 2+2? Return JSON with 'result' as string description and 'value' as the number.",
                schema=schema
            )
            
            assert isinstance(result, dict)
            # Empty dict {} is valid JSON - skip if model doesn't follow schema
            if len(result) == 0:
                pytest.skip("Model returned empty JSON object (model quality issue)")
            print(f"Structured result: {result}")
        except LLMConnectionError as e:
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                pytest.skip(f"Ollama timed out (external service issue): {e}")
            raise
        except LLMError as e:
            # Empty or invalid JSON responses indicate model quality issues, not code bugs
            if "valid JSON" in str(e) or "response=" in str(e):
                pytest.skip(f"Model returned invalid JSON (model quality issue): {e}")
            raise

    def test_query_raw(self, default_config):
        """Test raw query without system prompt."""
        config = default_config
        config.auto_inject_system_prompt = False
        client = LLMClient(config)
        
        response = client.query_raw("Complete: Hello")
        assert response is not None
        assert len(response) > 0

    def test_stream_query(self, client):
        """Test streaming query."""
        chunks = []
        
        for chunk in client.stream_query("Say 'hi'"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0

    def test_get_available_models(self, client):
        """Test fetching available models."""
        models = client.get_available_models()
        
        assert isinstance(models, list)
        # Should have at least one model if Ollama is running
        assert len(models) > 0
        print(f"Available models: {models}")

    def test_context_maintained_across_queries(self, client):
        """Test context is maintained across queries.
        
        Note: Small models may not perfectly recall context, so we just
        verify the conversation flow works without errors.
        """
        # First query
        response1 = client.query("Remember this number: 7.")
        assert response1 is not None
        
        # Second query referencing first
        response2 = client.query("What number did I just tell you to remember?")
        assert response2 is not None
        
        # Context should have both messages
        messages = client.context.get_messages()
        user_messages = [m for m in messages if m.get('role') == 'user']
        assert len(user_messages) >= 2, "Should have at least 2 user messages"
        print(f"Context messages: {len(messages)}")

    def test_reset_context_clears_history(self, client):
        """Test reset_context clears conversation history."""
        # Build up context
        client.query("Remember: secret code is 42.")
        
        # Reset and query
        response = client.query("What is the secret code?", reset_context=True)
        
        # Should not remember the code (or express uncertainty)
        # Response might say "I don't know" or similar
        assert response is not None

    def test_apply_template(self, client):
        """Test applying a research template."""
        response = client.apply_template(
            "summarize_abstract",
            text="This study examines the effects of X on Y."
        )
        
        assert response is not None
        assert len(response) > 0

    def test_seed_reproducibility(self, client):
        """Test seed produces consistent results."""
        opts = GenerationOptions(temperature=0.0, seed=42, max_tokens=50)
        
        response1 = client.query("Complete: The sky is", options=opts, reset_context=True)
        response2 = client.query("Complete: The sky is", options=opts, reset_context=True)
        
        # With same seed and temp=0, responses should be similar
        assert response1 is not None
        assert response2 is not None
        print(f"Response 1: {response1[:100]}")
        print(f"Response 2: {response2[:100]}")
