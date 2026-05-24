"""Tests for infrastructure.llm.utils.server — coverage using pytest-httpserver."""

from pytest_httpserver import HTTPServer

from infrastructure.llm.utils.server import (
    is_ollama_running,
    ensure_ollama_ready,
)


class TestIsOllamaRunning:
    def test_server_running(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": [{"name": "llama3:latest"}]}
        )
        assert is_ollama_running(httpserver.url_for("")) is True

    def test_server_not_running(self):
        assert is_ollama_running("http://localhost:1", timeout=0.5) is False

    def test_server_error_status(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_data("error", status=500)
        assert is_ollama_running(httpserver.url_for("")) is False

    def test_server_connection_refused(self):
        # Use a port that's definitely not listening
        assert is_ollama_running("http://127.0.0.1:1", timeout=0.5) is False


class TestEnsureOllamaReady:
    def test_ready_with_models(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": [{"name": "llama3:latest", "size": 1000}]}
        )
        assert ensure_ollama_ready(httpserver.url_for(""), auto_start=False) is True

    def test_not_running_no_auto_start(self):
        assert ensure_ollama_ready("http://localhost:1", auto_start=False) is False

    def test_running_no_models(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        assert ensure_ollama_ready(httpserver.url_for(""), auto_start=False) is False

    def test_many_models_logged(self, httpserver: HTTPServer):
        models = [{"name": f"model{i}:latest", "size": 1000} for i in range(8)]
        httpserver.expect_request("/api/tags").respond_with_json({"models": models})
        assert ensure_ollama_ready(httpserver.url_for(""), auto_start=False) is True
