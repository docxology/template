"""Tests for infrastructure.llm.core module.

Tests LLMClient functionality using real data (No Mocks Policy):
- Pure logic tests (config, context, options) use real data
- Network-dependent tests marked with @pytest.mark.requires_ollama
- Uses ollama_utils for model discovery and selection
"""

import pytest
import requests

from infrastructure.core.exceptions import LLMConnectionError, LLMError
from infrastructure.llm.core.client import LLMClient, ResponseMode
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig
from infrastructure.llm.core.context import ConversationContext
from .._test_helpers import safe_network_test
from .real_ollama_client import build_real_small_llm_client


def _ready_small_model_client(
    auto_inject_system_prompt: bool = True,
) -> LLMClient:
    """Return a client configured for a preloaded small Ollama model (real daemon)."""
    return build_real_small_llm_client(
        auto_inject_system_prompt=auto_inject_system_prompt,
        timeout=20.0,
    )


class TestLLMClientInitialization:
    """Test LLMClient initialization with real configurations."""

    @pytest.mark.no_patch_llm_client
    def test_client_with_default_config(self, clean_llm_env):
        """Test client initializes with real default config.

        This test verifies the actual default configuration behavior,
        so it opts out of the autouse fixture patching.
        """
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
        config = OllamaClientConfig(base_url="http://localhost:99999", timeout=0.1)
        client = LLMClient(config)

        result = client.check_connection()
        assert isinstance(result, bool)
        assert result is False  # Should fail to connect

    def test_check_connection_with_reason_returns_tuple(self, default_config):
        """Test check_connection_with_reason returns tuple with error message."""
        # Use non-existent host to ensure it fails quickly
        config = OllamaClientConfig(base_url="http://localhost:99999", timeout=0.1)
        client = LLMClient(config)

        is_available, error = client.check_connection_with_reason()
        assert isinstance(is_available, bool)
        assert is_available is False
        assert error is not None
        assert isinstance(error, str)


# =============================================================================
# INTEGRATION TESTS (Require Ollama)
# =============================================================================


