# LLM Integration Module

> **Local LLM assistance for research workflows**

**Location:** `infrastructure/llm/core.py`  
**Quick Reference:** [Modules Guide](../MODULES_GUIDE.md) | [API Reference](../../reference/API_REFERENCE.md)

---

## Key Features

- **Ollama Integration**: Local model support (privacy-first)
- **Template System**: Pre-built prompts for research tasks
- **Context Management**: Multi-turn conversation handling
- **Streaming Support**: Real-time response generation
- **Model Fallback**: Automatic fallback to alternative models
- **Token Counting**: Track usage and costs

---

## Research Templates

- Abstract summarization
- Literature review generation
- Code documentation
- Data interpretation
- Section drafting assistance
- Citation formatting
- Technical abstract translation (Chinese, Hindi, Russian)

---

## Usage Examples

### Basic LLM Query

```python
from infrastructure.llm import LLMClient

# Initialize client (reads OLLAMA_HOST, OLLAMA_MODEL from environment)
client = LLMClient()

# Simple query
response = client.query("What are the key findings in this paper?")
print(response)
```

### Using Research Templates

```python
# Apply research template
summary = client.apply_template(
    "summarize_abstract",
    text=abstract_text
)

# Generate literature review section
review = client.apply_template(
    "literature_review",
    topic="machine learning",
    papers=["paper1", "paper2", "paper3"]
)
```

### Response Modes

```python
# Short response (< 150 tokens)
answer = client.query_short("What is quantum entanglement?")

# Long response (> 500 tokens)
explanation = client.query_long("Explain quantum entanglement in detail")

# Structured JSON response
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array"}
    }
}
result = client.query_structured("Summarize...", schema=schema)
```

### Streaming Responses

```python
# Stream response in real-time
for chunk in client.stream_query("Write a research summary"):
    print(chunk, end="", flush=True)
```

---

## CLI Integration

```bash
# Check Ollama connection
python3 -m infrastructure.llm.cli check

# List available models
python3 -m infrastructure.llm.cli models

# Send query
python3 -m infrastructure.llm.cli query "What is machine learning?"

# Apply template
python3 -m infrastructure.llm.cli template summarize_abstract --input "Abstract text..."
```

---

**Related:** [Literature Module](LITERATURE_MODULE.md) | [Rendering Module](RENDERING_MODULE.md)
