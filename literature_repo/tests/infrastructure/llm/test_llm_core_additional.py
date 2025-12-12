"""Additional tests for infrastructure/llm/core.py to improve coverage.

Targets uncovered paths identified in coverage report:
- Fallback model logic (lines 122-132)
- query_raw with add_to_context (lines 168-172)
- query_structured JSON parsing edge cases (lines 324-342)
- Streaming methods (lines 435-468, 486-495, 513-522)
- get_available_models (lines 530-539)
- Error handling paths
"""

import json
from unittest.mock import patch, MagicMock
import pytest
import requests

from infrastructure.llm.core.client import LLMClient, ResponseMode
from infrastructure.llm.core.config import LLMConfig, GenerationOptions
from infrastructure.core.exceptions import LLMConnectionError, LLMError


class TestInjectSystemPrompt:
    """Test _inject_system_prompt edge cases."""

    def test_inject_system_prompt_empty_string(self):
        """Test _inject_system_prompt with empty system_prompt (line 78->exit)."""
        config = LLMConfig(
            system_prompt="",  # Empty string
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        # Should not add empty system message
        messages = client.context.get_messages()
        system_messages = [m for m in messages if m.get('role') == 'system']
        # Empty prompt means nothing injected
        assert len(system_messages) == 0

    def test_inject_system_prompt_none(self):
        """Test _inject_system_prompt with None system_prompt."""
        config = LLMConfig(
            system_prompt=None,
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        messages = client.context.get_messages()
        system_messages = [m for m in messages if m.get('role') == 'system']
        assert len(system_messages) == 0

    def test_inject_already_injected(self):
        """Test _inject_system_prompt when already injected."""
        config = LLMConfig(
            system_prompt="Test prompt",
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        # Manually call inject again
        client._inject_system_prompt()
        
        # Should not duplicate
        messages = client.context.get_messages()
        system_messages = [m for m in messages if m.get('role') == 'system']
        assert len(system_messages) == 1


class TestQueryFallback:
    """Test query fallback mechanism (lines 122-132)."""

    def test_query_fallback_on_connection_error(self):
        """Test fallback models on primary connection error."""
        config = LLMConfig(
            default_model="primary-model",
            fallback_models=["fallback1", "fallback2"],
            auto_inject_system_prompt=False
        )
        client = LLMClient(config=config)
        
        call_count = [0]
        
        def mock_generate(model, options=None):
            call_count[0] += 1
            if model == "primary-model":
                raise LLMConnectionError("Primary failed")
            elif model == "fallback1":
                raise LLMConnectionError("Fallback1 failed")
            else:
                return "Success from fallback2"
        
        with patch.object(client, '_generate_response', side_effect=mock_generate):
            result = client.query("Test prompt")
            
            assert result == "Success from fallback2"
            assert call_count[0] == 3  # Primary + 2 fallbacks

    def test_query_all_fallbacks_fail(self):
        """Test when all fallback models fail."""
        config = LLMConfig(
            default_model="primary",
            fallback_models=["fallback1"],
            auto_inject_system_prompt=False
        )
        client = LLMClient(config=config)
        
        def mock_generate(model, options=None):
            raise LLMConnectionError(f"Model {model} failed")
        
        with patch.object(client, '_generate_response', side_effect=mock_generate):
            with pytest.raises(LLMConnectionError):
                client.query("Test prompt")


class TestQueryRaw:
    """Test query_raw with add_to_context (lines 168-172)."""

    def test_query_raw_add_to_context_true(self):
        """Test query_raw adds messages when add_to_context=True."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Raw response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_raw("Test prompt", add_to_context=True)
            
            assert result == "Raw response"
            
            # Should be in context
            messages = client.context.get_messages()
            user_messages = [m for m in messages if m.get('role') == 'user']
            assistant_messages = [m for m in messages if m.get('role') == 'assistant']
            
            assert len(user_messages) == 1
            assert len(assistant_messages) == 1

    def test_query_raw_add_to_context_false(self):
        """Test query_raw does not add messages when add_to_context=False."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Raw response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_raw("Test prompt", add_to_context=False)
            
            assert result == "Raw response"
            
            # Should NOT be in context
            messages = client.context.get_messages()
            assert len(messages) == 0


class TestQueryStructuredJsonParsing:
    """Test query_structured JSON parsing edge cases (lines 324-342)."""

    def test_query_structured_valid_json(self):
        """Test query_structured with valid JSON response."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": '{"key": "value"}'}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_structured("Test prompt")
            
            assert result == {"key": "value"}

    def test_query_structured_wrapped_json(self):
        """Test query_structured extracts JSON from wrapped response (lines 332-336)."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        # Response with text before/after JSON
        wrapped_json = 'Here is the response:\n{"key": "value"}\nEnd of response.'
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": wrapped_json}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_structured("Test prompt")
            
            assert result == {"key": "value"}

    def test_query_structured_invalid_wrapped_json(self):
        """Test query_structured with invalid JSON in wrapper (lines 337-341)."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        # Response with braces but invalid JSON
        invalid_wrapped = 'Some text { invalid json content } more text'
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": invalid_wrapped}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with pytest.raises(LLMError) as exc_info:
                client.query_structured("Test prompt")
            
            assert "Failed to parse structured response" in str(exc_info.value)

    def test_query_structured_no_json(self):
        """Test query_structured with no JSON in response (lines 342-345)."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        # Response with no braces at all
        no_json = 'This is just plain text without any JSON'
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": no_json}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with pytest.raises(LLMError) as exc_info:
                client.query_structured("Test prompt")
            
            assert "Structured response must be valid JSON" in str(exc_info.value)

    def test_query_structured_with_schema(self):
        """Test query_structured with schema (line 305)."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": '{"name": "test"}'}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_structured("Test prompt", schema=schema)
            
            assert result == {"name": "test"}


class TestStreamQuery:
    """Test streaming methods (lines 435-468)."""

    def test_stream_query_basic(self):
        """Test basic stream_query functionality."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        # Create mock streaming response
        lines = [
            json.dumps({"message": {"content": "Hello"}}),
            json.dumps({"message": {"content": " world"}}),
            json.dumps({"message": {"content": "!"}}),
        ]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            chunks = list(client.stream_query("Test prompt"))
            
            assert chunks == ["Hello", " world", "!"]

    def test_stream_query_adds_to_context(self):
        """Test stream_query adds full response to context."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [
            json.dumps({"message": {"content": "Part1"}}),
            json.dumps({"message": {"content": "Part2"}}),
        ]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            # Consume the iterator
            list(client.stream_query("Test prompt"))
            
            # Check context
            messages = client.context.get_messages()
            assistant_messages = [m for m in messages if m.get('role') == 'assistant']
            
            assert len(assistant_messages) == 1
            assert assistant_messages[0]['content'] == "Part1Part2"

    def test_stream_query_connection_error(self):
        """Test stream_query handles connection errors."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        with patch('infrastructure.llm.core.client.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Failed")
            
            with pytest.raises(LLMConnectionError):
                list(client.stream_query("Test prompt"))

    def test_stream_query_empty_lines(self):
        """Test stream_query handles empty lines."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [
            json.dumps({"message": {"content": "Hello"}}),
            b"",  # Empty line
            json.dumps({"message": {"content": " world"}}),
        ]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = lines
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            chunks = list(client.stream_query("Test prompt"))
            
            # Should skip empty lines
            assert chunks == ["Hello", " world"]


class TestStreamShort:
    """Test stream_short method (lines 486-495)."""

    def test_stream_short(self):
        """Test stream_short uses short options."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Short response"}})]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            chunks = list(client.stream_short("Test prompt"))
            
            assert len(chunks) > 0

    def test_stream_short_with_options(self):
        """Test stream_short with additional options."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        opts = GenerationOptions(temperature=0.5, seed=42)
        
        lines = [json.dumps({"message": {"content": "Response"}})]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            chunks = list(client.stream_short("Test", options=opts))
            
            assert len(chunks) > 0


class TestStreamLong:
    """Test stream_long method (lines 513-522)."""

    def test_stream_long(self):
        """Test stream_long uses long options."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Long detailed response"}})]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            chunks = list(client.stream_long("Test prompt"))
            
            assert len(chunks) > 0

    def test_stream_long_with_options(self):
        """Test stream_long with additional options."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        opts = GenerationOptions(temperature=0.7, seed=123)
        
        lines = [json.dumps({"message": {"content": "Response"}})]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            chunks = list(client.stream_long("Test", options=opts))
            
            assert len(chunks) > 0


class TestGetAvailableModels:
    """Test get_available_models method (lines 530-539)."""

    def test_get_available_models_success(self):
        """Test successful model list retrieval."""
        client = LLMClient()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:latest"},
                {"name": "llama3:8b"},
                {"name": "mistral:latest"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.get', return_value=mock_response):
            models = client.get_available_models()
            
            # Should deduplicate based on base name
            assert "llama3" in models
            assert "mistral" in models
            assert len(models) == 2  # Deduplicated

    def test_get_available_models_empty(self):
        """Test get_available_models with no models."""
        client = LLMClient()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.get', return_value=mock_response):
            models = client.get_available_models()
            
            assert models == []

    def test_get_available_models_connection_error(self):
        """Test get_available_models returns fallback on error (line 537-539)."""
        config = LLMConfig(fallback_models=["fallback1", "fallback2"])
        client = LLMClient(config=config)
        
        with patch('infrastructure.llm.core.client.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Failed")
            
            models = client.get_available_models()
            
            # Should return fallback models
            assert models == ["fallback1", "fallback2"]


class TestCheckConnection:
    """Test check_connection method."""

    def test_check_connection_success(self):
        """Test check_connection returns True on success."""
        client = LLMClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch('infrastructure.llm.core.client.requests.get', return_value=mock_response):
            result = client.check_connection()
            
            assert result is True

    def test_check_connection_non_200(self):
        """Test check_connection returns False on non-200."""
        client = LLMClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch('infrastructure.llm.core.client.requests.get', return_value=mock_response):
            result = client.check_connection()
            
            assert result is False

    def test_check_connection_exception(self):
        """Test check_connection returns False on exception (line 552)."""
        client = LLMClient()
        
        with patch('infrastructure.llm.core.client.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            
            result = client.check_connection()
            
            assert result is False


class TestGenerateResponseDirect:
    """Test _generate_response_direct method."""

    def test_generate_response_direct_with_format_json(self):
        """Test _generate_response_direct with format_json option."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        opts = GenerationOptions(format_json=True)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": '{"key": "value"}'}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response) as mock_post:
            result = client._generate_response_direct(
                "test-model",
                [{"role": "user", "content": "test"}],
                options=opts
            )
            
            # Verify format was set in payload
            call_kwargs = mock_post.call_args[1]
            payload = call_kwargs['json']
            assert payload.get('format') == 'json'

    def test_generate_response_direct_connection_error(self):
        """Test _generate_response_direct raises LLMConnectionError."""
        # Use invalid endpoint to trigger real connection error
        config = LLMConfig(
            base_url="http://localhost:99999",
            timeout=0.1,
            auto_inject_system_prompt=False
        )
        client = LLMClient(config=config)
        
        with pytest.raises(LLMConnectionError) as exc_info:
            client._generate_response_direct(
                "test-model",
                [{"role": "user", "content": "test"}]
            )
        
        assert "Failed to connect to Ollama" in str(exc_info.value)