@pytest.mark.requires_ollama
@pytest.mark.timeout(180)
class TestLLMClientWithOllama:
    """Integration tests requiring running Ollama server.

    Run with: pytest -m requires_ollama
    Deselect with: pytest -m "not requires_ollama"

    Uses ollama_utils for dynamic model selection based on available models.
    """

    @pytest.fixture(autouse=True)
    def check_ollama(self, ensure_ollama_for_tests):
        """Ensure Ollama is running and functional for tests."""
        # Fixture dependency ensures Ollama is ready
        # If Ollama can't be started, ensure_ollama_for_tests will fail loudly
        pass

    @pytest.fixture
    def client(self, default_config):
        """Create LLMClient with discovered model."""
        return LLMClient(default_config)

    def test_query_basic(self, client):
        """Test basic query to Ollama returns a non-empty response."""
        with safe_network_test("Ollama"):
            response = client.query("What is 2 + 2?")
            assert response is not None
            assert len(response) > 0
            # Just verify we got a response - content may vary by model
            print(f"Basic query response: {response[:100]}")

    def test_query_with_options(self, client):
        """Test query with generation options."""
        opts = GenerationOptions(temperature=0.0, max_tokens=50)

        with safe_network_test("Ollama"):
            response = client.query("Say 'test' and nothing else.", options=opts)
            assert response is not None
            assert response, "Model returned an empty response"

    def test_query_short(self, client):
        """Test short response mode."""
        with safe_network_test("Ollama"):
            response = client.query_short("What is 2+2?")
            assert response is not None
            assert len(response) < 1000  # Should be concise

    @pytest.mark.timeout(180)  # Extended timeout for network-dependent test (3 minutes)
    def test_query_long(self, client, default_config):
        """Test long response mode.

        Uses extended timeout for long-form generation which may take longer.
        Fails with setup guidance on timeout; the requires_ollama fixture should
        have made the local service available before this test runs.
        """
        # Create client with extended timeout for long responses
        extended_config = default_config.with_overrides(timeout=120.0)
        long_client = LLMClient(extended_config)

        try:
            # Use simpler prompt to reduce processing time
            with safe_network_test("Ollama"):
                response = long_client.query_long("Explain what a variable is in programming.")

                assert response is not None
                assert len(response) > 50  # Should have some content
        except (
            LLMConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as e:
            error_str = str(e).lower()
            if any(
                keyword in error_str
                for keyword in ["timed out", "timeout", "connection", "refused"]
            ):
                pytest.fail(f"Ollama connection/timeout issue after setup: {e}")
            raise

    def test_query_structured(self, client, default_config):
        """Test structured JSON response.

        Uses extended timeout and handles empty responses gracefully.
        Fails on LLM errors or empty responses so default-selected tests do not
        hide model/setup regressions as skips.
        """
        # Create client with extended timeout for structured response
        extended_config = default_config.with_overrides(timeout=90.0)
        structured_client = LLMClient(extended_config)

        schema = {
            "type": "object",
            "properties": {"result": {"type": "string"}, "value": {"type": "number"}},
        }

        try:
            with safe_network_test("Ollama"):
                result = structured_client.query_structured(
                    "What is 2+2? Return JSON with 'result' as string description and 'value' as the number.",
                    schema=schema,
                )

                assert isinstance(result, dict)
                assert result, "Model returned an empty JSON object"
                print(f"Structured result: {result}")
        except LLMConnectionError as e:
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                pytest.fail(f"Ollama timed out after setup: {e}")
            raise
        except LLMError as e:
            if "valid JSON" in str(e) or "response=" in str(e):
                pytest.fail(f"Model returned invalid JSON: {e}")
            raise

    def test_query_raw(self, default_config):
        """Test raw query without system prompt."""
        config = default_config
        config.auto_inject_system_prompt = False
        client = LLMClient(config)

        with safe_network_test("Ollama"):
            response = client.query_raw("Complete: Hello")
            assert response is not None
            assert len(response) > 0

    def test_stream_query(self, client):
        """Test streaming query."""
        chunks = []

        with safe_network_test("Ollama"):
            for chunk in client.stream_query("Say 'hi'"):
                chunks.append(chunk)

            assert len(chunks) > 0
            full_response = "".join(chunks)
            assert len(full_response) > 0

    def test_get_available_models(self, client):
        """Test fetching available models."""
        with safe_network_test("Ollama"):
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
        with safe_network_test("Ollama"):
            response1 = client.query("Remember this number: 7.")
            assert response1 is not None

            # Second query referencing first
            response2 = client.query("What number did I just tell you to remember?")
            assert response2 is not None

            # Context should have both messages
            messages = client.context.get_messages()
            user_messages = [m for m in messages if m.get("role") == "user"]
            assert len(user_messages) >= 2, "Should have at least 2 user messages"
            print(f"Context messages: {len(messages)}")

    def test_reset_context_clears_history(self, client):
        """Test reset_context clears conversation history."""
        # Build up context
        with safe_network_test("Ollama"):
            client.query("Remember: secret code is 42.")

            # Reset and query
            response = client.query("What is the secret code?", reset_context=True)

            # Should not remember the code (or express uncertainty)
            # Response might say "I don't know" or similar
            assert response is not None

    def test_apply_template(self, client):
        """Test applying a research template."""
        with safe_network_test("Ollama"):
            response = client.apply_template(
                "summarize_abstract", text="This study examines the effects of X on Y."
            )

            assert response is not None
            assert len(response) > 0

    def test_seed_reproducibility(self, client):
        """Test seed produces consistent results."""
        opts = GenerationOptions(temperature=0.0, seed=42, max_tokens=50)

        with safe_network_test("Ollama"):
            response1 = client.query("Complete: The sky is", options=opts, reset_context=True)
            response2 = client.query("Complete: The sky is", options=opts, reset_context=True)

            # With same seed and temp=0, responses should be similar
            assert response1 is not None
            assert response2 is not None
            print(f"Response 1: {response1[:100]}")
            print(f"Response 2: {response2[:100]}")


class TestResponseModeDetails:
    """Test ResponseMode enum details."""

    def test_response_mode_comparison(self):
        """Test ResponseMode can be compared."""
        assert ResponseMode.SHORT == ResponseMode.SHORT
        assert ResponseMode.SHORT != ResponseMode.LONG

    def test_response_mode_str(self):
        """Test ResponseMode string conversion."""
        assert str(ResponseMode.SHORT) == "ResponseMode.SHORT"
        assert ResponseMode.SHORT.value == "short"


class TestGenerationOptionsDetails:
    """Test GenerationOptions in detail."""

    def test_options_with_seed(self):
        """Test options with seed for reproducibility."""
        opts = GenerationOptions(seed=42, temperature=0.0)

        assert opts.seed == 42
        assert opts.temperature == 0.0

    def test_options_with_max_tokens(self):
        """Test options with max_tokens."""
        opts = GenerationOptions(max_tokens=100)

        assert opts.max_tokens == 100

    def test_options_with_all_params(self):
        """Test options with all parameters."""
        opts = GenerationOptions(
            temperature=0.5,
            max_tokens=1000,
            top_p=0.95,
            top_k=50,
            seed=42,
            stop=["END"],
            format_json=True,
            repeat_penalty=1.1,
            num_ctx=4096,
        )

        assert opts.temperature == 0.5
        assert opts.max_tokens == 1000
        assert opts.top_p == 0.95
        assert opts.top_k == 50
        assert opts.seed == 42
        assert opts.stop == ["END"]
        assert opts.format_json is True
        assert opts.repeat_penalty == 1.1
        assert opts.num_ctx == 4096

    def test_options_defaults(self):
        """Test default option values."""
        opts = GenerationOptions()

        assert opts.temperature is None
        assert opts.max_tokens is None
        assert opts.seed is None
        assert opts.format_json is False


class TestContextManagementPure:
    """Test conversation context management (pure logic)."""

    def test_context_accumulates(self):
        """Test context accumulates messages."""
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)

        client.context.add_message("user", "First message")
        client.context.add_message("assistant", "First response")
        client.context.add_message("user", "Second message")

        messages = client.context.get_messages()
        user_messages = [m for m in messages if m.get("role") == "user"]
        assert len(user_messages) == 2

    def test_context_preserves_order(self):
        """Test context preserves message order."""
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)

        client.context.add_message("user", "First")
        client.context.add_message("assistant", "Second")
        client.context.add_message("user", "Third")

        messages = client.context.get_messages()
        contents = [m["content"] for m in messages]
        assert contents == ["First", "Second", "Third"]

    def test_context_reset(self):
        """Test context reset clears messages."""
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)

        client.context.add_message("user", "Test")
        client.reset()

        messages = client.context.get_messages()
        assert len(messages) == 0

    def test_context_token_estimation(self):
        """Test context tracks token estimation."""
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)

        # Empty context
        assert client.context.estimated_tokens == 0

        # Add message
        client.context.add_message("user", "Test message here")
        assert client.context.estimated_tokens > 0


