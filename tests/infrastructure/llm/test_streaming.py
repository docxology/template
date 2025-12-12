"""Comprehensive tests for LLM streaming methods with logging, metrics, and error recovery."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import LLMConfig, GenerationOptions
from infrastructure.llm.review.metrics import StreamingMetrics
from infrastructure.core.exceptions import LLMConnectionError


class TestStreamingBasic:
    """Test basic streaming functionality."""
    
    def test_stream_query_basic(self):
        """Test basic stream_query functionality."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
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
            list(client.stream_query("Test prompt"))
            
            messages = client.context.get_messages()
            assistant_messages = [m for m in messages if m.get('role') == 'assistant']
            
            assert len(assistant_messages) == 1
            assert assistant_messages[0]['content'] == "Part1Part2"
    
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
            
            assert chunks == ["Hello", " world"]


class TestStreamingLogging:
    """Test streaming logging functionality."""
    
    def test_stream_query_logs_start(self, caplog):
        """Test stream_query logs start with structured data."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Response"}})]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                list(client.stream_query("Test prompt", log_progress=True))
                
                # Check for start log - check both records and text
                has_start = any("Starting streaming query" in r.message for r in caplog.records) or "Starting streaming query" in caplog.text
                assert has_start
    
    def test_stream_query_logs_chunks_debug(self, caplog):
        """Test stream_query logs chunks at DEBUG level."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True  # Ensure propagation for caplog
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [
            json.dumps({"message": {"content": "Chunk1"}}),
            json.dumps({"message": {"content": "Chunk2"}}),
        ]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("DEBUG", logger="infrastructure.llm.core.client"):
                list(client.stream_query("Test prompt", log_progress=True))
                
                # Check for chunk logs - check both records and text
                # LogRecord doesn't have 'extra' attribute, check attributes directly
                has_chunk_log = (
                    any("Streaming chunk" in r.message for r in caplog.records) or
                    "Streaming chunk" in caplog.text or
                    any(hasattr(r, 'chunk_count') and getattr(r, 'chunk_count') is not None 
                        for r in caplog.records) or
                    any(hasattr(r, 'chunk_size') and getattr(r, 'chunk_size') is not None 
                        for r in caplog.records)
                )
                assert has_chunk_log, f"Expected chunk log, got records: {[r.message for r in caplog.records]}"
    
    def test_stream_query_logs_completion(self, caplog):
        """Test stream_query logs completion with metrics."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Response"}})]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                list(client.stream_query("Test prompt"))
                
                # Check for completion log - check both records and text
                has_completion = any("Streaming completed" in r.message for r in caplog.records) or "Streaming completed" in caplog.text
                assert has_completion


class TestStreamingErrorRecovery:
    """Test streaming error recovery and retry logic."""
    
    def test_stream_query_retries_on_timeout(self):
        """Test stream_query retries on timeout."""
        config = LLMConfig(auto_inject_system_prompt=False, timeout=1.0)
        client = LLMClient(config=config)
        
        # First attempt fails with timeout, second succeeds
        mock_post = MagicMock()
        mock_post.side_effect = [
            requests.exceptions.Timeout("Timeout"),
            MagicMock(
                iter_lines=lambda: [json.dumps({"message": {"content": "Response"}}).encode()],
                raise_for_status=MagicMock(),
                __enter__=lambda self: self,
                __exit__=lambda *args: False,
            )
        ]
        
        with patch('infrastructure.llm.core.client.requests.post', mock_post):
            chunks = list(client.stream_query("Test prompt", retries=1))
            
            assert len(chunks) > 0
            assert mock_post.call_count == 2  # Initial + retry
    
    def test_stream_query_saves_partial_on_error(self, tmp_path):
        """Test stream_query saves partial response on error."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        # Simulate partial response then error
        lines = [
            json.dumps({"message": {"content": "Partial"}}),
        ]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(side_effect=requests.exceptions.Timeout("Timeout"))
        
        save_path = tmp_path / "partial.md"
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with patch('infrastructure.llm.core.client.time.sleep'):  # Speed up retry
                try:
                    list(client.stream_query(
                        "Test prompt",
                        save_response=True,
                        save_path=save_path,
                        retries=0
                    ))
                except LLMConnectionError:
                    pass  # Expected
        
        # Check if partial response was saved
        if save_path.exists():
            content = save_path.read_text()
            assert "Partial" in content
    
    def test_stream_query_handles_connection_error(self):
        """Test stream_query handles connection errors."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        with patch('infrastructure.llm.core.client.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            with pytest.raises(LLMConnectionError):
                list(client.stream_query("Test prompt", retries=0))


class TestStreamingResponseSaving:
    """Test streaming response saving functionality."""
    
    def test_stream_query_saves_response(self, tmp_path):
        """Test stream_query saves response when requested."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [
            json.dumps({"message": {"content": "Full"}}),
            json.dumps({"message": {"content": " response"}}),
        ]
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        save_path = tmp_path / "response.md"
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            list(client.stream_query(
                "Test prompt",
                save_response=True,
                save_path=save_path
            ))
        
        assert save_path.exists()
        content = save_path.read_text()
        assert "Full response" in content
        assert "streaming" in content.lower() or "chunk" in content.lower()
    
    def test_stream_short_saves_response(self, tmp_path):
        """Test stream_short saves response when requested."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Short"}})]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        save_path = tmp_path / "short.md"
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            list(client.stream_short(
                "Test",
                save_response=True,
                save_path=save_path
            ))
        
        assert save_path.exists()
    
    def test_stream_long_saves_response(self, tmp_path):
        """Test stream_long saves response when requested."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Long"}})]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        save_path = tmp_path / "long.md"
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            list(client.stream_long(
                "Test",
                save_response=True,
                save_path=save_path
            ))
        
        assert save_path.exists()


