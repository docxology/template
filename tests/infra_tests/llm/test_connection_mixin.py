"""Tests for infrastructure.llm.core._connection — _ConnectionMixin coverage."""

import json

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response

from infrastructure.core.exceptions import LLMConnectionError
from infrastructure.llm.core._connection import _ConnectionMixin
from infrastructure.llm.core.config import OllamaClientConfig, GenerationOptions


class FakeClient(_ConnectionMixin):
    """Minimal client using _ConnectionMixin for testing."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.config = OllamaClientConfig(base_url=base_url, timeout=timeout)


class TestGetAvailableModels:
    def test_success(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": [{"name": "llama3:latest"}, {"name": "gemma:7b"}, {"name": "llama3:8b"}]}
        )
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        models = client.get_available_models()
        assert "llama3" in models or "gemma" in models
        # Dedup: llama3:latest and llama3:8b both map to "llama3"
        assert len([m for m in models if m == "llama3"]) <= 1

    def test_connection_error_fallback(self):
        client = FakeClient("http://127.0.0.1:1", timeout=0.5)
        models = client.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0  # Fallback models

    def test_empty_models(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        models = client.get_available_models()
        assert models == []


class TestCheckConnection:
    def test_success(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        assert client.check_connection() is True

    def test_failure(self):
        client = FakeClient("http://127.0.0.1:1", timeout=0.5)
        assert client.check_connection(timeout=0.5) is False


class TestCheckConnectionWithReason:
    def test_success(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        ok, reason = client.check_connection_with_reason()
        assert ok is True
        assert reason is None

    def test_non_200(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_data("error", status=500)
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        ok, reason = client.check_connection_with_reason()
        assert ok is False
        assert "500" in reason

    def test_connection_error(self):
        client = FakeClient("http://127.0.0.1:1", timeout=0.5)
        ok, reason = client.check_connection_with_reason(timeout=0.5)
        assert ok is False
        assert reason is not None


class TestGenerateResponseDirect:
    def test_success(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/chat", method="POST").respond_with_json(
            {"message": {"content": "Hello from LLM"}}
        )
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        result = client._generate_response_direct(
            "testmodel", [{"role": "user", "content": "Hi"}]
        )
        assert result == "Hello from LLM"

    def test_empty_response_with_error(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/chat", method="POST").respond_with_json(
            {"message": {"content": ""}, "error": "Model not loaded"}
        )
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        with pytest.raises(LLMConnectionError, match="error"):
            client._generate_response_direct("testmodel", [{"role": "user", "content": "Hi"}])

    def test_thinking_tags_stripped(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/chat", method="POST").respond_with_json(
            {"message": {"content": "<think>reasoning</think>The answer is 42."}}
        )
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        result = client._generate_response_direct(
            "testmodel", [{"role": "user", "content": "What?"}]
        )
        assert "The answer is 42" in result
        assert "<think>" not in result

    def test_empty_after_strip_raises(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/chat", method="POST").respond_with_json(
            {"message": {"content": "<think>only thinking</think>"}}
        )
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        with pytest.raises(LLMConnectionError, match="empty"):
            client._generate_response_direct("m", [{"role": "user", "content": "x"}])

    def test_http_error(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/chat", method="POST").respond_with_data(
            "Not Found", status=404
        )
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        with pytest.raises(LLMConnectionError, match="HTTP"):
            client._generate_response_direct("m", [{"role": "user", "content": "x"}])

    def test_timeout_with_retry(self, httpserver: HTTPServer):
        """First request times out, second succeeds."""
        call_count = {"n": 0}

        def handler(request):
            call_count["n"] += 1
            if call_count["n"] == 1:
                import time
                time.sleep(2)
                return Response("timeout", status=408)
            return Response(
                json.dumps({"message": {"content": "Recovered"}}),
                content_type="application/json",
            )

        httpserver.expect_request("/api/chat", method="POST").respond_with_handler(handler)
        client = FakeClient(httpserver.url_for("").rstrip("/"), timeout=0.5)
        result = client._generate_response_direct(
            "m", [{"role": "user", "content": "x"}], retries=1
        )
        assert result == "Recovered"

    def test_connection_error_all_retries(self):
        client = FakeClient("http://127.0.0.1:1", timeout=0.3)
        with pytest.raises(LLMConnectionError, match="connect"):
            client._generate_response_direct(
                "m", [{"role": "user", "content": "x"}], retries=1
            )

    def test_format_json_option(self, httpserver: HTTPServer):
        """Ensure format_json option is passed in payload."""
        received = {}

        def handler(request):
            received.update(json.loads(request.data))
            return Response(
                json.dumps({"message": {"content": '{"key": "value"}'}}),
                content_type="application/json",
            )

        httpserver.expect_request("/api/chat", method="POST").respond_with_handler(handler)
        client = FakeClient(httpserver.url_for("").rstrip("/"))
        opts = GenerationOptions(format_json=True)
        client._generate_response_direct(
            "m", [{"role": "user", "content": "x"}], options=opts
        )
        assert received.get("format") == "json"