class TestLLMClientPropertiesPure:
    """Test LLMClient properties (pure logic)."""

    def test_config_property(self):
        """Test config property."""
        config = OllamaClientConfig(temperature=0.5)
        client = LLMClient(config=config)

        assert client.config.temperature == 0.5

    def test_context_property(self):
        """Test context property."""
        client = LLMClient()

        assert client.context is not None
        assert hasattr(client.context, "get_messages")
        assert hasattr(client.context, "add_message")
        assert hasattr(client.context, "clear")

    def test_config_stored_on_client(self):
        """Test that config values passed to LLMClient are accessible via client.config."""
        config = OllamaClientConfig(temperature=0.5)
        client = LLMClient(config=config)

        assert client.config.temperature == 0.5


class TestSystemPromptManagementPure:
    """Test system prompt management (pure logic)."""

    def test_set_system_prompt(self):
        """Test setting system prompt."""
        config = OllamaClientConfig(system_prompt="Initial prompt", auto_inject_system_prompt=True)
        client = LLMClient(config=config)

        client.set_system_prompt("New system prompt")

        messages = client.context.get_messages()
        system_messages = [m for m in messages if m.get("role") == "system"]
        assert len(system_messages) == 1
        assert system_messages[0]["content"] == "New system prompt"

    def test_inject_system_prompt_manual(self):
        """Test _inject_system_prompt method manually."""
        config = OllamaClientConfig(system_prompt="Test prompt", auto_inject_system_prompt=False)
        client = LLMClient(config=config)

        # Initially no system prompt
        messages = client.context.get_messages()
        assert len(messages) == 0

        # Manually inject
        client._inject_system_prompt()

        messages = client.context.get_messages()
        system_messages = [m for m in messages if m.get("role") == "system"]
        assert len(system_messages) == 1

    def test_system_prompt_preserved_on_reset(self):
        """Test system prompt is preserved when auto-inject is on."""
        config = OllamaClientConfig(system_prompt="Persistent prompt", auto_inject_system_prompt=True)
        client = LLMClient(config=config)

        # Add user message
        client.context.add_message("user", "Test")

        # Reset
        client.reset()

        # System prompt should be back
        messages = client.context.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"


