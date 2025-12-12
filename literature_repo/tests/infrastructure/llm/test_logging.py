"""Tests for structured logging in LLM operations.

Test Pattern:
    All logging tests use `caplog` fixture with explicit logger configuration.
    Ensure the logger is properly configured before tests run by:
    1. Getting the logger with get_logger()
    2. Setting the appropriate log level
    3. Using caplog.at_level() with the logger name to capture logs
    
    Example:
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
            # Test code
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import LLMConfig, GenerationOptions


class TestQueryLogging:
    """Test logging for query operations."""
    
    def test_query_logs_start(self, caplog):
        """Test query logs start with structured data."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        # Ensure logger is properly configured for test
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        logger.propagate = True  # Ensure propagation for caplog
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query("Test prompt")
                
                assert "Starting query" in caplog.text
                # Check LogRecord attributes for structured data (extra fields)
                # In Python logging, extra={...} fields become attributes on LogRecord
                start_records = [r for r in caplog.records if "Starting query" in r.message]
                assert len(start_records) > 0, "No 'Starting query' log record found"
                start_record = start_records[0]
                # Check for structured data in LogRecord attributes
                # These should be set by the extra={...} parameter in the logging call
                has_model = hasattr(start_record, 'model') and getattr(start_record, 'model', None) is not None
                has_prompt_length = hasattr(start_record, 'prompt_length') and getattr(start_record, 'prompt_length', None) is not None
                has_structured_data = has_model or has_prompt_length
                assert has_structured_data, (
                    f"Expected structured data (model or prompt_length) in log record. "
                    f"Available attributes: {[a for a in dir(start_record) if not a.startswith('_')]}"
                )
    
    def test_query_logs_completion(self, caplog):
        """Test query logs completion with metrics."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        # Ensure logger is properly configured for test
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        logger.propagate = True  # Ensure propagation for caplog
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Response text"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query("Test prompt")
                
                assert "Query completed" in caplog.text
                # Check LogRecord attributes for structured data (extra fields)
                # In Python logging, extra={...} fields become attributes on LogRecord
                completion_records = [r for r in caplog.records if "Query completed" in r.message]
                assert len(completion_records) > 0, "No 'Query completed' log record found"
                completion_record = completion_records[0]
                # Check for structured data in LogRecord attributes
                # These should be set by the extra={...} parameter in the logging call
                has_response_length = hasattr(completion_record, 'response_length') and getattr(completion_record, 'response_length', None) is not None
                has_generation_time = hasattr(completion_record, 'generation_time_seconds') and getattr(completion_record, 'generation_time_seconds', None) is not None
                has_structured_data = has_response_length or has_generation_time
                assert has_structured_data, (
                    f"Expected structured data (response_length or generation_time_seconds) in log record. "
                    f"Available attributes: {[a for a in dir(completion_record) if not a.startswith('_')]}"
                )
    
    def test_query_logs_context_reset(self, caplog):
        """Test query logs context reset."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        # Ensure loggers are properly configured for test
        client_logger = get_logger("infrastructure.llm.core.client")
        context_logger = get_logger("infrastructure.llm.core.context")
        client_logger.setLevel(logging.INFO)
        context_logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        # Add some context first
        client.context.add_message("user", "Previous message")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO"):
                client.query("New prompt", reset_context=True)
                
                assert "Resetting context" in caplog.text


class TestQueryRawLogging:
    """Test logging for raw query operations."""
    
    def test_query_raw_logs_start(self, caplog):
        """Test query_raw logs start."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query_raw("Test prompt")
                
                assert "Starting raw query" in caplog.text
    
    def test_query_raw_logs_completion(self, caplog):
        """Test query_raw logs completion."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query_raw("Test prompt")
                
                assert "Raw query completed" in caplog.text


class TestQueryShortLogging:
    """Test logging for short query operations."""
    
    def test_query_short_logs_start(self, caplog):
        """Test query_short logs start."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Short"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query_short("Test")
                
                assert "Starting short query" in caplog.text
    
    def test_query_short_logs_completion(self, caplog):
        """Test query_short logs completion."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Short"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query_short("Test")
                
                assert "Short query completed" in caplog.text