class TestQueryShortLongOptions:
    """Test query_short and query_long with options."""

    def test_query_short_with_options(self):
        """Test query_short passes options correctly."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        opts = GenerationOptions(temperature=0.3, seed=42, stop=["END"])
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Short answer"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_short("Test prompt", options=opts)
            
            assert result is not None

    def test_query_long_with_options(self):
        """Test query_long passes options correctly."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        opts = GenerationOptions(temperature=0.8, seed=123, stop=["DONE"])
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Long detailed answer"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_long("Test prompt", options=opts)
            
            assert result is not None

    def test_query_short_no_options(self):
        """Test query_short with no options."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Answer"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_short("Test prompt")
            
            assert result is not None

    def test_query_long_no_options(self):
        """Test query_long with no options."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Detailed answer"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query_long("Test prompt")
            
            assert result is not None


class TestQueryResetWithAutoInject:
    """Test query with reset_context and auto_inject (lines 110-111)."""

    def test_query_reset_context_reinjects_system_prompt(self):
        """Test reset_context with auto_inject_system_prompt re-injects system prompt."""
        config = LLMConfig(
            system_prompt="Research assistant",
            auto_inject_system_prompt=True
        )
        client = LLMClient(config=config)
        
        # Add some messages
        client.context.add_message("user", "First question")
        client.context.add_message("assistant", "First answer")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "New response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            result = client.query("New question", reset_context=True)
            
            messages = client.context.get_messages()
            
            # Should have: system, user (new), assistant (new)
            system_messages = [m for m in messages if m.get('role') == 'system']
            assert len(system_messages) == 1
            assert system_messages[0]['content'] == "Research assistant"

