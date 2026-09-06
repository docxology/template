import os
import threading

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig

from tests.infra_tests.llm.ollama_stub_server import build_chat_handler


@pytest.fixture
def ollama_test_server():
    """Local HTTP test server mimicking Ollama API endpoints (real HTTP, no mocks)."""
    server = HTTPServer()
    server.start()

    server.expect_request("/api/chat", method="POST").respond_with_handler(build_chat_handler())

    # Mock /api/tags endpoint (model list)
    server.expect_request("/api/tags").respond_with_json(
        {
            "models": [
                {"name": "gemma3:4b", "size": "4.7GB"},
                {"name": "llama3:8b", "size": "4.7GB"},
            ]
        }
    )

    try:
        yield server
    finally:
        # Under heavy load (e.g., coverage runs) server shutdown can occasionally
        # block long enough to trip the repo-wide pytest-timeout. Make teardown
        # best-effort and bounded.
        stopper = threading.Thread(target=server.stop, daemon=True)
        stopper.start()
        stopper.join(timeout=2.0)


@pytest.fixture
def test_config(ollama_test_server):
    """Create a real OllamaClientConfig pointing to test server."""
    config = OllamaClientConfig(auto_inject_system_prompt=False)
    config.base_url = ollama_test_server.url_for("/")
    config.default_model = "llama3:latest"
    config.fallback_models = ["llama3:8b"]
    return config


@pytest.fixture
def test_client(test_config):
    """Create a real LLMClient using test server."""
    return LLMClient(test_config)


@pytest.fixture
def default_config(request):
    """Create a default OllamaClientConfig for testing with auto_inject disabled.

    Pins ``default_model`` to the discovered small/fast model for
    ``requires_ollama`` integration tests, so they query a model that is
    actually pulled (the bare ``OllamaClientConfig`` default is ``gemma3:4b``,
    which a contributor may not have installed). Pure tests never issue a real
    query, so probing a daemon during their setup only adds latency and makes
    the fast tier environment-dependent.
    """
    if request.node.get_closest_marker("requires_ollama") is None:
        return OllamaClientConfig(auto_inject_system_prompt=False)

    from infrastructure.llm.utils.models import select_small_fast_model

    model = select_small_fast_model()
    if model:
        return OllamaClientConfig(auto_inject_system_prompt=False, default_model=model)
    return OllamaClientConfig(auto_inject_system_prompt=False)


@pytest.fixture
def config_with_system_prompt():
    """Create OllamaClientConfig with custom system prompt."""
    return OllamaClientConfig(
        system_prompt="You are a helpful research assistant.",
        auto_inject_system_prompt=True,
    )


@pytest.fixture
def generation_options():
    """Create GenerationOptions for testing."""
    from infrastructure.llm.core.config import GenerationOptions

    return GenerationOptions(temperature=0.5, max_tokens=500, seed=42, stop=["END"])


@pytest.fixture
def clean_llm_env(monkeypatch):
    """Clean LLM-related environment variables for testing."""
    # Remove LLM-related env vars
    env_vars_to_remove = ["OLLAMA_HOST", "OLLAMA_MODEL", "LLM_MAX_INPUT_LENGTH"]
    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)
    yield
    # Cleanup happens automatically


