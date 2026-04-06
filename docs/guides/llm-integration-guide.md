# AI-Assisted Research with Ollama

> **Use local LLMs for manuscript review, translation, and literature analysis**

**Skill Level**: 11-12  
**Quick Reference:** [Modules Guide](../modules/modules-guide.md) | [LLM Module](../modules/guides/llm-module.md) | [RUN_GUIDE](../RUN_GUIDE.md)

---

## Prerequisites

1. **Install Ollama**: [ollama.com](https://ollama.com)
2. **Pull a model**:

```bash
ollama serve          # Start the server (runs on localhost:11434)
ollama pull gemma3:4b # Lightweight model for reviews
```

3. **Verify**: `ollama list` should show your model.

---

## Quick Start: Pipeline LLM Review

The simplest way to use LLM features is through the pipeline:

```bash
# Run with LLM review enabled
./run.sh --pipeline  # Select your project, LLM stages run automatically

# Or via the core pipeline
uv run python scripts/execute_pipeline.py --project code_project
# Stage 06 (LLM Review) runs if Ollama is available
```

If Ollama is not running, Stage 06 gracefully skips — no failure.

---

## Configuring LLM in config.yaml

Each project controls LLM behavior in `projects/{name}/manuscript/config.yaml`:

```yaml
llm:
  reviews:
    enabled: true
    types:
      - executive_summary    # 1-page overview
      - quality_review       # Detailed feedback
  translations:
    enabled: true
    languages: [zh, hi, ru]  # Target languages for abstract
```

Set `enabled: false` to skip LLM stages entirely.

---

## Programmatic Usage

### Basic Query

```python
from infrastructure.llm import LLMClient, OllamaClientConfig, GenerationOptions

# Create client
config = OllamaClientConfig(default_model="gemma3:4b")
client = LLMClient(config)

# Generate text
options = GenerationOptions(temperature=0.7, max_tokens=1000)
response = client.generate("Summarize the key findings of this paper.", options=options)
print(response)
```

### Manuscript Review

```python
from infrastructure.llm import generate_review_with_metrics
from pathlib import Path

# Generate a structured review of a manuscript
result, metrics = generate_review_with_metrics(
    manuscript_path=Path("projects/code_project/output/manuscript/"),
    review_type="quality_review",
)
print(result)
print(f"Tokens used: {metrics}")
```

### Prompt Templates

```python
from infrastructure.llm import get_template

# Get a built-in template
template = get_template("executive_summary")
print(template)  # Shows the prompt structure
```

### Output Validation

```python
from infrastructure.llm import validate_complete, is_off_topic

# Check if LLM output is complete
is_valid = validate_complete(response_text)

# Check if response drifted off-topic
off_topic = is_off_topic(response_text, expected_topic="gradient descent")
```

---

## CLI Usage

```bash
# Query the LLM directly
uv run python -m infrastructure.llm.cli query "What is gradient descent?"

# Check Ollama connectivity
uv run python -m infrastructure.llm.cli check

# List available models
uv run python -m infrastructure.llm.cli models
```

---

## Pipeline Integration

LLM features are used in two pipeline stages:

| Stage | Script | Purpose |
|-------|--------|---------|
| 06 | `scripts/06_llm_review.py` | Executive summary + quality review |
| 06 | `scripts/06_llm_review.py` | Abstract translations (if configured) |

Both stages are **skippable** — the pipeline succeeds without Ollama.

---

## Troubleshooting

**Ollama not running:**
```bash
ollama serve  # Start the server
# Or check: curl http://localhost:11434/api/tags
```

**Model too large for system:**
```bash
ollama pull gemma3:4b   # 4B parameters, ~3GB RAM
# Instead of larger models like llama3:70b
```

**Timeout on generation:**
- Increase timeout in `OllamaClientConfig(timeout=120)`
- Use a smaller model
- Reduce `max_tokens` in `GenerationOptions`

**Tests requiring Ollama:**
```bash
# Run LLM-specific tests (requires running Ollama)
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v

# Skip Ollama tests (default in CI)
uv run pytest tests/infra_tests/llm/ -m "not requires_ollama" -v
```

---

## Related Documentation

- **[LLM Module Reference](../modules/guides/llm-module.md)** — API details
- **[RUN_GUIDE](../RUN_GUIDE.md)** — Pipeline execution
- **[Extending & Automation (Level 12)](extending-and-automation.md)** — Research workflow integration
- **[Infrastructure AGENTS.md](../../infrastructure/llm/AGENTS.md)** — Machine-readable spec
