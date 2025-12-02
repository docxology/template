# LLM Module

Local LLM integration for research assistance with flexible response modes and comprehensive configurability.

## Features

- **Ollama Integration**: Connects to local models (Llama 3, Mistral, etc.)
- **Multiple Response Modes**: Short (< 150 tokens), Long (> 500 tokens), Structured (JSON), Raw
- **Per-Query Configuration**: Temperature, seed, stop sequences, max_tokens per query
- **Context Management**: Multi-turn conversations with automatic system prompt injection
- **Research Templates**: Pre-built prompts for common research tasks
- **Streaming Responses**: Real-time response generation
- **Environment Configuration**: Full configuration via OLLAMA_* and LLM_* env vars
- **Comprehensive Validation**: Output quality and format checking
- **Command-Line Interface**: Interactive queries from terminal

## Quick Start

```python
from infrastructure.llm import LLMClient, GenerationOptions

# Initialize (reads OLLAMA_HOST, OLLAMA_MODEL from environment)
client = LLMClient()

# Simple query with context
response = client.query("What is machine learning?")

# With reproducibility
opts = GenerationOptions(temperature=0.0, seed=42)
response = client.query("Explain...", options=opts)
```

## Response Modes

### Short Responses (< 150 tokens)
```python
answer = client.query_short("What is quantum entanglement?")
```

### Long Responses (> 500 tokens)
```python
explanation = client.query_long(
    "Explain quantum entanglement in detail with examples"
)
```

### Structured Responses (JSON)
```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array"},
        "confidence": {"type": "number"}
    },
    "required": ["summary", "key_points"]
}

result = client.query_structured(
    "Summarize the following paper...",
    schema=schema
)
```

### Raw Queries (No Modification)
```python
# Bypass system prompt and instructions
response = client.query_raw("Complete: The quick brown fox")
```

## Per-Query Options

Control generation behavior per-query:

```python
from infrastructure.llm import GenerationOptions

# Deterministic output with seed
opts = GenerationOptions(
    temperature=0.0,
    seed=42,
    max_tokens=500,
    stop=["END", "STOP"],
)
response = client.query("...", options=opts)

# All available options
opts = GenerationOptions(
    temperature=0.7,      # Creativity (0.0 = deterministic)
    max_tokens=2048,      # Max output tokens
    top_p=0.9,            # Nucleus sampling
    top_k=40,             # Top-k sampling
    seed=42,              # Reproducibility seed
    stop=["END"],         # Stop sequences
    format_json=True,     # Force JSON output
    repeat_penalty=1.1,   # Repetition penalty
    num_ctx=4096,         # Context window
)
```

## Configuration

### Environment Variables

```bash
# Connection
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="qwen3:4b"

# Generation defaults
export LLM_TEMPERATURE="0.7"
export LLM_MAX_TOKENS="2048"
export LLM_CONTEXT_WINDOW="4096"
export LLM_TIMEOUT="300"
export LLM_NUM_CTX="4096"
export LLM_SEED="42"  # For reproducibility
export LLM_SYSTEM_PROMPT="Custom system prompt"
```

### Programmatic Configuration

```python
from infrastructure.llm import LLMConfig, LLMClient

config = LLMConfig(
    base_url="http://localhost:11434",
    default_model="qwen3:4b",
    temperature=0.7,
    max_tokens=2048,
    seed=42,
    system_prompt="You are a helpful assistant.",
    auto_inject_system_prompt=True,
)

client = LLMClient(config)

# Override configuration
fast_config = config.with_overrides(temperature=0.0, timeout=30.0)
```

## Streaming

```python
for chunk in client.stream_query("Write a poem"):
    print(chunk, end="", flush=True)

# With options
opts = GenerationOptions(temperature=0.9)
for chunk in client.stream_short("Quick summary", options=opts):
    print(chunk, end="")

for chunk in client.stream_long("Detailed explanation", options=opts):
    print(chunk, end="")
```

## Context Management

```python
# Automatic system prompt injection
client = LLMClient()  # System prompt added automatically

# Multi-turn conversation
response1 = client.query("What is X?")
response2 = client.query("Can you elaborate?")  # Context maintained

# Reset context
client.reset()  # Clears and re-injects system prompt

# Query with context reset
response = client.query("New topic", reset_context=True)

# Change system prompt
client.set_system_prompt("New persona...")
```

## Utilities

```python
# Check Ollama connection
if client.check_connection():
    print("Ollama is running")

# List available models
models = client.get_available_models()
print(f"Available: {models}")

# Apply research templates
summary = client.apply_template(
    "summarize_abstract",
    text=abstract_text
)
```

## Validation

