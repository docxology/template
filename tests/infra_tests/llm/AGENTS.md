# LLM Module Tests

## Overview

Tests for `infrastructure.llm` follow the **no mocks** rule: `MagicMock` /
`unittest.mock.patch` are not used. Deterministic HTTP uses **pytest_httpserver**
(`ollama_test_server`). Subprocess-oriented helpers (for example
`pull_ollama_model`) use **real stub scripts** and optional injectable ``which`` /
``run`` parameters instead of patching `subprocess.run`.

**Scale:** 66 `test_*.py` modules (hundreds of tests). Run subsets while
developing; CI-quality gate is the full deterministic suite.

**Coverage (informal):** with `-m "not requires_ollama"`, package
`infrastructure.llm` is typically **~84%** line aggregate; many files hit 100%.
Re-measure after substantive edits:

```bash
uv run pytest tests/infra_tests/llm/ -m "not requires_ollama" \
  --cov=infrastructure.llm --cov-report=term-missing --cov-fail-under=0
```

## Layout

```text
tests/infra_tests/llm/
├── __init__.py
├── conftest.py                 # ollama_test_server, patch_llm_client_for_tests (OLLAMA_HOST → stub)
├── ollama_stub_server.py       # POST /api/chat handler rules (models, prompts, stream shapes)
├── real_ollama_client.py       # Real daemon helpers for requires_ollama
├── test_*.py                   # 66 modules — core client, streaming, review, validation, CLI, …
└── AGENTS.md                   # This file
```

Groupings (non-exhaustive):

| Area | Examples |
|------|----------|
| Client / connection / streaming | `test_core.py`, `test_llm_core_*.py`, `test_connection_mixin_coverage.py`, `test_streaming.py`, `test_stream_helpers_coverage.py`, `test_response_saving.py` |
| Config / context | `test_config.py`, `test_config_expanded_coverage.py`, `test_context.py`, `test_context_*coverage*.py` |
| Utils / server | `test_ollama_utils.py`, `test_server_coverage.py`, `test_heartbeat*.py` |
| Review / manuscript | `test_review_*.py`, `test_manuscript_*.py`, `test_llm_review.py` |
| Validation / sanitization | `test_validation.py`, `test_validation_*coverage*.py`, `test_sanitization*.py` |
| CLI / prompts / templates | `test_cli.py` (direct command functions); optional subprocess tests calling `python -m infrastructure.llm.cli` for `main()` exit codes |
| Review pipeline | `test_llm_review.py` and related `test_review_*.py` modules |

## Test Categories

### 1. Deterministic (`-m "not requires_ollama"`)

Default for CI and local runs: **pytest_httpserver** stubs Ollama’s HTTP API.
`patch_llm_client_for_tests` sets `OLLAMA_HOST` to the stub unless the test is
marked `@pytest.mark.no_patch_llm_client`.

**Stub prompt markers** (handled in `ollama_stub_server.build_chat_handler`):

- `__OLLAMA_HTTP_EMPTY_STREAM__` — single final stream chunk with empty content
- `__OLLAMA_HTTP_BAD_NDJSON_LINE__` — non-JSON first line, then valid chunks (parser skips bad lines)

Model names `primary-model` / `fallback1` still yield HTTP 500 for fallback tests.

### 2. Real daemon (`@pytest.mark.requires_ollama`)

Smoke checks against a local Ollama install (`ollama serve`, at least one model).
Not expected in environments without the daemon.

## Running Tests

```bash
# Deterministic suite (fake Ollama HTTP server)
uv run pytest tests/infra_tests/llm/ -m "not requires_ollama" -v

# Real-daemon smoke tests
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v

# Full LLM suite
uv run pytest tests/infra_tests/llm/ -v

# With coverage
uv run pytest tests/infra_tests/llm/ --cov=infrastructure/llm --cov-report=term-missing

# Quick summary
uv run pytest tests/infra_tests/llm/ -q
```

## Key Fixtures (conftest.py)

### Configuration Fixtures

```python
@pytest.fixture
def default_config():
    """OllamaClientConfig with auto-discovered model from Ollama.
    Falls back to the configured default if Ollama is not available."""

@pytest.fixture
def config_with_system_prompt():
    """OllamaClientConfig with auto_inject_system_prompt=True."""

@pytest.fixture
def generation_options():
    """Sample GenerationOptions for testing."""
```

### Environment Fixtures