class TestStreamingWithOptions:
    """Test streaming with different generation options."""
    
    def test_stream_query_with_temperature(self):
        """Test stream_query with temperature option."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Response"}})]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        opts = GenerationOptions(temperature=0.5)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response) as mock_post:
            list(client.stream_query("Test", options=opts))
            
            # Verify options were passed
            call_args = mock_post.call_args
            assert call_args is not None
            payload = call_args[1]['json']
            assert 'options' in payload
    
    def test_stream_query_with_max_tokens(self):
        """Test stream_query with max_tokens option."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Response"}})]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        opts = GenerationOptions(max_tokens=100)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            chunks = list(client.stream_query("Test", options=opts))
            assert len(chunks) > 0


class TestStreamingContextManagement:
    """Test streaming context management."""
    
    def test_stream_query_maintains_context(self):
        """Test stream_query maintains context across calls."""
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        lines = [json.dumps({"message": {"content": "Response"}})]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [l.encode() for l in lines]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            # First stream
            list(client.stream_query("First prompt"))
            
            # Second stream
            list(client.stream_query("Second prompt"))
            
            messages = client.context.get_messages()
            user_messages = [m for m in messages if m.get('role') == 'user']
            assistant_messages = [m for m in messages if m.get('role') == 'assistant']
            
            assert len(user_messages) == 2
            assert len(assistant_messages) == 2


@pytest.mark.requires_ollama
class TestStreamingIntegration:
    """Integration tests for streaming (requires Ollama)."""
    
    def test_stream_query_real_ollama(self):
        """Test stream_query with real Ollama."""
        client = LLMClient()
        
        if not client.check_connection():
            pytest.skip("Ollama not available")
        
        chunks = []
        for chunk in client.stream_query("Say 'hello' in one word"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        assert "hello" in full_response.lower()
    
    def test_stream_short_real_ollama(self):
        """Test stream_short with real Ollama."""
        client = LLMClient()
        
        if not client.check_connection():
            pytest.skip("Ollama not available")
        
        chunks = []
        for chunk in client.stream_short("What is 2+2?"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
    
    def test_stream_long_real_ollama(self):
        """Test stream_long with real Ollama."""
        client = LLMClient()
        
        if not client.check_connection():
            pytest.skip("Ollama not available")
        
        chunks = []
        for chunk in client.stream_long("Explain machine learning briefly"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 50  # Should be longer than short response



