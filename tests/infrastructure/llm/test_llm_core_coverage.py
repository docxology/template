"""Comprehensive tests for infrastructure/llm/core.py.

Tests LLM core functionality using real data (No Mocks Policy):
- Pure logic tests for initialization, config, context management
- Integration tests marked with @pytest.mark.requires_ollama for network calls
"""

import pytest

from infrastructure.llm.core.client import LLMClient, ResponseMode
from infrastructure.llm.core.config import LLMConfig, GenerationOptions


class TestResponseMode:
    """Test ResponseMode enum."""
    
    def test_response_modes(self):
        """Test response mode values."""
        assert ResponseMode.SHORT.value == "short"
        assert ResponseMode.LONG.value == "long"
        assert ResponseMode.STRUCTURED.value == "structured"
        assert ResponseMode.RAW.value == "raw"
    
    def test_response_mode_is_string_enum(self):
        """Test ResponseMode is a string enum."""
        assert isinstance(ResponseMode.SHORT, str)
        assert ResponseMode.SHORT == "short"
    
    def test_all_response_modes(self):
        """Test all response modes are defined."""
        modes = [m.value for m in ResponseMode]
        assert "short" in modes
        assert "long" in modes
        assert "structured" in modes
        assert "raw" in modes


class TestLLMClientInit:
    """Test LLMClient initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        client = LLMClient()
        assert client is not None
        assert client.config is not None
    
    def test_init_with_config(self):
        """Test initialization with config."""
        config = LLMConfig(
            default_model="test-model",
            temperature=0.5
        )
        client = LLMClient(config=config)
        assert client.config.default_model == "test-model"
        assert client.config.temperature == 0.5
    
    def test_init_creates_context(self):
        """Test that init creates conversation context."""
        client = LLMClient()
        assert client.context is not None
    
    def test_init_context_max_tokens(self):
        """Test context window matches config."""
        config = LLMConfig(context_window=8192)
        client = LLMClient(config=config)
        assert client.context.max_tokens == 8192
    
    def test_init_with_fallback_models(self):
        """Test initialization with fallback models."""
        config = LLMConfig(fallback_models=["mistral", "phi3"])
        client = LLMClient(config=config)
        assert "mistral" in client.config.fallback_models
        assert "phi3" in client.config.fallback_models


class TestLLMClientSystemPrompt:
    """Test LLMClient system prompt functionality."""
    
    def test_system_prompt_injection(self):
        """Test system prompt is injected."""
        config = LLMConfig(
            system_prompt="Test system prompt",
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        # System prompt should be in context
        messages = client.context.get_messages()
        assert any(m.get('role') == 'system' for m in messages)
    
    def test_no_auto_inject(self):
        """Test disabling auto system prompt injection."""
        config = LLMConfig(
            system_prompt="Test prompt",
            auto_inject_system_prompt=False
        )
        client = LLMClient(config=config)
        
        messages = client.context.get_messages()
        assert len(messages) == 0
    
    def test_system_prompt_content(self):
        """Test system prompt content is preserved."""
        config = LLMConfig(
            system_prompt="You are a helpful assistant.",
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        messages = client.context.get_messages()
        system_msg = next((m for m in messages if m.get('role') == 'system'), None)
        assert system_msg is not None
        assert "helpful assistant" in system_msg['content']
    
    def test_inject_system_prompt_idempotent(self):
        """Test _inject_system_prompt is idempotent."""
        config = LLMConfig(
            system_prompt="Test prompt",
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        # Manually call again
        client._inject_system_prompt()
        
        messages = client.context.get_messages()
        system_msgs = [m for m in messages if m.get('role') == 'system']
        # Should only have one system message
        assert len(system_msgs) == 1


class TestLLMClientContextManagement:
    """Test LLMClient context management (pure logic, no network)."""
    
    def test_context_add_message(self):
        """Test adding messages to context."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        client.context.add_message("user", "Test message")
        
        messages = client.context.get_messages()
        assert len(messages) == 1
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == 'Test message'
    
    def test_context_multiple_messages(self):
        """Test adding multiple messages."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        client.context.add_message("user", "Question")
        client.context.add_message("assistant", "Answer")
        client.context.add_message("user", "Follow-up")
        
        messages = client.context.get_messages()
        assert len(messages) == 3
    
    def test_reset_clears_user_messages(self):
        """Test reset clears user messages."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        client.context.add_message("user", "Test message")
        client.reset()
        
        messages = client.context.get_messages()
        user_messages = [m for m in messages if m.get('role') == 'user']
        assert len(user_messages) == 0
    
    def test_reset_reinjects_system_prompt(self):
        """Test reset re-injects system prompt."""
        config = LLMConfig(
            system_prompt="System prompt",
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        client.context.add_message("user", "Test")
        client.reset()
        
        messages = client.context.get_messages()
        assert len(messages) == 1
        assert messages[0]['role'] == 'system'
    
    def test_set_system_prompt_resets_context(self):
        """Test set_system_prompt resets context."""
        config = LLMConfig(
            system_prompt="Old prompt",
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        client.context.add_message("user", "Test")
        client.set_system_prompt("New prompt")
        
        messages = client.context.get_messages()
        assert len(messages) == 1
        assert messages[0]['content'] == "New prompt"


class TestLLMClientGenerationOptions:
    """Test GenerationOptions integration with LLMClient."""
    
    def test_options_to_ollama_format(self):
        """Test options convert to Ollama format."""
        config = LLMConfig(temperature=0.7, max_tokens=2048, top_p=0.9)
        opts = GenerationOptions(temperature=0.5, max_tokens=500, seed=42)
        
        ollama_opts = opts.to_ollama_options(config)
        
        assert ollama_opts["temperature"] == 0.5
        assert ollama_opts["num_predict"] == 500
        assert ollama_opts["seed"] == 42
        assert ollama_opts["top_p"] == 0.9  # From config
    
    def test_default_options_use_config(self):
        """Test default options use config values."""
        config = LLMConfig(temperature=0.7, max_tokens=2048)
        opts = GenerationOptions()
        
        ollama_opts = opts.to_ollama_options(config)
        
        assert ollama_opts["temperature"] == 0.7
        assert ollama_opts["num_predict"] == 2048
    
    def test_options_with_stop_sequences(self):
        """Test options with stop sequences."""
        config = LLMConfig()
        opts = GenerationOptions(stop=["END", "STOP"])
        
        ollama_opts = opts.to_ollama_options(config)
        assert ollama_opts["stop"] == ["END", "STOP"]
    
    def test_options_format_json_flag(self):
        """Test format_json flag is set correctly."""
        opts = GenerationOptions(format_json=True)
        assert opts.format_json is True
        
        opts_no_json = GenerationOptions()
        assert opts_no_json.format_json is False


class TestLLMClientHelpers:
    """Test LLMClient helper methods (no network required for some)."""
    
    def test_check_connection_returns_bool(self):
        """Test check_connection returns boolean."""
        # Use non-existent host to ensure fast failure
        config = LLMConfig(base_url="http://localhost:99999", timeout=0.1)
        client = LLMClient(config=config)
        
        result = client.check_connection()
        assert isinstance(result, bool)
        assert result is False
    
    def test_client_has_required_methods(self):
        """Test client has all required methods."""
        client = LLMClient()
        
        assert hasattr(client, 'query')
        assert hasattr(client, 'query_raw')
        assert hasattr(client, 'query_short')
        assert hasattr(client, 'query_long')
        assert hasattr(client, 'query_structured')
        assert hasattr(client, 'stream_query')
        assert hasattr(client, 'reset')
        assert hasattr(client, 'set_system_prompt')
        assert hasattr(client, 'check_connection')
        assert hasattr(client, 'get_available_models')
        assert hasattr(client, 'apply_template')


class TestLLMCoreIntegration:
    """Integration tests for LLM core (no network)."""
    
    def test_full_workflow_setup(self):
        """Test complete LLM workflow setup."""
        config = LLMConfig(
            auto_inject_system_prompt=False
        )
        client = LLMClient(config=config)
        
        # Should be able to create client
        assert client is not None
        
        # Should have context
        assert client.context is not None
        
        # Should have config
        assert client.config is not None
    
    def test_config_chain(self):
        """Test config chaining with overrides."""
        config = LLMConfig(temperature=0.7)
        new_config = config.with_overrides(temperature=0.0, seed=42)
        
        client = LLMClient(config=new_config)
        
        assert client.config.temperature == 0.0
        assert client.config.seed == 42
    
    def test_options_from_config(self):
        """Test creating options from config."""
        config = LLMConfig()
        opts = config.create_options(temperature=0.0, seed=42)
        
        assert opts.temperature == 0.0
        assert opts.seed == 42


# =============================================================================
# INTEGRATION TESTS (Require Ollama)
# =============================================================================

@pytest.mark.requires_ollama
class TestLLMClientQueryIntegration:
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
    
    def test_query_adds_to_context(self):
        """Test that query adds messages to context."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        client.query("Say 'test'")
        
        messages = client.context.get_messages()
        user_msgs = [m for m in messages if m.get('role') == 'user']
        asst_msgs = [m for m in messages if m.get('role') == 'assistant']
        
        assert len(user_msgs) >= 1
        assert len(asst_msgs) >= 1
    
    def test_apply_template(self):
        """Test applying a template."""
        client = LLMClient()
        result = client.apply_template(
            "summarize_abstract",
            text="This is a test abstract about machine learning."
        )
        
        assert result is not None
        assert len(result) > 0