```python
@pytest.fixture
def clean_llm_env():
    """Removes all LLM_* and OLLAMA_* environment variables.
    Restores after test for isolation."""
```

### Sample Data Fixtures

```python
@pytest.fixture
def sample_messages():
    """List of conversation messages for context testing."""

@pytest.fixture
def sample_json_responses():
    """Dict of valid/invalid JSON strings for validation testing."""

@pytest.fixture
def sample_schema():
    """JSON schema for structured response validation."""
```

## Integration Test Behavior

Integration tests are designed to be robust against external service variability:

### Loud Failures

Tests now FAIL loudly when:
- Ollama server cannot be started automatically
- Ollama server is running but has no models
- Connection issues persist after auto-start attempts

Tests use the `ensure_ollama_for_tests` session fixture which:
- Automatically starts Ollama if not running
- Verifies Ollama has at least one model installed
- Provides detailed error messages with troubleshooting steps

The real-daemon path is intentionally a smoke layer: it verifies `/api/tags`,
model discovery, connection checks, and representative query/streaming paths
without attempting to fully certify every Ollama deployment state.

```python
@pytest.mark.requires_ollama
class TestLLMClientWithOllama:
    @pytest.fixture(autouse=True)
    def check_ollama(self, ensure_ollama_for_tests):
        """Ensure Ollama is running and functional for tests."""
        # Fixture dependency ensures Ollama is ready
        # If Ollama can't be started, ensure_ollama_for_tests will fail loudly
        pass
```

### Timeout Handling

Long queries use extended timeouts:

```python
def test_query_long(self, client, default_config):
    # Extended timeout for long-form generation
    extended_config = default_config.with_overrides(timeout=120.0)
    try:
        response = client.query_long("...")
    except LLMConnectionError as e:
        if "timed out" in str(e).lower():
            pytest.skip(f"Ollama timed out: {e}")
```

### Empty Response Handling

Structured queries handle model quality issues:

```python
def test_query_structured(self, ...):
    result = client.query_structured(...)
    if len(result) == 0:
        pytest.skip("Model returned empty JSON (model quality issue)")
```

## Coverage Summary

Do not rely on static percentages in this file: run `--cov=infrastructure.llm`
as in the Overview. The deterministic suite targets user-facing branches; some
CLI and daemon-only paths stay thin until exercised manually or with
`requires_ollama`.

## Adding Tests

### For Pure Logic

```python
# test_new_feature.py
class TestNewFeature:
    def test_basic_functionality(self, default_config):
        """Test without network access."""
        client = LLMClient(default_config)
        # Test logic that doesn't require Ollama
        assert client.config is not None
```

### For Integration

```python
@pytest.mark.requires_ollama
class TestNewIntegration:
    @pytest.fixture(autouse=True)
    def check_ollama(self):
        if not is_ollama_running():
            pytest.skip("Ollama not available")
    
    def test_with_ollama(self, client):
        """Test with real Ollama server."""
        try:
            response = client.query("Test")
            assert response is not None
        except LLMConnectionError as e:
            pytest.skip(f"Ollama issue: {e}")
```

## Pipeline Integration

### Automated Pipeline (run.sh)

LLM integration tests are **skipped** during automated pipeline runs for speed:

```bash
# In run.sh (option 8 / --pipeline)
uv run pytest tests/infra_tests/ -m "not requires_ollama" ...
```

### Manual Testing

Run integration tests separately when needed:

```bash
# Ensure Ollama is running
ollama serve

# Run integration tests
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v
```

## Troubleshooting

### Tests Skip Unexpectedly

1. Check if Ollama is running: `ollama list`
2. Verify model is available: `ollama list | grep llama`
3. Check connection: `curl http://localhost:11434/api/tags`

### Tests Timeout

1. Increase timeout: `default_config.with_overrides(timeout=180.0)`
2. Use simpler prompts for testing
3. Check Ollama model size (smaller models are faster)

### Empty JSON Responses

This is a model quality issue, not a code bug:
- Try a different model with better JSON capabilities
- Use `use_native_json=True` for Ollama's format="json" mode

## See Also

- [`../../../infrastructure/llm/AGENTS.md`](../../../infrastructure/llm/AGENTS.md) - Module documentation
- [`../../../infrastructure/llm/README.md`](../../../infrastructure/llm/README.md) - Quick reference
- [`conftest.py`](conftest.py) - Fixture definitions


