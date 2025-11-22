# LLM Module

Local LLM integration for research assistance with flexible response modes.

## Features

- **Ollama Integration**: Connects to local models (Llama 3, Mistral, etc.)
- **Multiple Response Modes**: Short (< 150 tokens), Long (> 500 tokens), Structured (JSON)
- **Context Management**: Multi-turn conversations with token limits
- **Research Templates**: Pre-built prompts for common research tasks
- **Streaming Responses**: Real-time response generation
- **Comprehensive Validation**: Output quality and format checking
- **Model Discovery**: List available models and check connection

## Response Modes

### Short Responses
Brief, direct answers (< 150 tokens):
```python
client = LLMClient()
answer = client.query_short("What is quantum entanglement?")
```

### Long Responses
Comprehensive, detailed answers (> 500 tokens):
```python
explanation = client.query_long(
    "Explain quantum entanglement in detail with examples"
)
```

### Structured Responses
JSON-formatted structured data:
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

## Streaming

Generate responses in real-time:
```python
for chunk in client.stream_query("Write a poem"):
    print(chunk, end="", flush=True)

# Or with specific modes
for chunk in client.stream_short("Quick summary"):
    print(chunk, end="")

for chunk in client.stream_long("Detailed explanation"):
    print(chunk, end="")
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

## Quick Start

```python
from infrastructure.llm import LLMClient, OutputValidator

# Initialize client
client = LLMClient()

# Simple query
response = client.query("What is machine learning?")

# With validation
answer = client.query_short("Is AI dangerous?")
if OutputValidator.validate_short_response(answer):
    print("Valid short response")

# Structured data
data = client.query_structured(
    "Extract key info from text...",
    schema={"type": "object", "properties": {...}}
)
```