@pytest.fixture(autouse=True)
def patch_llm_client_for_tests(request, monkeypatch):
    """Redirect LLMClient to test server via environment variables.

    Sets OLLAMA_HOST to the test server URL so that OllamaClientConfig.from_env()
    naturally discovers the test server. No class patching required —
    fully compliant with the zero-mocks policy.

    The HTTP server is acquired lazily. Most LLM tests exercise configuration or
    context logic and do not need a listening socket; starting one for every
    test made the fast tier pay the cost of a real server even when no request
    could be made. Tests that need the stub request it explicitly through the
    ``ollama_test_server`` fixture, which also makes their network boundary
    visible in the test signature.

    Skips environment redirection if test is marked with ``no_patch_llm_client``
    to allow testing real default configuration.
    """
    # Check if test needs real default behavior
    if request.node.get_closest_marker("no_patch_llm_client"):
        return  # Skip — test will use real default config

    # Do not start pytest-httpserver for pure unit tests. ``fixturenames`` is
    # pytest's resolved fixture closure, so this also handles fixtures that
    # depend on ``ollama_test_server`` without eagerly constructing it here.
    if "ollama_test_server" not in request.fixturenames:
        return

    ollama_test_server = request.getfixturevalue("ollama_test_server")

    # Set environment variables so OllamaClientConfig.from_env() picks up test server
    monkeypatch.setenv("OLLAMA_HOST", ollama_test_server.url_for("/"))
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:4b")
    # Disable auto system prompt injection for predictable test behavior
    monkeypatch.setenv("LLM_AUTO_INJECT_SYSTEM_PROMPT", "false")


# ============================================================================
# Ollama (requires_ollama tests)
# ============================================================================


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _ollama_test_pull_timeout() -> float | None:
    # Default 180s (3 min) — long enough for a small model on a warm cache,
    # short enough that a missing/slow registry fails fast with a clear
    # message pointing to manual `ollama pull <model>`. Override with
    # OLLAMA_TEST_PULL_TIMEOUT (seconds, or "none"/"inf" to disable).
    raw = os.environ.get("OLLAMA_TEST_PULL_TIMEOUT", "180").strip()
    if not raw or raw.lower() in ("none", "inf"):
        return None
    return float(raw)


