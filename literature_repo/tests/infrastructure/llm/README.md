# tests/infrastructure/llm/ - LLM Integration Tests

Comprehensive test suite for local LLM integration (91%+ coverage).

## Quick Start

### Run LLM Tests

```bash
# All LLM tests (requires Ollama)
pytest tests/infrastructure/llm/ -v

# Skip network tests
pytest tests/infrastructure/llm/ -m "not requires_ollama" -v

# Only integration tests
pytest tests/infrastructure/llm/ -m requires_ollama -v
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

## Coverage Requirements

- **91% minimum** for LLM infrastructure modules
- Currently achieving **91%+** coverage
- Network-dependent tests marked with `@pytest.mark.requires_ollama`

## Test Philosophy

- **Pure logic tests** - Configuration and validation without network
- **Integration tests** - Full LLM interactions (requires Ollama)
- **No mocks** - Real LLM responses when possible
- **Graceful skipping** - Tests skip when Ollama unavailable

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete LLM test documentation
- [`../../infrastructure/llm/README.md`](../../infrastructure/llm/README.md) - LLM module overview












