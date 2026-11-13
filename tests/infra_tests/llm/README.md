# tests/infra_tests/llm/ - LLM Integration Tests

Deterministic tests use **pytest_httpserver** (`ollama_test_server` + `ollama_stub_server.py`) for client protocol and conversation-state contracts. Explicit **requires_ollama** tests cover real-daemon status, model selection, missing-model lookup and preload state.

## Quick Start

### Run LLM Tests

```bash
# Deterministic suite backed by the local HTTP test server
uv run pytest tests/infra_tests/llm/ -m "not requires_ollama" -v

# Real-daemon state contracts (requires an owned prepared daemon)
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v

# Default LLM test profile (repository marker defaults still apply)
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

## Coverage

- Re-measure with `uv run pytest tests/infra_tests/llm/ -m "not requires_ollama" --cov=infrastructure.llm --cov-report=term-missing`.
- The deterministic aggregate is typically **~80–86%** depending on the tree; there is no separate CI floor for `infrastructure.llm` beyond what the full infra suite enforces.
- Daemon-only behavior is marked `@pytest.mark.requires_ollama` and is not part of the default gate.

## Test Philosophy

- **Pure logic tests** - Configuration and validation without network
- **Deterministic integration tests** - Client protocol and state behavior against owned HTTP endpoints
- **Real-daemon contracts** - Explicit daemon, selection, preload and query-history outcomes
- **No mocks** - HTTP contract fixtures are not model-runtime acceptance
- **Loud failures** - Required daemon prerequisites fail when unavailable
- **Owned runtime** - Release preparation and cleanup belong to the hosted acceptance workflow

### Local Ollama Expectations

- `tests/infra_tests/llm/conftest.py` provides `ollama_test_server`; `ollama_stub_server.py` holds POST `/api/chat` response rules.
- `tests/infra_tests/llm/conftest.py` provides `ensure_ollama_for_tests` for this package. Release jobs prepare pinned model bytes first and disable implicit pulls.
- Prose-presence, generated-length, canned-word, history-count-growth and redundant metric/default smokes are retired, not re-pinned. The unused prepared-client helper is removed. Deterministic HTTP contracts do not replace the real generation required by native consumers.
- Actual local generation remains a separate Source-owned native obligation: `infrastructure.llm.core.local_ollama.generate_local_review` and the native `local-review` / `translation` consumers bind the selected model digest, exact request/response bytes, completion/token evidence, prompt and unchanged manuscript sources.
- Successful preparation does not certify that an arbitrary generation fits a consumer's request budget. Keep request, pytest and operation clocks unchanged; retain genuine daemon diagnostics rather than shortening prompts, changing token budgets or treating an idle streaming timeout as a whole-response deadline.

## See Also

- [`AGENTS.md`](AGENTS.md) - LLM test documentation
- [`../../../infrastructure/llm/README.md`](../../../infrastructure/llm/README.md) - LLM module overview
