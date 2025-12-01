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
export OLLAMA_MODEL="llama3"

# Generation defaults
export LLM_TEMPERATURE="0.7"
export LLM_MAX_TOKENS="2048"
export LLM_CONTEXT_WINDOW="4096"
export LLM_TIMEOUT="60"
export LLM_NUM_CTX="4096"
export LLM_SEED="42"  # For reproducibility
export LLM_SYSTEM_PROMPT="Custom system prompt"
```

### Programmatic Configuration

```python
from infrastructure.llm import LLMConfig, LLMClient

config = LLMConfig(
    base_url="http://localhost:11434",
    default_model="llama3",
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

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed architecture and API documentation
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure layer documentation
