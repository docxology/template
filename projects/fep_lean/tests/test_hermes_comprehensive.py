"""Comprehensive tests for llm.hermes — zero mock, real network/os testing."""

from __future__ import annotations

import http.server
import os
import socket
import threading
import urllib.error
from pathlib import Path

import pytest

from llm.hermes import (
    HermesAPIError,
    HermesConfig,
    HermesExplainer,
    HermesResult,
    _extract_explanation,
    _extract_lean_block,
    _hermes_network_max_retries,
)

PROJ = Path(__file__).resolve().parent.parent
# _LIVE_TESTS_ENABLED retained for future live-API TestCallAPI variants;
# the current TestCallAPI tests use local loopback servers and never skip.
_FEP_LEAN_LIVE_VAR = os.environ.get("FEP_LEAN_LIVE_TESTS", "").lower()
_HAS_API_KEY = bool(
    os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
)
_LIVE_TESTS_ENABLED = (
    _FEP_LEAN_LIVE_VAR in ("1", "true", "yes")
    or (_HAS_API_KEY and _FEP_LEAN_LIVE_VAR not in ("0", "false", "no"))
)


# ── Local HTTP server helpers (no external deps, no mocks) ───────────────────

class _FixedStatusHandler(http.server.BaseHTTPRequestHandler):
    """Local HTTP handler that replies with a configured status code for any POST.

    Sends a complete HTTP response including ``Content-Length`` so that
    ``urllib`` can fully read the error body before the connection closes.
    Without ``Content-Length``, urllib may see a ``ConnectionResetError``
    while trying to read the body via ``HTTPError.read()``.
    """

    _status: int = 404
    _body: bytes = b"test error response"

    def do_POST(self) -> None:  # noqa: N802
        body = self._body
        self.send_response(self._status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def log_message(self, *args: object) -> None:  # suppress server output
        pass


def _make_handler(status: int) -> type:
    """Return a handler subclass pre-configured to return *status*."""
    return type(f"_Handler{status}", (_FixedStatusHandler,), {"_status": status})


class _SlowResponseHandler(http.server.BaseHTTPRequestHandler):
    """Reply 200 with ``Content-Length`` set, but trickle bytes slowly.

    Each ``write`` is paced under the per-op socket timeout, so urllib's own
    ``timeout`` argument never fires; only a hard wall-clock deadline can
    bound this. Used to verify that ``_make_request`` aborts via its
    worker-thread ``join(timeout=...)`` and surfaces a transient
    ``HermesAPIError`` instead of hanging.
    """

    _delay_per_byte: float = 0.5  # 500 ms between bytes
    _total_bytes: int = 64

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(self._total_bytes))
        self.end_headers()
        for _ in range(self._total_bytes):
            try:
                self.wfile.write(b"x")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return  # client gave up — expected when the deadline fires
            import time as _t
            _t.sleep(self._delay_per_byte)

    def log_message(self, *args: object) -> None:
        pass


class _TruncatedContentHandler(http.server.BaseHTTPRequestHandler):
    """Reply 200 with ``Content-Length`` larger than the bytes actually sent.

    ``urllib`` keeps reading until *length* bytes are received; the server closes
    early so the client raises ``http.client.IncompleteRead`` — the same class
    of failure as chunked/streaming drops from upstream APIs.
    """

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        payload = b'{"partial":'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "4096")
        self.end_headers()
        self.wfile.write(payload)
        self.wfile.flush()

    def log_message(self, *args: object) -> None:  # suppress server output
        pass


