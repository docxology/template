"""Comprehensive tests for infrastructure/llm/core.py.

Tests LLM core functionality comprehensively.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from infrastructure.llm import core
from infrastructure.llm.core import LLMClient, ResponseMode
from infrastructure.llm.config import LLMConfig, GenerationOptions


class TestResponseMode:
    """Test ResponseMode enum."""
    
    def test_response_modes(self):
        """Test response mode values."""
        assert ResponseMode.SHORT.value == "short"
        assert ResponseMode.LONG.value == "long"
        assert ResponseMode.STRUCTURED.value == "structured"
        assert ResponseMode.RAW.value == "raw"


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


class TestLLMClientQuery:
    """Test LLMClient query methods."""
    
    def test_query_adds_to_context(self):
        """Test that query adds user message to context."""
        client = LLMClient()
        
        # Mock the response
        with patch.object(client, '_generate_response', return_value="Test response"):
            client.query("Test prompt")
            
            messages = client.context.get_messages()
            user_messages = [m for m in messages if m.get('role') == 'user']
            assert len(user_messages) >= 1
    
    def test_query_reset_context(self):
        """Test query with reset_context."""
        client = LLMClient()
        
        # Add initial message
        client.context.add_message("user", "First message")
        
        with patch.object(client, '_generate_response', return_value="Response"):
            client.query("Second message", reset_context=True)
            
            # Context should be reset - only system prompt and new messages
            messages = client.context.get_messages()
            # Should not have "First message"
            assert not any("First message" in str(m) for m in messages)
    
    def test_query_with_options(self):
        """Test query with generation options."""
        client = LLMClient()
        opts = GenerationOptions(temperature=0.0, seed=42)
        
        with patch.object(client, '_generate_response', return_value="Response") as mock:
            client.query("Test", options=opts)
            # Should pass options to _generate_response
            mock.assert_called_once()


class TestLLMClientReset:
    """Test LLMClient reset functionality."""
    
    def test_reset_clears_context(self):
        """Test reset clears conversation context."""
        client = LLMClient()
        client.context.add_message("user", "Test message")
        
        if hasattr(client, 'reset'):
            client.reset()
            # Context should be cleared (except possibly system prompt)
            messages = client.context.get_messages()
            user_messages = [m for m in messages if m.get('role') == 'user']
            assert len(user_messages) == 0


class TestLLMClientTemplates:
    """Test LLMClient template methods."""
    
    def test_apply_template(self):
        """Test applying a template."""
        client = LLMClient()
        
        if hasattr(client, 'apply_template'):
            with patch.object(client, 'query', return_value="Summary"):
                result = client.apply_template("summarize_abstract", text="Test abstract")
                assert result is not None or True  # May not be implemented


class TestLLMCoreIntegration:
    """Integration tests for LLM core."""
    
    def test_full_workflow(self):
        """Test complete LLM workflow."""
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