class TestQueryLongLogging:
    """Test logging for long query operations."""
    
    def test_query_long_logs_start(self, caplog):
        """Test query_long logs start."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Long response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query_long("Test")
                
                assert "Starting long query" in caplog.text
    
    def test_query_long_logs_completion(self, caplog):
        """Test query_long logs completion."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Long response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query_long("Test")
                
                assert "Long query completed" in caplog.text


class TestQueryStructuredLogging:
    """Test logging for structured query operations."""
    
    def test_query_structured_logs_start(self, caplog):
        """Test query_structured logs start."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": '{"key": "value"}'}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query_structured("Test", schema={"type": "object"})
                
                assert "Starting structured query" in caplog.text
    
    def test_query_structured_logs_completion(self, caplog):
        """Test query_structured logs completion."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": '{"key": "value"}'}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query_structured("Test", schema={"type": "object"})
                
                assert "Structured query completed" in caplog.text


class TestContextLogging:
    """Test logging for context operations."""
    
    def test_context_add_logs(self, caplog):
        """Test context add_message logs."""
        import logging
        from infrastructure.llm.core.context import ConversationContext
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.DEBUG)
        
        context = ConversationContext(max_tokens=1000)
        
        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.context"):
            context.add_message("user", "Test message")
            
            assert "Adding message to context" in caplog.text or "Message added to context" in caplog.text
    
    def test_context_clear_logs(self, caplog):
        """Test context clear logs."""
        import logging
        from infrastructure.llm.core.context import ConversationContext
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.INFO)
        
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "Test")
        
        with caplog.at_level("INFO", logger="infrastructure.llm.core.context"):
            context.clear()
            
            assert "Clearing context" in caplog.text
    
    def test_context_prune_logs(self, caplog):
        """Test context prune logs."""
        import logging
        from infrastructure.llm.core.context import ConversationContext
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.INFO)
        
        context = ConversationContext(max_tokens=100)  # Small limit
        # Fill context
        for i in range(10):
            context.add_message("user", "Message " + "x" * 50)
        
        with caplog.at_level("INFO", logger="infrastructure.llm.core.context"):
            # Add message that triggers pruning
            context.add_message("user", "New message " + "x" * 50)
            
            assert "Pruning context" in caplog.text or "Pruned message" in caplog.text or "Context pruned" in caplog.text


class TestErrorLogging:
    """Test error logging."""
    
    def test_connection_error_logs(self, caplog):
        """Test connection errors are logged."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.ERROR)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        with patch('infrastructure.llm.core.client.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            with caplog.at_level("ERROR", logger="infrastructure.llm.core.client"):
                try:
                    client.query("Test")
                except Exception:
                    pass
                
                assert "Connection error" in caplog.text or "Failed to connect" in caplog.text
    
    def test_timeout_error_logs(self, caplog):
        """Test timeout errors are logged."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.ERROR)
        
        config = LLMConfig(auto_inject_system_prompt=False, timeout=0.1)
        client = LLMClient(config=config)
        
        with patch('infrastructure.llm.core.client.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Timeout")
            
            with caplog.at_level("ERROR", logger="infrastructure.llm.core.client"):
                try:
                    client.query("Test")
                except Exception:
                    pass
                
                assert "timeout" in caplog.text.lower() or "Timeout" in caplog.text


class TestLoggingLevels:
    """Test different logging levels."""
    
    def test_debug_logging(self, caplog):
        """Test DEBUG level logging."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("DEBUG", logger="infrastructure.llm.core.client"):
                client.query("Test")
                
                # Should have detailed debug logs
                assert len(caplog.records) > 0
    
    def test_info_logging(self, caplog):
        """Test INFO level logging."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)
        
        config = LLMConfig(auto_inject_system_prompt=False)
        client = LLMClient(config=config)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Response"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('infrastructure.llm.core.client.requests.post', return_value=mock_response):
            with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
                client.query("Test")
                
                # Should have info logs - check both records and text
                has_info = any("Starting query" in r.message or "Query completed" in r.message 
                              for r in caplog.records) or "Starting query" in caplog.text or "Query completed" in caplog.text
                assert has_info



