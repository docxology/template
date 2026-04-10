# tests/infra_tests/llm/ - LLM Integration Tests

Deterministic tests use **pytest_httpserver** (`ollama_test_server` + `ollama_stub_server.py`); optional **requires_ollama** smoke tests hit a real daemon.

## Quick Start

### Run LLM Tests

```bash
# Deterministic suite backed by the local HTTP test server
uv run pytest tests/infra_tests/llm/ -m "not requires_ollama" -v

# Real-daemon smoke tests (requires Ollama running locally)
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v

# Full LLM test suite
uv run pytest tests/infra_tests/llm/ -v
```

## Test Categories

### Core Functionality
- `test_core.py` - LLM client core operations
- `test_ollama_utils.py` - Ollama model management
- `test_validation.py` - Response validation

### Advanced Features
- `test_context.py` - Conversation context management
- `test_templates.py` - Research prompt templates
- `test_config.py` - Configuration management

### Integration Tests
- `test_cli.py` - Command-line interface
- `test_llm_core_additional.py` - Extended core functionality
- `test_llm_core_coverage.py` - Coverage-focused tests

## Coverage

- Re-measure with `uv run pytest tests/infra_tests/llm/ -m "not requires_ollama" --cov=infrastructure.llm --cov-report=term-missing`.
- The deterministic aggregate is typically **~80–86%** depending on the tree; there is no separate CI floor for `infrastructure.llm` beyond what the full infra suite enforces.
- Daemon-only behavior is marked `@pytest.mark.requires_ollama` and is not part of the default gate.

## Test Philosophy

- **Pure logic tests** - Configuration and validation without network
- **Deterministic integration tests** - Full LLM behavior against `ollama_test_server`
- **Real-daemon smoke tests** - Marked with `@pytest.mark.requires_ollama`
- **No mocks** - Real LLM responses when possible
- **Loud failures** - Tests FAIL when Ollama unavailable (auto-start attempted)
- **Auto-start** - Ollama server is automatically started for tests

### Local Ollama Expectations

- `tests/infra_tests/llm/conftest.py` provides `ollama_test_server`; `ollama_stub_server.py` holds POST `/api/chat` response rules.
- `tests/conftest.py` provides `ensure_ollama_for_tests` and an autouse hook for `@pytest.mark.requires_ollama` (real daemon; may run `ollama pull smollm2` unless `OLLAMA_SKIP_TEST_MODEL_PULL=1`).
- `real_ollama_client.py` builds `LLMClient` instances aimed at `http://localhost:11434` with a preloaded small model (avoids patched `OLLAMA_HOST`).
- The real-daemon layer checks `/api/tags`, model discovery, queries, streaming, and preload behavior.

## See Also

- [`AGENTS.md`](AGENTS.md) - LLM test documentation
- [`../../../infrastructure/llm/README.md`](../../../infrastructure/llm/README.md) - LLM module overview
















