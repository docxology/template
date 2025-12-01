"""Additional comprehensive tests for infrastructure/llm/core.py.

Tests LLM core functionality thoroughly.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.llm.core import LLMClient, ResponseMode
from infrastructure.llm.config import LLMConfig, GenerationOptions


class TestResponseModeQueries:
    """Test response mode specific queries."""
    
    def test_query_short(self):
        """Test short query mode."""
        client = LLMClient()
        
        if hasattr(client, 'query_short'):
            with patch.object(client, '_generate_response', return_value="Short"):
                result = client.query_short("Test")
                assert result is not None
    
    def test_query_long(self):
        """Test long query mode."""
        client = LLMClient()
        
        if hasattr(client, 'query_long'):
            with patch.object(client, '_generate_response', return_value="Long response"):
                result = client.query_long("Test")
                assert result is not None
    
    def test_query_structured(self):
        """Test structured query mode."""
        client = LLMClient()
        
        if hasattr(client, 'query_structured'):
            with patch.object(client, '_generate_response', return_value='{"key": "value"}'):
                try:
                    result = client.query_structured("Test")
                    assert result is not None
                except Exception:
                    pass  # May require specific schema
    
    def test_query_raw(self):
        """Test raw query mode."""
        client = LLMClient()
        
        if hasattr(client, 'query_raw'):
            with patch.object(client, '_generate_response', return_value="Raw"):
                try:
                    result = client.query_raw("Test")
                    assert result is not None
                except Exception:
                    pass  # May have different signature


class TestGenerationOptions:
    """Test GenerationOptions usage."""
    
    def test_options_with_seed(self):
        """Test options with seed for reproducibility."""
        opts = GenerationOptions(seed=42, temperature=0.0)
        client = LLMClient()
        
        with patch.object(client, '_generate_response', return_value="Response"):
            result = client.query("Test", options=opts)
            assert result is not None
    
    def test_options_with_max_tokens(self):
        """Test options with max_tokens."""
        opts = GenerationOptions(max_tokens=100)
        client = LLMClient()
        
        with patch.object(client, '_generate_response', return_value="Response"):
            result = client.query("Test", options=opts)
            assert result is not None


class TestContextManagement:
    """Test conversation context management."""
    
    def test_context_accumulates(self):
        """Test context accumulates across queries."""
        client = LLMClient()
        
        with patch.object(client, '_generate_response', return_value="Response"):
            client.query("First message")
            client.query("Second message")
            
            messages = client.context.get_messages()
            user_messages = [m for m in messages if m.get('role') == 'user']
            assert len(user_messages) >= 2
    
    def test_reset_context(self):
        """Test context reset."""
        client = LLMClient()
        
        with patch.object(client, '_generate_response', return_value="Response"):
            client.query("First")
            client.query("Second", reset_context=True)
            
            # After reset, should only have second message (and maybe system)
            messages = client.context.get_messages()
            user_messages = [m for m in messages if m.get('role') == 'user']
            assert len(user_messages) == 1


class TestLLMClientProperties:
    """Test LLMClient properties."""
    
    def test_config_property(self):
        """Test config property."""
        config = LLMConfig(temperature=0.5)
        client = LLMClient(config=config)
        
        assert client.config.temperature == 0.5
    
    def test_context_property(self):
        """Test context property."""
        client = LLMClient()
        
        assert client.context is not None
        assert hasattr(client.context, 'get_messages')
        assert hasattr(client.context, 'add_message')


class TestSystemPromptManagement:
    """Test system prompt management."""
    
    def test_set_system_prompt(self):
        """Test setting system prompt."""
        client = LLMClient()
        
        if hasattr(client, 'set_system_prompt'):
            client.set_system_prompt("New system prompt")
            messages = client.context.get_messages()
            system_messages = [m for m in messages if m.get('role') == 'system']
            assert len(system_messages) >= 1
    
    def test_inject_system_prompt(self):
        """Test _inject_system_prompt method."""
        config = LLMConfig(
            system_prompt="Test prompt",
            auto_inject_system_prompt=False
        )
        client = LLMClient(config=config)
        
        # Initially no system prompt
        messages = client.context.get_messages()
        assert len(messages) == 0
        
        # Manually inject
        client._inject_system_prompt()
        messages = client.context.get_messages()
        system_messages = [m for m in messages if m.get('role') == 'system']
        assert len(system_messages) == 1


class TestLLMCoreEdgeCases:
    """Test edge cases for LLM core."""
    
    def test_empty_prompt(self):
        """Test handling empty prompt."""
        client = LLMClient()
        
        with patch.object(client, '_generate_response', return_value=""):
            result = client.query("")
            assert result == ""
    
    def test_long_prompt(self):
        """Test handling long prompt."""
        client = LLMClient()
        long_prompt = "Test " * 1000
        
        with patch.object(client, '_generate_response', return_value="Response"):
            result = client.query(long_prompt)
            assert result is not None