def _start_local_server(status: int) -> tuple[http.server.HTTPServer, int]:
    """Bind an ephemeral-port HTTPServer in a daemon thread; return (server, port)."""
    srv = http.server.HTTPServer(("127.0.0.1", 0), _make_handler(status))
    port: int = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def _start_truncated_body_server() -> tuple[http.server.HTTPServer, int]:
    """HTTPServer that returns a truncated 200 JSON body (IncompleteRead on client)."""
    srv = http.server.HTTPServer(("127.0.0.1", 0), _TruncatedContentHandler)
    port: int = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def _start_slow_response_server() -> tuple[http.server.ThreadingHTTPServer, int]:
    """HTTPServer that drips bytes slowly so only a wall-clock deadline can bound it.

    Uses ``ThreadingHTTPServer`` with ``daemon_threads=True`` so the in-flight
    slow handler does not block ``server.shutdown()`` in the test teardown.
    """
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _SlowResponseHandler)
    srv.daemon_threads = True
    port: int = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def _free_port() -> int:
    """Return an ephemeral port number that has nothing listening on it.

    Binds a socket to port 0 (kernel assigns a free port), records the port,
    then closes the socket — leaving the port closed/refused but known.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

class TestLoadGaussDotenv:
    """Test HermesConfig._load_gauss_dotenv."""

    def test_loads_keys_from_dotenv(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text("FOO_KEY=bar123\nBAZ=qux\n", encoding="utf-8")
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.delenv("FOO_KEY", raising=False)
        monkeypatch.delenv("BAZ", raising=False)

        HermesConfig._load_gauss_dotenv()
        assert os.environ["FOO_KEY"] == "bar123"
        assert os.environ["BAZ"] == "qux"

    def test_does_not_overwrite_existing_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text("EXISTING_VAR=from_file\n", encoding="utf-8")
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.setenv("EXISTING_VAR", "original")

        HermesConfig._load_gauss_dotenv()
        assert os.environ["EXISTING_VAR"] == "original"

    def test_handles_missing_dotenv(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        HermesConfig._load_gauss_dotenv()  # should not raise

    def test_handles_comments_and_blank_lines(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text("# comment\n\nVALID=yes\n  \n", encoding="utf-8")
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.delenv("VALID", raising=False)

        HermesConfig._load_gauss_dotenv()
        assert os.environ["VALID"] == "yes"

    def test_strips_quotes_from_values(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text("Q1='single'\nQ2=\"double\"\n", encoding="utf-8")
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.delenv("Q1", raising=False)
        monkeypatch.delenv("Q2", raising=False)

        HermesConfig._load_gauss_dotenv()
        assert os.environ["Q1"] == "single"
        assert os.environ["Q2"] == "double"

    def test_handles_read_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        dotenv = tmp_path / ".env"
        dotenv.write_text("X=Y\n", encoding="utf-8")
        
        # Genuine read error via filesystem permissions
        dotenv.chmod(0o000)
        HermesConfig._load_gauss_dotenv()  # should not raise
        dotenv.chmod(0o644)


class TestKeyAffinityValidation:
    """Test that API key ↔ endpoint mismatches are caught."""

    def test_anthropic_key_to_openrouter_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")

        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.enabled is False
        assert cfg.api_key == "sk-ant-fake-key"

    def test_openrouter_key_to_anthropic_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-fake-or-key")
        monkeypatch.setenv("HERMES_API_BASE", "https://api.anthropic.com/v1")
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")

        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.enabled is False

    def test_correct_key_stays_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-correct-key")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")

        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.enabled is True
        assert cfg.api_key == "sk-or-v1-correct-key"


class TestCallAPI:
    """Test HermesExplainer._call_api using genuine local OS/network operations.

    Tests use real sockets on loopback — no external network, no mocks,
    no FEP_LEAN_LIVE_TESTS gate.  They exercise ``urllib`` exception branches
    inside ``_call_api``:

    * ``urllib.error.HTTPError`` (non-2xx response) → ``HermesAPIError(status_code=N, transient=False)``
    * ``urllib.error.URLError`` (connection refused) → ``HermesAPIError(..., transient=True)``
    * Truncated ``Content-Length`` / ``IncompleteRead`` → ``HermesAPIError(..., transient=True)``

    Implementation details
    ----------------------
    * ``test_call_api_http_error`` spins up a daemon ``HTTPServer`` on an
      ephemeral loopback port that returns a hard-coded 404 for any POST.
      The server thread is cleaned up via ``server.shutdown()`` in the
      ``finally`` block so it does not linger across tests.

    * ``test_call_api_url_error`` allocates an ephemeral port via a socket
      bound to port 0, reads the OS-assigned port number, then closes the
      socket *without* starting a listener.  Any connection attempt
      immediately receives ECONNREFUSED, which ``urllib`` wraps in
      ``urllib.error.URLError`` — exactly the path we want to exercise.
      The timeout is set to 1 s so the test is fast even if the OS queues
      the refused connection.
    """

    def test_call_api_http_error(self) -> None:
        """_call_api raises HermesAPIError(status_code=404) on a 404 response.

        Uses a local daemon HTTPServer (no external network).
        """
        server, port = _start_local_server(404)
        try:
            cfg = HermesConfig(
                enabled=True,
                api_key="sk-or-test",
                base_url=f"http://127.0.0.1:{port}",
            )
            h = HermesExplainer(cfg)
            with pytest.raises(HermesAPIError) as exc_info:
                h._call_api([{"role": "user", "content": "hi"}], "fake-model")
            assert exc_info.value.status_code == 404
            assert exc_info.value.transient is False
        finally:
            server.shutdown()

    def test_call_api_url_error(self) -> None:
        """_call_api raises HermesAPIError("Network error: …") on connection refused.

        Binds a socket to get a free port number, closes it (leaving nothing
        listening), then points HermesExplainer at that port — guaranteeing
        ECONNREFUSED without touching external DNS or the network.
        """
        refused_port = _free_port()
        cfg = HermesConfig(
            enabled=True,
            api_key="sk-or-test",
            base_url=f"http://127.0.0.1:{refused_port}",
            timeout_s=1,
        )
        h = HermesExplainer(cfg)
        with pytest.raises(HermesAPIError) as exc_info:
            h._call_api([{"role": "user", "content": "hi"}], "fake-model")
        assert "Network error" in str(exc_info.value)
        assert exc_info.value.transient is True

    def test_call_api_truncated_body_raises_transient_hermes_api_error(self) -> None:
        """_call_api maps IncompleteRead-style failures to transient HermesAPIError."""
        server, port = _start_truncated_body_server()
        try:
            cfg = HermesConfig(
                enabled=True,
                api_key="sk-or-test",
                base_url=f"http://127.0.0.1:{port}",
                timeout_s=5,
            )
            h = HermesExplainer(cfg)
            with pytest.raises(HermesAPIError) as exc_info:
                h._call_api([{"role": "user", "content": "hi"}], "fake-model")
            assert exc_info.value.status_code is None
            assert exc_info.value.transient is True
            assert "HTTP transport error" in str(exc_info.value) or "Connection error" in str(
                exc_info.value
            )
        finally:
            server.shutdown()

    def test_call_api_wall_clock_deadline_aborts_slow_stream(self) -> None:
        """_make_request enforces a hard wall-clock deadline on slow responses.

        urllib's per-op ``timeout`` argument does not bound total wall time
        when a server trickles bytes within the timeout window. We observed
        a 150 s ``timeout_s`` taking 10+ minutes in production. The
        worker-thread + ``join(timeout=...)`` guard in ``_make_request``
        must abort the request and raise a transient ``HermesAPIError``
        within ``timeout_s`` seconds.
        """
        server, port = _start_slow_response_server()
        deadline_s = 2  # ~32 s of trickle would otherwise be needed (64B * 0.5s)
        try:
            cfg = HermesConfig(
                enabled=True,
                api_key="sk-or-test",
                base_url=f"http://127.0.0.1:{port}",
                timeout_s=deadline_s,
            )
            h = HermesExplainer(cfg)
            import time as _t
            t0 = _t.monotonic()
            with pytest.raises(HermesAPIError) as exc_info:
                h._call_api([{"role": "user", "content": "hi"}], "fake-model")
            elapsed = _t.monotonic() - t0
            # Must give up within roughly one deadline (allow 2x slack for
            # thread scheduling + handshake).
            assert elapsed < 2 * deadline_s + 1, (
                f"deadline not enforced: elapsed={elapsed:.2f}s "
                f"(expected < {2 * deadline_s + 1}s)"
            )
            assert exc_info.value.transient is True
            assert "Wall-clock timeout" in str(exc_info.value)
        finally:
            server.shutdown()


class TestHermesNetworkMaxRetriesEnv:
    """``HERMES_NETWORK_MAX_RETRIES`` parsing."""

    def test_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HERMES_NETWORK_MAX_RETRIES", raising=False)
        assert _hermes_network_max_retries() == 2

    def test_numeric_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HERMES_NETWORK_MAX_RETRIES", "5")
        assert _hermes_network_max_retries() == 5


class TestTextExtraction:
    """Test _extract_lean_block and _extract_explanation."""

    def test_extract_lean_block_standard(self) -> None:
        content = "Some text\n```lean\ntheorem foo : True := trivial\n```\nMore text"
        assert "theorem foo" in _extract_lean_block(content)

    def test_extract_lean_block_fallback(self) -> None:
        content = "Some text\n```\ntheorem bar : True := trivial\n```\nMore text"
        assert "theorem bar" in _extract_lean_block(content)

    def test_extract_lean_block_none(self) -> None:
        assert _extract_lean_block("no code here") == ""

    def test_extract_explanation(self) -> None:
        content = "First paragraph.\n\n```lean\ncode\n```\n\nSecond paragraph."
        result = _extract_explanation(content)
        assert "First paragraph." in result
        assert "code" not in result

    def test_extract_explanation_headers_skipped(self) -> None:
        content = "# Header\n\nReal content.\n\n```lean\nx\n```"
        result = _extract_explanation(content)
        assert "Header" not in result
        assert "Real content" in result


class TestHermesConfigMisc:
    """Test HermesConfig helper methods."""

    def test_is_reasoning_model(self) -> None:
        cfg = HermesConfig(model="nvidia/nemotron-3-super-120b-a12b:free")
        assert cfg.is_reasoning_model() is True
        cfg2 = HermesConfig(model="some-other-model")
        assert cfg2.is_reasoning_model() is False

    def test_effective_max_tokens(self) -> None:
        cfg = HermesConfig(model="nvidia/nemotron-3-super-120b-a12b:free", max_tokens=100, reasoning_max_tokens=9999)
        assert cfg.effective_max_tokens() == 9999
        cfg2 = HermesConfig(model="other", max_tokens=100, reasoning_max_tokens=9999)
        assert cfg2.effective_max_tokens() == 100

    def test_effective_timeout(self) -> None:
        cfg = HermesConfig(model="nvidia/nemotron-3-super-120b-a12b:free", timeout_s=30, reasoning_timeout_s=600)
        assert cfg.effective_timeout() == 600

    def test_hermes_result_as_dict(self) -> None:
        r = HermesResult(success=True, model_used="m", topic_id="t", reasoning="x" * 3000)
        d = r.as_dict()
        assert d["success"] is True
        assert len(d["reasoning"]) <= 2000

    def test_build_model_chain_openrouter(self) -> None:
        cfg = HermesConfig(model="primary-model", base_url="https://openrouter.ai/api/v1")
        h = HermesExplainer(cfg)
        chain = h._build_model_chain()
        assert chain[0] == "primary-model"
        assert len(chain) > 1

    def test_build_model_chain_non_openrouter(self) -> None:
        cfg = HermesConfig(model="primary-only", base_url="https://custom.api.com/v1")
        h = HermesExplainer(cfg)
        chain = h._build_model_chain()
        assert chain == ["primary-only"]


class TestFromSettingsEdgeCases:
    """Cover HermesConfig.from_settings branches: malformed YAML, API key priority, is_live."""

    def test_malformed_settings_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover lines 178-179: YAML parse exception branch."""
        bad_yaml = tmp_path / "settings.yaml"
        bad_yaml.write_text("hermes: { bad: [ yaml }", encoding="utf-8")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        cfg = HermesConfig.from_settings(settings_path=bad_yaml)
        # Should fall back to defaults without crashing
        assert cfg.max_tokens == 16384

    def test_api_key_anthropic_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover lines 205-207: ANTHROPIC_API_KEY used when OPENROUTER absent."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("HERMES_API_BASE", "https://api.anthropic.com/v1")
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.api_key == "sk-ant-test123"

    def test_api_key_openai_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover lines 208-210: OPENAI_API_KEY used when others absent."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test456")
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.api_key == "sk-openai-test456"

    def test_api_key_from_settings_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover lines 212-214: api_key from settings.yaml when no env vars."""
        yaml_file = tmp_path / "settings.yaml"
        yaml_file.write_text("hermes:\n  api_key: sk-yaml-key789\n", encoding="utf-8")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        cfg = HermesConfig.from_settings(settings_path=yaml_file)
        assert cfg.api_key == "sk-yaml-key789"

    def test_no_api_key_anywhere(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover line 215-216: empty api_key when none set."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.api_key == ""
        assert cfg.enabled is True  # enabled but no key


class TestIsLiveProperty:
    """Cover line 308: HermesExplainer.is_live property."""

    def test_is_live_enabled_with_key(self) -> None:
        cfg = HermesConfig(enabled=True, api_key="sk-test")
        assert HermesExplainer(cfg).is_live is True

    def test_is_live_enabled_no_key(self) -> None:
        cfg = HermesConfig(enabled=True, api_key="")
        assert HermesExplainer(cfg).is_live is False

    def test_is_live_disabled_with_key(self) -> None:
        cfg = HermesConfig(enabled=False, api_key="sk-test")
        assert HermesExplainer(cfg).is_live is False

    def test_is_live_disabled_no_key(self) -> None:
        cfg = HermesConfig(enabled=False, api_key="")
        assert HermesExplainer(cfg).is_live is False


class TestParseResponse:
    """Cover lines 464-498: HermesExplainer._parse_response edge cases."""

    def _make_explainer(self) -> HermesExplainer:
        return HermesExplainer(HermesConfig(enabled=False))

    def test_empty_choices(self) -> None:
        h = self._make_explainer()
        r = h._parse_response({"choices": []}, "model-x", 1.0, "fep-001")
        assert r.success is False
        assert "empty choices" in r.error

    def test_missing_choices_key(self) -> None:
        h = self._make_explainer()
        r = h._parse_response({}, "model-x", 1.0, "fep-001")
        assert r.success is False

    def test_valid_response_with_lean_block(self) -> None:
        h = self._make_explainer()
        raw = {
            "choices": [{"message": {"content": "Explanation.\n\n```lean\ntheorem x : True := trivial\n```"}}],
            "usage": {"completion_tokens": 100, "prompt_tokens": 50},
        }
        r = h._parse_response(raw, "model-y", 2.5, "fep-002")
        assert r.success is True
        assert r.model_used == "model-y"
        assert "theorem x" in r.refined_lean_sketch
        assert r.tokens_used == 150
        assert r.duration_s == 2.5
        assert r.topic_id == "fep-002"

    def test_think_tags_extracted_as_reasoning(self) -> None:
        h = self._make_explainer()
        raw = {
            "choices": [{"message": {"content": "Before<think>Deep reasoning here</think>After text"}}],
            "usage": {"completion_tokens": 50, "prompt_tokens": 20},
        }
        r = h._parse_response(raw, "model-z", 1.0, "fep-003")
        assert r.reasoning == "Deep reasoning here"
        assert "<think>" not in r.explanation
        assert r.tokens_used == 70

    def test_reasoning_field_direct(self) -> None:
        h = self._make_explainer()
        raw = {
            "choices": [{"message": {"content": "content", "reasoning": "direct reasoning"}}],
            "usage": {},
        }
        r = h._parse_response(raw, "model-r", 0.5, "fep-004")
        assert r.reasoning == "direct reasoning"
        assert r.tokens_used == 0

    def test_empty_content_returns_failure(self) -> None:
        h = self._make_explainer()
        raw = {
            "choices": [{"message": {"content": ""}}],
            "usage": {"completion_tokens": 10, "prompt_tokens": 5},
        }
        r = h._parse_response(raw, "model-e", 0.1, "fep-005")
        assert r.success is False  # bool("") is False
