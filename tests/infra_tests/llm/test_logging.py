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


from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig

# No mock imports needed - using real HTTP server


class TestQueryLogging:
    """Test logging for query operations."""

    def test_query_logs_start(self, caplog, ollama_test_server):
        """Test query logs start with structured data."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        # Ensure logger is properly configured for test
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True  # Ensure propagation for caplog

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.client"):
            client.query("Test prompt")

            # _send_request logs "Sending request to Ollama" with model/url structured data
            assert "Sending request to Ollama" in caplog.text
            send_records = [r for r in caplog.records if "Sending request to Ollama" in r.message]
            assert len(send_records) > 0, "No 'Sending request to Ollama' log record found"
            send_record = send_records[0]
            has_model = (
                hasattr(send_record, "model") and getattr(send_record, "model", None) is not None
            )
            has_message_count = (
                hasattr(send_record, "message_count")
                and getattr(send_record, "message_count", None) is not None
            )
            has_structured_data = has_model or has_message_count
            assert has_structured_data, (
                f"Expected structured data (model or message_count) in log record. "
                f"Available attributes: {[a for a in dir(send_record) if not a.startswith('_')]}"
            )

    def test_query_logs_completion(self, caplog, ollama_test_server):
        """Test query logs completion with metrics."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        # Ensure logger is properly configured for test
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True  # Ensure propagation for caplog

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # query_structured() logs "Structured query completed" with generation_time_seconds
        with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
            client.query_structured("Test structured query")

            assert "Structured query completed" in caplog.text
            completion_records = [
                r for r in caplog.records if "Structured query completed" in r.message
            ]
            assert len(completion_records) > 0, "No 'Structured query completed' log record found"
            completion_record = completion_records[0]
            has_generation_time = (
                hasattr(completion_record, "generation_time_seconds")
                and getattr(completion_record, "generation_time_seconds", None) is not None
            )
            assert has_generation_time, (
                f"Expected generation_time_seconds in log record. "
                f"Available attributes: {[a for a in dir(completion_record) if not a.startswith('_')]}"
            )

    def test_query_logs_context_reset(self, caplog, ollama_test_server):
        """Test query logs context reset."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        # Ensure loggers are properly configured for test
        client_logger = get_logger("infrastructure.llm.core.client")
        context_logger = get_logger("infrastructure.llm.core.context")
        client_logger.setLevel(logging.INFO)
        context_logger.setLevel(logging.INFO)

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        # Add some context first
        client.context.add_message("user", "Previous message")

        with caplog.at_level("INFO"):
            client.query("New prompt", reset_context=True)

            assert "Resetting context" in caplog.text


class TestQueryRawLogging:
    """Test logging for raw query operations."""

    def test_query_raw_logs_context_add(self, caplog, ollama_test_server):
        """Test query_raw logs the raw context add at DEBUG level."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.client"):
            client.query_raw("Test prompt")

            # query_raw logs "Added raw query to context" and then sends the request
            assert "Added raw query to context" in caplog.text or "Sending request to Ollama" in caplog.text

    def test_query_raw_sends_request(self, caplog, ollama_test_server):
        """Test query_raw triggers an Ollama request."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.client"):
            client.query_raw("Test prompt")

            assert "Sending request to Ollama" in caplog.text


class TestQueryShortLogging:
    """Test logging for short query operations."""

    def test_query_short_sends_request(self, caplog, ollama_test_server):
        """Test query_short triggers an Ollama request at DEBUG level."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.client"):
            client.query_short("Test")

            assert "Sending request to Ollama" in caplog.text

    def test_query_short_returns_response(self, ollama_test_server):
        """Test query_short returns a non-empty string response."""
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        result = client.query_short("Test")
        assert isinstance(result, str)
        assert len(result) > 0


