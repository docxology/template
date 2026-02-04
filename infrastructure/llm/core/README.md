# LLM Core

Core Large Language Model client and configuration management for local LLM integration.

## Overview

The LLM core provides the fundamental interface for interacting with Large Language Models through Ollama. It handles connection management, prompt engineering, response processing, and conversation context.

## Key Components

- **LLMClient**: Main interface for LLM queries and conversations
- **LLMConfig**: Configuration management for model settings
- **ConversationContext**: Multi-turn conversation management
- **Response Processing**: Streaming, structured responses, and validation

## Quick Start

```python
from infrastructure.llm.core import LLMClient

# Basic usage
client = LLMClient()
response = client.query("Explain quantum computing")

# Structured response
schema = {"type": "object", "properties": {"explanation": {"type": "string"}}}
result = client.query_structured("Explain quantum computing", schema=schema)
```

## Configuration

### Environment Variables
```bash
export OLLAMA_HOST="http://localhost:11434"      # Ollama server URL
export OLLAMA_MODEL="gemma3:4b"                  # Default model
export LLM_TEMPERATURE="0.7"                     # Generation temperature
export LLM_MAX_TOKENS="2048"                     # Maximum tokens
export LLM_SYSTEM_PROMPT="You are a helpful assistant"  # System prompt
```

### Programmatic Configuration
```python
from infrastructure.llm.core.config import LLMConfig

config = LLMConfig(
    base_url="http://localhost:11434",
    default_model="gemma3:4b",
    temperature=0.7,
    max_tokens=2048,
    system_prompt="You are a research assistant"
)

client = LLMClient(config)
```

## Usage Examples

### Basic Queries
```python
# Simple query
response = client.query("What is machine learning?")

# Short response (concise)
short = client.query_short("Summarize this paper")

# Long response (detailed)
long = client.query_long("Provide detailed analysis")
```

### Structured Responses
```python
# JSON-structured output
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}}
    }
}

result = client.query_structured("Analyze this research", schema=schema)
print(result["title"])
print(result["summary"])
```

### Streaming Responses
```python
# Real-time streaming
for chunk in client.stream_query("Write a long explanation"):
    print(chunk, end="", flush=True)
```

### Conversation Management
```python
# Multi-turn conversation
client.query("What is Python?")
client.query("How do I install it?")
client.query("Show me a simple example")

# Reset conversation
client.reset()

# Custom system prompt
client.set_system_prompt("You are an expert in data science")
```

## Error Handling

```python
from infrastructure.llm.core.exceptions import LLMConnectionError, LLMTimeoutError

try:
    response = client.query("Test query")
except LLMConnectionError:
    print("Cannot connect to Ollama server")
except LLMTimeoutError:
    print("Request timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Connection Management

### Automatic Model Selection
```python
# Auto-select best available model
config = LLMConfig.from_env()  # Uses environment or defaults
client = LLMClient(config)

# Client automatically selects from available models
# Priority: llama3-gradient > llama3.1 > llama2 > gemma3 > mistral
```

### Health Checking
```python
# Check server availability
is_running = client.check_connection()

# Detailed health information
from infrastructure.llm.utils.ollama import check_ollama_health
health = check_ollama_health()
print(f"Server healthy: {health['healthy']}")
```

## Testing

```bash
# Test core functionality (no Ollama required)
pytest tests/infra_tests/llm/test_config.py -v
pytest tests/infra_tests/llm/test_context.py -v

# Test with Ollama (requires running server)
pytest tests/infra_tests/llm/test_core.py -m requires_ollama -v
```

## Performance Considerations

- **Connection Pooling**: Efficient HTTP connection reuse
- **Token Management**: Automatic context window management
- **Streaming**: Memory-efficient real-time response processing
- **Caching**: Optional response caching for repeated queries

## See Also

- [AGENTS.md](AGENTS.md) - technical documentation
- [../README.md](../README.md) - LLM infrastructure overview
- [../../core/](../../core/) - Core infrastructure utilities