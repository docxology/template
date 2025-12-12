# LLM Module Tests

## Overview

Comprehensive test suite for the LLM module with **88%+ coverage** following the **No Mocks Policy**. All tests use real data and real computations.

## Test Organization

```
tests/infrastructure/llm/
├── conftest.py              # Shared fixtures
├── test_cli.py              # CLI command tests (13 tests)
├── test_config.py           # Configuration tests (38 tests)
├── test_context.py          # Context management tests (4 tests)
├── test_core.py             # Core LLMClient tests (26 tests)
├── test_llm_core_additional.py   # Additional core coverage (33 tests)
├── test_llm_core_coverage.py     # Extended coverage tests (28 tests)
├── test_llm_core_full.py         # Complete feature tests (26 tests)
├── test_ollama_utils.py     # Model discovery tests (24 tests)
├── test_templates.py        # Template tests (4 tests)
└── test_validation.py       # Validation tests (51 tests)
```

## Test Categories

### 1. Pure Logic Tests (No Ollama Required)

Tests that verify business logic without network access:

| File | Tests | What's Tested |
|------|-------|---------------|
| `test_config.py` | 38 | LLMConfig, GenerationOptions, environment loading |
| `test_context.py` | 4 | ConversationContext, token management, message handling |
| `test_validation.py` | 51 | OutputValidator, JSON parsing, structure validation |
| `test_templates.py` | 4 | Template rendering, variable substitution |
| `test_llm_core_coverage.py` | 25 | LLMClient initialization, options, system prompts |
| `test_llm_core_full.py` | 21 | Response modes, context management, edge cases |

### 2. Integration Tests (Require Ollama)

Tests marked with `@pytest.mark.requires_ollama` that require a running Ollama server:

| File | Tests | What's Tested |
|------|-------|---------------|
| `test_core.py` | 12 | Full query lifecycle, streaming, templates |
| `test_cli.py` | 3 | CLI commands with real Ollama |
| `test_ollama_utils.py` | 12 | Model discovery, selection, connection |

## Running Tests

```bash
# All LLM tests (requires Ollama for full suite)
pytest tests/infrastructure/llm/ -v

# Pure logic tests only (fast, no Ollama)
pytest tests/infrastructure/llm/ -m "not requires_ollama" -v

# Integration tests only (requires Ollama)
pytest tests/infrastructure/llm/ -m requires_ollama -v

# With coverage
pytest tests/infrastructure/llm/ --cov=infrastructure/llm --cov-report=term-missing

# Quick summary
pytest tests/infrastructure/llm/ -q
```

## Key Fixtures (conftest.py)

### Configuration Fixtures

```python
@pytest.fixture
def default_config():
    """LLMConfig with auto-discovered model from Ollama.
    Falls back to 'llama3' if Ollama not available."""

@pytest.fixture
def config_with_system_prompt():
    """LLMConfig with auto_inject_system_prompt=True."""

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

### Graceful Skipping

Tests skip gracefully when:
- Ollama server is not running
- Connection times out (extended to 120s for long queries)
- Model returns empty or invalid responses

```python
@pytest.mark.requires_ollama
class TestLLMClientWithOllama:
    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Auto-skip if Ollama not available."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")
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

| Module | Coverage | Key Areas |
|--------|----------|-----------|
| `__init__.py` | 100% | Public API exports |
| `config.py` | 98% | Configuration, environment loading |
| `context.py` | 100% | Message management, token tracking |
| `core.py` | 98% | LLMClient methods, query modes |
| `templates.py` | 100% | Template rendering |
| `validation.py` | 99% | JSON, length, structure validation |
| `ollama_utils.py` | 83% | Model discovery (network-dependent) |
| `cli.py` | 60% | Command-line interface |
| **Total** | **88%** | All critical paths covered |

## Adding New Tests

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
# In run_manuscript.sh (option 8 / --pipeline)
pytest tests/infrastructure/ -m "not requires_ollama" ...
```

### Manual Testing

Run integration tests separately when needed:

```bash
# Ensure Ollama is running
ollama serve

# Run integration tests
pytest tests/infrastructure/llm/ -m requires_ollama -v
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