@pytest.fixture(scope="session")
def ensure_ollama_for_tests():
    """Ensure Ollama is running and a small/fast model is available for tests.

    - Starts Ollama when possible (same as :func:`ensure_ollama_ready`).
    - When ``OLLAMA_SKIP_TEST_MODEL_PULL`` is unset/false, runs ``ollama pull`` for
      ``OLLAMA_TEST_PULL_MODEL`` (default ``smollm2``) if no matching small model is installed.
    - Set ``OLLAMA_SKIP_TEST_MODEL_PULL=1`` for air-gapped runs (install models manually).

    See ``tests/README.md`` for environment variables.
    """
    from infrastructure.core.logging.utils import get_logger
    from infrastructure.llm.utils.ollama import (
        ensure_ollama_ready,
        get_model_names,
        is_ollama_running,
        pull_ollama_model,
        small_fast_preference_matches,
    )

    logger = get_logger(__name__)
    skip_pull = _env_truthy("OLLAMA_SKIP_TEST_MODEL_PULL")
    pull_model = (os.environ.get("OLLAMA_TEST_PULL_MODEL") or "smollm2").strip()
    pull_timeout = _ollama_test_pull_timeout()

    if is_ollama_running():
        logger.info("✓ Ollama server is already running")
    else:
        logger.warning("⚠️  Ollama server is not running - attempting to start...")
        if not ensure_ollama_ready(auto_start=True):
            pytest.fail(
                "\n" + "=" * 80 + "\n"
                "❌ CRITICAL: Ollama server cannot be started for tests!\n"
                "=" * 80 + "\n"
                "Tests require a working Ollama installation.\n\n"
                "Troubleshooting:\n"
                "  1. Install Ollama: https://ollama.ai\n"
                "  2. Start Ollama manually: ollama serve\n"
                "  3. Verify installation: ollama --version\n"
                "  4. Check if port 11434 is available: lsof -i :11434\n"
                "  5. Pull a small test model: ollama pull smollm2\n\n"
                "To deselect Ollama tests: pytest -m 'not requires_ollama'\n"
                "=" * 80
            )

    def _fail_no_models() -> None:
        pytest.fail(
            "\n" + "=" * 80 + "\n"
            "❌ CRITICAL: Ollama server is running but has no models!\n"
            "=" * 80 + "\n"
            "Tests require at least one Ollama model.\n\n"
            "Quick install for tests:\n"
            "  ollama pull smollm2\n\n"
            "Or set OLLAMA_SKIP_TEST_MODEL_PULL=0 (default) to allow auto-pull.\n"
            "Air-gapped: pre-install smollm2 and set OLLAMA_SKIP_TEST_MODEL_PULL=1.\n\n"
            "Verify: ollama list\n"
            "=" * 80
        )

    models = get_model_names()

    def _maybe_pull(reason: str) -> None:
        nonlocal models
        if skip_pull:
            logger.warning(
                "Ollama has no small/fast test model (%s); OLLAMA_SKIP_TEST_MODEL_PULL is set — "
                "tests may use slower fallback models or fail if no model can be loaded. "
                "Install e.g. smollm2 manually.",
                reason,
            )
            return
        logger.info("Pulling test model %r (%s)...", pull_model, reason)
        ok, err = pull_ollama_model(pull_model, timeout=pull_timeout)
        if not ok:
            pytest.fail(
                "\n" + "=" * 80 + "\n"
                "❌ CRITICAL: ollama pull failed for test model.\n"
                "=" * 80 + "\n"
                f"Model: {pull_model}\n"
                f"Timeout: {pull_timeout}s (override with OLLAMA_TEST_PULL_TIMEOUT)\n"
                f"Error: {err}\n\n"
                "Fastest fix — pull the model manually in another terminal:\n"
                f"  ollama pull {pull_model}\n\n"
                "Then re-run tests, or set OLLAMA_SKIP_TEST_MODEL_PULL=1 to\n"
                "use whatever is already installed (see `ollama list`).\n"
                "=" * 80
            )
        models = get_model_names()
        if not models:
            _fail_no_models()
        if not small_fast_preference_matches(models):
            pytest.fail(
                "\n" + "=" * 80 + "\n"
                "❌ CRITICAL: After pull, no small/fast preference model is listed.\n"
                "=" * 80 + "\n"
                f"Expected one of the preferences matching: {pull_model!r}\n"
                f"Got: {models!r}\n"
                "=" * 80
            )

    if not models:
        _maybe_pull("no models installed")
    elif not small_fast_preference_matches(models):
        _maybe_pull("no smollm2/gemma2:2b/… style model in library")

    if not models:
        _fail_no_models()

    # Capability probe: a listed model proves nothing about the runtime — a
    # broken install (e.g. Homebrew Ollama whose bundled llama-server binary is
    # missing) lists models fine and then returns HTTP 500 on every generate.
    # Probe actual inference once per session so 20+ LLM tests fail with one
    # actionable diagnosis instead of identical confusing per-test errors.
    from infrastructure.llm.utils.models import preload_model, select_small_fast_model

    probe_model = select_small_fast_model() or models[0]
    probe_ok, probe_err = preload_model(probe_model, timeout=120.0, retries=1)
    if not probe_ok:
        pytest.fail(
            "\n" + "=" * 80 + "\n"
            "❌ CRITICAL: Ollama lists models but cannot run inference!\n"
            "=" * 80 + "\n"
            f"Probe model: {probe_model}\n"
            f"Error: {probe_err}\n\n"
            "The server is up and models are installed, but loading a model failed —\n"
            "this usually means a broken Ollama runtime (e.g. a Homebrew upgrade that\n"
            "left the llama-server binary missing).\n\n"
            "Troubleshooting:\n"
            "  1. ollama run " + probe_model + " 'hi'   # reproduce directly\n"
            "  2. brew reinstall ollama && brew services restart ollama\n"
            "  3. Or reinstall from https://ollama.ai\n\n"
            "To deselect Ollama tests: pytest -m 'not requires_ollama'\n"
            "=" * 80
        )

    logger.info("✓ Ollama ready for tests with %d model(s): %s", len(models), ", ".join(models[:5]))
    return True


@pytest.fixture(autouse=True)
def _ollama_requires_session(request: pytest.FixtureRequest) -> None:
    """Run session-scoped Ollama ensure once for any ``requires_ollama`` test."""
    if request.node.get_closest_marker("requires_ollama"):
        request.getfixturevalue("ensure_ollama_for_tests")
