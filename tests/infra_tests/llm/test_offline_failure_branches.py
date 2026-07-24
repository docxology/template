"""Real-behavior tests for offline LLM/API failure branches.

Exercises the real error paths in ``infrastructure.llm.core._connection``,
``infrastructure.llm.utils.server``, and ``infrastructure.llm.core.client``
when Ollama is absent or unreachable. No mocks: real closed ports
(``127.0.0.1:1``), real subprocess calls, real ``shutil.which`` lookups.

All tests are marked ``no_patch_llm_client`` so the LLM conftest's
auto-redirect to the pytest_httpserver stub does not interfere with the
dead-port connections we need to exercise.
"""

from __future__ import annotations

import shutil
import socket
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.exceptions import LLMConnectionError
from infrastructure.llm.core._connection import _ConnectionMixin
from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig
from infrastructure.llm.utils.server import (
    ensure_ollama_ready,
    is_ollama_running,
    pull_ollama_model,
    start_ollama_server,
)

# A port where nothing listens — connection refused is the expected outcome.
DEAD_HOST = "http://127.0.0.1:1"
# A secondary dead port for variety.
DEAD_HOST_ALT = "http://127.0.0.1:2"

pytestmark = pytest.mark.no_patch_llm_client


# --- helpers ----------------------------------------------------------------


class _FakeClient(_ConnectionMixin):
    """Minimal client exercising _ConnectionMixin against a dead URL."""

    def __init__(self, base_url: str, timeout: float = 1.0):
        self.config = OllamaClientConfig(base_url=base_url, timeout=timeout)


