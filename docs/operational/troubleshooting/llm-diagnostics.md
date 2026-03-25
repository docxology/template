# LLM Diagnostics & Configuration Reference

> **Environment variables, diagnostic commands, and performance tuning** for LLM review features

**Quick Reference:** [LLM Troubleshooting](llm-review.md) | [LLM Integration](../../../infrastructure/llm/AGENTS.md) | [Configuration](../config/configuration.md)

For common issues and solutions, see [llm-review.md](llm-review.md). This document covers environment variables, diagnostic commands, and performance optimization.

---

## Environment Variables

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MAX_INPUT_LENGTH` | `500000` | Max characters to send to LLM (0 = unlimited) |
| `LLM_REVIEW_TIMEOUT` | `300` | Timeout per review in seconds |
| `LLM_LONG_MAX_TOKENS` | `16384` | Maximum tokens per review response |
| `LLM_CONTEXT_WINDOW` | `262144` | Context window size (for 256K models) |
| `LOG_LEVEL` | `1` | Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR) |

### Usage Examples

```bash
# Enable debug logging
export LOG_LEVEL=0

# Increase timeout for slow models
export LLM_REVIEW_TIMEOUT=600

# Limit input for smaller models
export LLM_MAX_INPUT_LENGTH=100000

# Run with custom settings
uv run python scripts/06_llm_review.py --reviews-only
```

---

## Diagnostic Commands

### Check Ollama Status

```bash
# Basic status check
curl http://localhost:11434/api/tags

# List available models
ollama list

# Check loaded models
ollama ps

# Test model directly
ollama run llama3-gradient "Test query"
```

### Check LLM Review System

```bash
# Check script imports
uv run python -c "from infrastructure.llm.core.client import LLMClient; print('OK')"

# Check Ollama utilities
uv run python -c "from infrastructure.llm.utils.ollama import is_ollama_running; print(is_ollama_running())"

# Test LLM client
uv run python -c "
from infrastructure.llm.core.client import LLMClient
client = LLMClient()
print('Available:', client.check_connection())
"
```

### Check PDF and Text Extraction

```bash
# Check PDF exists
ls -la projects/{name}/output/pdf/{name}_combined.pdf

# Test PDF text extraction
uv run python -c "
from pathlib import Path
import PyPDF2
pdf_path = Path('projects/{name}/output/pdf/{name}_combined.pdf')
if pdf_path.exists():
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f'Pages: {len(reader.pages)}')
        print(f'First 200 chars: {reader.pages[0].extract_text()[:200]}')
else:
    print('PDF not found')
"
```

### Review Generated Files

```bash
# Check review outputs
ls -la projects/{name}/output/llm/

# Review metadata
cat projects/{name}/output/llm/review_metadata.json

# Check individual reviews
cat projects/{name}/output/llm/executive_summary.md
cat projects/{name}/output/llm/quality_review.md
```

### Check Logs

```bash
# Enable debug logging
export LOG_LEVEL=0
uv run python scripts/06_llm_review.py --reviews-only 2>&1 | tee llm_review.log

# Review log file
cat llm_review.log | grep -i error
```

---

## Performance Optimization

### Model Selection

**For speed:**
- Use smaller models: `gemma2:2b`, `gemma3:4b`
- Faster response times
- Lower memory usage

**For quality:**
- Use larger models: `llama3-gradient`, `llama3.1`
- Better review quality
- Larger context windows

### Input Optimization

```bash
# For long manuscripts, limit input
export LLM_MAX_INPUT_LENGTH=250000  # ~62K tokens

# For short manuscripts, allow full content
export LLM_MAX_INPUT_LENGTH=0  # Unlimited
```

### Timeout Tuning

```bash
# For fast models
export LLM_REVIEW_TIMEOUT=180  # 3 minutes

# For slow models or long inputs
export LLM_REVIEW_TIMEOUT=600  # 10 minutes
```

---

## Common Error Patterns

**Connection errors:**
- Ollama not running → Start Ollama server
- Port blocked → Check firewall/network
- Wrong URL → Verify Ollama base URL

**Model errors:**
- No models installed → Install recommended model
- Model not loaded → Preload model or wait for auto-load
- Out of memory → Use smaller model or free memory

**Timeout errors:**
- Model too slow → Use faster model or increase timeout
- Input too long → Reduce input size or use larger context model
- System overloaded → Free system resources

---

## See Also

- [LLM Troubleshooting](llm-review.md) — Common issues and solutions
- [LLM Integration](../../../infrastructure/llm/AGENTS.md) — LLM system documentation
- [Configuration](../config/configuration.md) — Configuration system
- [LLM Standards](../../rules/llm_standards.md) — LLM development standards