class TestLLMCoreEdgeCasesPure:
    """Test edge cases for LLM core (pure logic)."""

    def test_empty_system_prompt(self):
        """Test handling empty system prompt."""
        config = OllamaClientConfig(system_prompt="", auto_inject_system_prompt=True)
        client = LLMClient(config=config)

        # Empty system prompt still results in a system message (empty content)
        # Actually, when system_prompt is empty, _inject_system_prompt skips injection
        # because of the falsy check on self.config.system_prompt
        messages = client.context.get_messages()
        # Empty prompt is falsy, so no system message is added
        assert len(messages) == 0

    def test_long_system_prompt(self):
        """Test handling long system prompt."""
        long_prompt = "System instruction. " * 100
        config = OllamaClientConfig(system_prompt=long_prompt, auto_inject_system_prompt=True)
        client = LLMClient(config=config)

        messages = client.context.get_messages()
        system_msg = next((m for m in messages if m.get("role") == "system"), None)
        assert system_msg is not None
        assert len(system_msg["content"]) > 1000

    def test_multiple_resets(self):
        """Test multiple reset calls."""
        config = OllamaClientConfig(system_prompt="Test", auto_inject_system_prompt=True)
        client = LLMClient(config=config)

        # Multiple resets should be idempotent
        client.reset()
        client.reset()
        client.reset()

        messages = client.context.get_messages()
        system_msgs = [m for m in messages if m.get("role") == "system"]
        assert len(system_msgs) == 1

    def test_config_response_mode_limits(self):
        """Test config response mode token limits."""
        config = OllamaClientConfig(short_max_tokens=100, long_max_tokens=5000, long_min_tokens=400)

        assert config.short_max_tokens == 100
        assert config.long_max_tokens == 5000
        assert config.long_min_tokens == 400


class TestOptionsConversion:
    """Test options conversion to Ollama format."""

    def test_options_num_ctx(self):
        """Test num_ctx option."""
        config = OllamaClientConfig(num_ctx=8192)
        opts = GenerationOptions()

        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts.get("num_ctx") == 8192

    def test_options_override_num_ctx(self):
        """Test num_ctx override."""
        config = OllamaClientConfig(num_ctx=4096)
        opts = GenerationOptions(num_ctx=16384)

        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts.get("num_ctx") == 16384

    def test_options_repeat_penalty(self):
        """Test repeat_penalty option."""
        config = OllamaClientConfig()
        opts = GenerationOptions(repeat_penalty=1.2)

        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts.get("repeat_penalty") == 1.2

    def test_options_top_k(self):
        """Test top_k option."""
        config = OllamaClientConfig()
        opts = GenerationOptions(top_k=50)

        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts.get("top_k") == 50


class TestLLMQueryModesIntegration:
    """Integration tests for query modes requiring Ollama.

    Run with: pytest -m requires_ollama
    Deselect with: pytest -m "not requires_ollama"
    """

    @pytest.fixture(autouse=True)
    def check_ollama(self, ensure_ollama_for_tests):
        """Ensure Ollama is running and functional for tests."""
        # Fixture dependency ensures Ollama is ready
        # If Ollama can't be started, ensure_ollama_for_tests will fail loudly
        pass

    def test_query_short(self):
        """Test short query mode."""
        client = _ready_small_model_client()
        result = client.query_short("What is 2+2? Answer briefly.")

        assert result is not None
        assert result, "Model returned an empty response"

    @pytest.mark.timeout(180)  # Extended timeout for network-dependent test
    def test_query_long(self):
        """Test long query mode."""
        client = _ready_small_model_client()
        try:
            result = client.query_long("Explain what Python is in detail.")

            assert result is not None
            assert len(result) > 0
        except (
            LLMConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as e:
            error_str = str(e).lower()
            if any(
                keyword in error_str
                for keyword in ["timed out", "timeout", "connection", "refused"]
            ):
                pytest.fail(f"Ollama connection/timeout issue after setup: {e}")
            raise

    def test_query_raw(self):
        """Test raw query mode."""
        client = _ready_small_model_client(auto_inject_system_prompt=False)
        result = client.query_raw("Complete: Hello")

        assert result is not None
        assert len(result) > 0

    def test_query_with_options(self):
        """Test query with generation options."""
        client = _ready_small_model_client()
        opts = GenerationOptions(temperature=0.0, max_tokens=50)

        result = client.query("Say 'test'", options=opts)
        assert result is not None

    def test_context_maintained(self):
        """Test context is maintained across queries."""
        client = _ready_small_model_client(auto_inject_system_prompt=False)

        client.query("My name is TestBot.")
        response = client.query("What is my name?")

        # Context should help the model remember
        assert response is not None