def _find_open_port() -> int:
    """Bind a temporary socket to find a guaranteed-free port, then close it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# --- is_ollama_running: connection refused ---------------------------------


def test_is_ollama_running_dead_port_returns_false() -> None:
    """is_ollama_running against a dead port returns False (ConnectionError)."""
    assert is_ollama_running(DEAD_HOST, timeout=0.5) is False


def test_is_ollama_running_alt_dead_port_returns_false() -> None:
    """A different dead port also returns False."""
    assert is_ollama_running(DEAD_HOST_ALT, timeout=0.5) is False


def test_is_ollama_running_garbage_url_returns_false() -> None:
    """A malformed URL does not crash — returns False via RequestException."""
    assert is_ollama_running("not-a-url", timeout=0.5) is False


# --- ensure_ollama_ready: offline with auto_start disabled ------------------


def test_ensure_ollama_ready_dead_port_no_auto_start() -> None:
    """ensure_ollama_ready returns False when the daemon is down and no auto-start."""
    assert ensure_ollama_ready(DEAD_HOST, auto_start=False) is False


def test_ensure_ollama_ready_dead_port_auto_start_fails() -> None:
    """ensure_ollama_ready returns False when the daemon is down and auto-start fails.

    Auto-start will attempt to find ``ollama`` in PATH and start it. If ollama
    is not installed, ``start_ollama_server`` returns False and
    ``ensure_ollama_ready`` returns False.
    """
    # This exercises the real start_ollama_server path; if ollama is not
    # installed (the common case in CI), it returns False quickly. If it IS
    # installed, it will try to start and then check the dead port — which will
    # still fail because we point at a dead URL.
    result = ensure_ollama_ready(DEAD_HOST, auto_start=True)
    assert result is False


# --- start_ollama_server: absent binary -------------------------------------


def test_start_ollama_server_returns_false_when_binary_absent(tmp_path: Path, monkeypatch) -> None:
    """start_ollama_server returns False when ollama is not in PATH."""
    # Clear PATH so shutil.which("ollama") returns None.
    monkeypatch.setenv("PATH", str(tmp_path))
    assert start_ollama_server(wait_seconds=0.1, max_retries=0) is False


# --- pull_ollama_model: absent binary (real shutil.which) -------------------


def test_pull_ollama_model_absent_binary_real_which(tmp_path: Path, monkeypatch) -> None:
    """pull_ollama_model returns (False, msg) when ollama is not in PATH.

    Uses a real empty PATH so ``shutil.which`` genuinely finds nothing.
    No mock framework involved.
    """
    monkeypatch.setenv("PATH", str(tmp_path))
    ok, err = pull_ollama_model("smollm2", timeout=1.0)
    assert ok is False
    assert err is not None
    assert "PATH" in err


def test_pull_ollama_model_absent_binary_injected_which() -> None:
    """pull_ollama_model with an injectable which returning None reports missing.

    This uses the function's optional ``which`` parameter (designed for tests)
    rather than patching — no mock framework.
    """
    ok, err = pull_ollama_model("smollm2", timeout=1.0, which=lambda _cmd: None)
    assert ok is False
    assert err is not None
    assert "PATH" in err


def test_pull_ollama_model_subprocess_timeout_real_stub(tmp_path: Path) -> None:
    """pull_ollama_model with a real stub that sleeps longer than the timeout.

    Uses a real executable script (no mocking of subprocess.run).
    """
    stub = tmp_path / "ollama"
    stub.write_text("#!/bin/sh\nsleep 30\nexit 0\n", encoding="utf-8")
    stub.chmod(0o755)

    ok, err = pull_ollama_model(
        "smollm2",
        timeout=0.3,
        which=lambda cmd: str(stub) if cmd == "ollama" else None,
    )
    assert ok is False
    assert err is not None
    assert "timed out" in err.lower()


def test_pull_ollama_model_nonzero_exit_real_stub(tmp_path: Path) -> None:
    """pull_ollama_model with a real stub that exits non-zero reports the error."""
    stub = tmp_path / "ollama"
    stub.write_text("#!/bin/sh\necho 'network error' >&2\nexit 1\n", encoding="utf-8")
    stub.chmod(0o755)

    ok, err = pull_ollama_model(
        "smollm2",
        timeout=5.0,
        which=lambda cmd: str(stub) if cmd == "ollama" else None,
    )
    assert ok is False
    assert err is not None
    assert "network error" in err


def test_pull_ollama_model_success_real_stub(tmp_path: Path) -> None:
    """pull_ollama_model with a real stub that exits 0 succeeds."""
    stub = tmp_path / "ollama"
    stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stub.chmod(0o755)

    ok, err = pull_ollama_model(
        "smollm2",
        timeout=5.0,
        which=lambda cmd: str(stub) if cmd == "ollama" else None,
    )
    assert ok is True
    assert err is None


# --- _ConnectionMixin: connection refused on dead port ----------------------


def test_check_connection_dead_port_returns_false() -> None:
    """check_connection against a dead port returns False."""
    client = _FakeClient(DEAD_HOST, timeout=0.5)
    assert client.check_connection(timeout=0.5) is False


def test_check_connection_with_reason_dead_port() -> None:
    """check_connection_with_reason against a dead port returns (False, reason)."""
    client = _FakeClient(DEAD_HOST, timeout=0.5)
    ok, reason = client.check_connection_with_reason(timeout=0.5)
    assert ok is False
    assert reason is not None
    assert "Connection" in reason or "error" in reason.lower()


def test_get_available_models_dead_port_returns_fallback() -> None:
    """get_available_models against a dead port returns the fallback list."""
    client = _FakeClient(DEAD_HOST, timeout=0.5)
    models = client.get_available_models()
    assert isinstance(models, list)
    # Fallback models are never empty — at least one entry.
    assert len(models) > 0
    # The fallback list comes from config.fallback_models.
    assert set(models) == set(client.config.fallback_models)


# --- _generate_response_direct: connection refused raises LLMConnectionError


def test_generate_response_direct_dead_port_raises() -> None:
    """_generate_response_direct against a dead port raises LLMConnectionError."""
    client = _FakeClient(DEAD_HOST, timeout=0.3)
    with pytest.raises(LLMConnectionError, match="connect"):
        client._generate_response_direct("testmodel", [{"role": "user", "content": "hi"}])


def test_generate_response_direct_dead_port_with_retries_raises() -> None:
    """_generate_response_direct with retries still raises after exhausting them."""
    client = _FakeClient(DEAD_HOST, timeout=0.3)
    with pytest.raises(LLMConnectionError, match="connect"):
        client._generate_response_direct("testmodel", [{"role": "user", "content": "hi"}], retries=2)


# --- LLMClient.query: offline path raises after fallbacks exhausted ---------


def test_llm_client_query_dead_port_raises_after_fallbacks() -> None:
    """LLMClient.query against a dead port raises LLMConnectionError.

    The primary model fails, all fallback models fail, and the error is
    re-raised. Uses a real dead URL with a short timeout.
    """
    config = OllamaClientConfig(
        base_url=DEAD_HOST,
        timeout=0.3,
        default_model="testmodel",
        fallback_models=["fallback1", "fallback2"],
        auto_inject_system_prompt=False,
    )
    client = LLMClient(config)
    with pytest.raises(LLMConnectionError):
        client.query("test prompt")


def test_llm_client_query_raw_dead_port_raises() -> None:
    """LLMClient.query_raw against a dead port raises LLMConnectionError.

    Requires the raw-query bypass caller (registered in bypass.py for tests).
    """
    config = OllamaClientConfig(
        base_url=DEAD_HOST,
        timeout=0.3,
        default_model="testmodel",
        auto_inject_system_prompt=False,
    )
    client = LLMClient(config)
    with pytest.raises(LLMConnectionError):
        client.query_raw(
            "raw prompt",
            bypass_caller="tests.infra_tests.llm",
            bypass_reason="offline dead-port coverage of raw protocol",
        )


# --- config from_env: offline does not crash --------------------------------


def test_config_from_env_with_dead_host(monkeypatch) -> None:
    """OllamaClientConfig.from_env reads OLLAMA_HOST without requiring a server."""
    monkeypatch.setenv("OLLAMA_HOST", DEAD_HOST)
    config = OllamaClientConfig.from_env()
    assert config.base_url == DEAD_HOST


def test_config_from_env_defaults_when_no_env(monkeypatch) -> None:
    """from_env falls back to default base_url when OLLAMA_HOST is unset."""
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    config = OllamaClientConfig.from_env()
    assert config.base_url == "http://localhost:11434"


# --- LLMClient init: does not connect to server ----------------------------


def test_llm_client_init_does_not_require_server(monkeypatch) -> None:
    """LLMClient construction succeeds even with a dead base_url.

    The client only connects on query, not on init.
    """
    monkeypatch.setenv("OLLAMA_HOST", DEAD_HOST)
    config = OllamaClientConfig.from_env()
    config.auto_inject_system_prompt = False
    client = LLMClient(config)
    assert client.config.base_url == DEAD_HOST
    # Context should have no messages if auto_inject is off.
    assert client.context.messages == []


def test_llm_client_reset_does_not_require_server() -> None:
    """LLMClient.reset() works without a server connection."""
    config = OllamaClientConfig(base_url=DEAD_HOST, timeout=0.3, auto_inject_system_prompt=False)
    client = LLMClient(config)
    client.reset()  # should not raise
    assert client.context.messages == []


def test_llm_client_set_system_prompt_does_not_require_server() -> None:
    """set_system_prompt works without a server connection.

    With ``auto_inject_system_prompt=False`` the prompt is stored on the config
    but not injected into the context (the reset clears messages and does not
    re-inject). With ``auto_inject=True`` the system message appears in context.
    """
    config = OllamaClientConfig(base_url=DEAD_HOST, timeout=0.3, auto_inject_system_prompt=True)
    client = LLMClient(config)
    client.set_system_prompt("You are a test assistant.")
    assert client.config.system_prompt == "You are a test assistant."
    # System prompt should be injected into context after reset (auto_inject on).
    assert client.context.messages[0].role == "system"
    assert client.context.messages[0].content == "You are a test assistant."


# --- real subprocess for ollama binary absence ------------------------------


def test_shutil_which_ollama_returns_none_in_empty_path(tmp_path: Path, monkeypatch) -> None:
    """Real shutil.which confirms ollama is absent from an empty PATH."""
    monkeypatch.setenv("PATH", str(tmp_path))
    assert shutil.which("ollama") is None


def test_real_subprocess_true_exits_zero() -> None:
    """A real subprocess call to ``true`` exits 0 (sanity check)."""
    result = subprocess.run(["true"], capture_output=True, check=False, timeout=5)
    assert result.returncode == 0


def test_real_subprocess_false_exits_one() -> None:
    """A real subprocess call to ``false`` exits 1 (sanity check)."""
    result = subprocess.run(["false"], capture_output=True, check=False, timeout=5)
    assert result.returncode == 1