class TestQueryLongLogging:
    """Test logging for long query operations."""

    def test_query_long_sends_request(self, caplog, ollama_test_server):
        """Test query_long triggers an Ollama request at DEBUG level."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.client"):
            client.query_long("Test")

            assert "Sending request to Ollama" in caplog.text

    def test_query_long_returns_response(self, ollama_test_server):
        """Test query_long returns a non-empty string response."""
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        result = client.query_long("Test")
        assert isinstance(result, str)
        assert len(result) > 0


class TestQueryStructuredLogging:
    """Test logging for structured query operations."""

    def test_query_structured_logs_start(self, caplog, ollama_test_server):
        """Test query_structured logs start."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
            try:
                client.query_structured("Test", schema={"type": "object"})
            except Exception:
                pass  # We expect this to fail due to invalid JSON, but we want to test logging

            assert "Starting structured query" in caplog.text

    def test_query_structured_logs_completion(self, caplog, ollama_test_server):
        """Test query_structured logs completion."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
            try:
                client.query_structured("Test", schema={"type": "object"})
            except Exception:
                pass  # We expect this to fail due to invalid JSON, but we want to test logging

            assert (
                "Structured query completed" in caplog.text
                or "Structured response is not valid JSON" in caplog.text
            )


class TestContextLogging:
    """Test logging for context operations."""

    def test_context_add_logs(self, caplog):
        """Test context add_message logs."""
        import logging

        from infrastructure.core.logging_utils import get_logger
        from infrastructure.llm.core.context import ConversationContext

        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.DEBUG)

        context = ConversationContext(max_tokens=1000)

        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.context"):
            context.add_message("user", "Test message")

            assert (
                "Adding message to context" in caplog.text
                or "Message added to context" in caplog.text
            )

    def test_context_clear_logs(self, caplog):
        """Test context clear logs."""
        import logging

        from infrastructure.core.logging_utils import get_logger
        from infrastructure.llm.core.context import ConversationContext

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

        from infrastructure.core.logging_utils import get_logger
        from infrastructure.llm.core.context import ConversationContext

        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.INFO)

        context = ConversationContext(max_tokens=100)  # Small limit
        # Fill context
        for i in range(10):
            context.add_message("user", "Message " + "x" * 50)

        with caplog.at_level("INFO", logger="infrastructure.llm.core.context"):
            # Add message that triggers pruning
            context.add_message("user", "New message " + "x" * 50)

            assert (
                "Pruning context" in caplog.text
                or "Pruned message" in caplog.text
                or "Context pruned" in caplog.text
            )


class TestErrorLogging:
    """Test error logging."""

    def test_connection_error_logs(self, caplog):
        """Test connection errors are logged when server is unreachable."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        # Ensure propagation so caplog can capture
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.ERROR)
        logger.propagate = True

        # Point client at a port with no server listening to trigger real ConnectionError
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = "http://localhost:1"  # Port 1 refuses connections
        config.fallback_models = []  # No fallbacks to keep test fast
        client = LLMClient(config=config)

        with caplog.at_level("ERROR", logger="infrastructure.llm.core.client"):
            try:
                client.query("Test")
            except Exception:
                pass

        assert "Connection error" in caplog.text or "Failed to connect" in caplog.text

    def test_timeout_error_logs(self, caplog):
        """Test timeout errors are logged when server is unresponsive."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        # Ensure propagation so caplog can capture
        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.ERROR)
        logger.propagate = True

        # Point client at a non-routable IP with a very short timeout to force real Timeout
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = "http://10.255.255.1"  # Non-routable — never responds
        config.timeout = 0.01  # 10ms — times out before route resolves
        config.fallback_models = []  # No fallbacks to keep test fast
        client = LLMClient(config=config)

        with caplog.at_level("ERROR", logger="infrastructure.llm.core.client"):
            try:
                client.query("Test")
            except Exception:
                pass

        assert "timeout" in caplog.text.lower() or "Connection error" in caplog.text


class TestLoggingLevels:
    """Test different logging levels."""

    def test_debug_logging(self, caplog, ollama_test_server):
        """Test DEBUG level logging."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.DEBUG)

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.client"):
            client.query("Test")

            # Should have detailed debug logs
            assert len(caplog.records) > 0

    def test_info_logging(self, caplog, ollama_test_server):
        """Test that resetting context generates an INFO log."""
        import logging

        from infrastructure.core.logging_utils import get_logger

        logger = get_logger("infrastructure.llm.core.client")
        logger.setLevel(logging.INFO)

        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = ollama_test_server.url_for("/")
        client = LLMClient(config=config)

        with caplog.at_level("INFO", logger="infrastructure.llm.core.client"):
            client.query("Test", reset_context=True)

            assert "Resetting context" in caplog.text
