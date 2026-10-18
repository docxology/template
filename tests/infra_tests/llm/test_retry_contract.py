"""Actual loopback HTTP attempts and explicit model-context warm-up."""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from infrastructure.core.exceptions import LLMConnectionError
from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig
from infrastructure.llm.utils.models import preload_model


@pytest.fixture
def owned_http_endpoint():
    """Own the actual socket, request history and cleanup; replace no client code."""
    state = {"requests": [], "failures": 1}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append((self.path, payload))
            if state["failures"]:
                state["failures"] -= 1
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            body = json.dumps(dict(message={"content": "actual response"}, done=True)).encode() + b"\n"
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson" if payload.get("stream") else "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()


@pytest.mark.parametrize("mode", ["blocking", "streaming", "short-stream", "long-stream"])
@pytest.mark.parametrize("profile", ["default", "fail-fast", "explicit-override"])
def test_actual_http_attempt_count_obeys_configuration_and_explicit_override(owned_http_endpoint, mode, profile):
    endpoint, state = owned_http_endpoint
    config = OllamaClientConfig(
        base_url=endpoint,
        default_model="owned",
        fallback_models=[],
        timeout=1,
        request_retries=1 if profile == "default" else 0,
    )
    client = LLMClient(config)

    def perform():
        override = 1 if profile == "explicit-override" else None
        if mode != "blocking":
            method = {
                "streaming": client.stream_query,
                "short-stream": client.stream_short,
                "long-stream": client.stream_long,
            }[mode]
            return "".join(method("test", retries=override, log_progress=False))
        if override is not None:
            return client._generate_response_direct("owned", [{"role": "user", "content": "test"}], retries=override)
        return client.query("test")

    if profile == "fail-fast":
        with pytest.raises(LLMConnectionError):
            perform()
        assert len(state["requests"]) == 1
    else:
        assert perform() == "actual response"
        assert len(state["requests"]) == 2
    assert all(path == "/api/chat" and payload["model"] == "owned" for path, payload in state["requests"])


def test_preload_explicit_context_performs_actual_matching_generate_request(owned_http_endpoint):
    endpoint, state = owned_http_endpoint
    state["failures"] = 0
    assert preload_model("owned", base_url=endpoint, timeout=1, retries=0, context_window=4096) == (True, None)
    assert len(state["requests"]) == 1
    path, payload = state["requests"][0]
    assert path == "/api/generate" and payload["model"] == "owned"
    assert payload["options"] == {"num_predict": 1, "num_ctx": 4096}


@pytest.mark.parametrize("value", [-1, True, 1.5, "1"])
def test_invalid_retry_count_refuses_before_any_http(value):
    with pytest.raises(ValueError, match="non-negative integer"):
        OllamaClientConfig(request_retries=value)


@pytest.mark.parametrize("value", [0, -1, True, 4096.0])
def test_invalid_preload_context_refuses_before_any_http(value):
    with pytest.raises(ValueError, match="positive integer"):
        preload_model("owned", context_window=value)