```python
from infrastructure.llm import OutputValidator

# Validate JSON output
data = OutputValidator.validate_json(response)

# Check response length
if OutputValidator.validate_short_response(response):
    print("Valid short response")

# Validate structure against schema
OutputValidator.validate_structure(data, schema)

# Comprehensive validation
OutputValidator.validate_complete(response, mode="structured", schema=schema)
```

## Error Handling

```python
from infrastructure.core.exceptions import (
    LLMConnectionError,
    LLMTemplateError,
    ValidationError,
    ContextLimitError
)

try:
    response = client.query("...")
except LLMConnectionError as e:
    print(f"Connection failed: {e.context}")
except ContextLimitError as e:
    print(f"Context limit exceeded: {e.context}")
```

## Command-Line Interface

The module provides a CLI for interactive queries:

```bash
# Check Ollama connection
python3 -m infrastructure.llm.cli check

# List available models
python3 -m infrastructure.llm.cli models

# Send a query
python3 -m infrastructure.llm.cli query "What is machine learning?"

# Short response
python3 -m infrastructure.llm.cli query --short "Summarize X"

# Long response
python3 -m infrastructure.llm.cli query --long "Explain X in detail"

# Streaming output
python3 -m infrastructure.llm.cli query --stream "Write a poem"

# With custom options
python3 -m infrastructure.llm.cli query --temperature 0.0 --seed 42 "Test"

# Apply research template
python3 -m infrastructure.llm.cli template --list
python3 -m infrastructure.llm.cli template summarize_abstract --input "Abstract text..."
```

## Testing

The LLM module has comprehensive test coverage (88%+) following the **No Mocks Policy**.

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| **Configuration** | 38 | LLMConfig, GenerationOptions, environment loading |
| **Context** | 4 | ConversationContext, token management |
| **Core Logic** | 80+ | LLMClient pure logic without network |
| **Integration** | 12 | Real Ollama interactions (requires running server) |
| **Templates** | 4 | Template rendering and variable substitution |
| **Validation** | 51 | Output validation, JSON parsing, structure checking |
| **CLI** | 13 | Command-line interface parsing and execution |
| **Ollama Utils** | 24 | Model discovery and selection utilities |

### Running Tests

```bash
# All LLM tests (including integration tests, requires Ollama)
pytest tests/infrastructure/llm/ -v

# Pure logic tests only (no Ollama required, fast)
pytest tests/infrastructure/llm/ -m "not requires_ollama" -v

# Integration tests only (requires running Ollama)
pytest tests/infrastructure/llm/ -m requires_ollama -v

# With coverage report
pytest tests/infrastructure/llm/ --cov=infrastructure/llm --cov-report=term-missing

# Generate HTML coverage report
pytest tests/infrastructure/llm/ --cov=infrastructure/llm --cov-report=html
open htmlcov/index.html
```

### Test Organization

```
tests/infrastructure/llm/
├── conftest.py              # Fixtures (clean_llm_env, default_config, etc.)
├── test_cli.py              # CLI command tests
├── test_config.py           # LLMConfig and GenerationOptions tests
├── test_context.py          # ConversationContext tests
├── test_core.py             # LLMClient core functionality
├── test_llm_core_additional.py   # Additional core coverage
├── test_llm_core_coverage.py     # Extended coverage tests
├── test_llm_core_full.py         # Complete feature tests
├── test_ollama_utils.py     # Model discovery utilities
├── test_templates.py        # Research template tests
└── test_validation.py       # OutputValidator tests
```

### Integration Test Behavior

Integration tests marked with `@pytest.mark.requires_ollama`:
- Auto-skip when Ollama is not running
- Use extended timeouts for slow models (120s for long queries)
- Skip gracefully on timeout or model quality issues
- Skipped during automated pipeline (`run_all.sh`) for speed

### Test Fixtures

Key fixtures defined in `conftest.py`:

```python
# Default LLMConfig with discovered model
default_config

# Config with auto system prompt injection enabled
config_with_system_prompt

# Sample GenerationOptions
generation_options

# Clean environment (removes LLM_* env vars for isolation)
clean_llm_env

# Sample messages and JSON responses
sample_messages
sample_json_responses
sample_schema
```

### Coverage Summary

| Module | Coverage | Notes |
|--------|----------|-------|
| `__init__.py` | 100% | Public API exports |
| `config.py` | 98% | Configuration management |
| `context.py` | 100% | Context handling |
| `core.py` | 98% | Main LLMClient logic |
| `templates.py` | 100% | Research templates |
| `validation.py` | 99% | Output validation |
| `ollama_utils.py` | 83% | Model discovery |
| `cli.py` | 60% | Command-line interface |
| **Total** | **88%** | All critical paths covered |

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed architecture and API documentation
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure layer documentation
