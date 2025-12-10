# LLM Review Troubleshooting Guide

This guide helps troubleshoot issues with the LLM manuscript review stage.

## Common Issues

### Ollama Not Running

**Symptoms**:
- Error: "Ollama server is not running"
- Exit code 2 (skipped)

**Solutions**:
```bash
# Start Ollama server
ollama serve

# Or start Ollama app if installed
open -a Ollama  # macOS

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### No Models Available

**Symptoms**:
- Error: "No Ollama models available"
- Exit code 2 (skipped)

**Solutions**:
```bash
# List available models
ollama list

# Install recommended model
ollama pull llama3-gradient

# Or install alternative
ollama pull llama3.1:latest
```

### Model Loading Timeout

**Symptoms**:
- Model warmup takes >120 seconds
- Error: "Model loading timed out"

**Solutions**:
- Use smaller model: `ollama pull llama3:8b`
- Increase available GPU memory
- Check system resources: `ollama ps`

### Slow Generation

**Symptoms**:
- Review generation takes >10 minutes
- Low tokens/second rate

**Solutions**:
- Use faster model (smaller parameter count)
- Reduce `max_tokens` in generation options
- Check GPU availability: `ollama ps`
- Monitor system resources

### Off-Topic Responses

**Symptoms**:
- Review doesn't match manuscript content
- Generic or unrelated content

**Solutions**:
- System automatically retries with reinforced prompt
- Check manuscript text extraction: `python3 -c "from infrastructure.validation.pdf_validator import extract_text_from_pdf; print(len(extract_text_from_pdf('project/output/pdf/project_combined.pdf')))"`
- Verify PDF contains actual content
- Try different model

### Repetitive Content

**Symptoms**:
- Review contains repeated sections
- Low unique content ratio

**Solutions**:
- System automatically deduplicates severe repetition
- Increase temperature slightly
- Try different model
- Check prompt quality

### Memory Issues

**Symptoms**:
- Out of memory errors
- Model fails to load

**Solutions**:
- Use smaller model
- Reduce `LLM_MAX_INPUT_LENGTH`
- Close other applications
- Increase system memory

## Configuration

### Environment Variables

```bash
# Maximum input length (characters)
export LLM_MAX_INPUT_LENGTH=500000  # Default: 500K chars (~125K tokens)
export LLM_MAX_INPUT_LENGTH=0       # Unlimited

# Review generation timeout (seconds)
export LLM_REVIEW_TIMEOUT=300       # Default: 5 minutes per review
export LLM_REVIEW_TIMEOUT=600       # 10 minutes for slow models

# Model selection
export LLM_MODEL="llama3-gradient"  # Override default model
```

### Config File

Edit `project/manuscript/config.yaml`:

```yaml
llm:
  translations:
    enabled: true
    languages:
      - zh  # Chinese
      - hi  # Hindi
      - ru  # Russian
```

## Debugging

### Enable Verbose Logging

```bash
export LOG_LEVEL=0  # DEBUG level
python3 scripts/06_llm_review.py --reviews-only
```

### Check Ollama Status

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check loaded models
ollama ps

# Check model info
ollama show llama3-gradient
```

### Test LLM Connection

```bash
# Test basic query
python3 -c "
from infrastructure.llm import LLMClient
client = LLMClient()
print(client.query('Hello, world!'))
"
```

### Check Manuscript Extraction

```bash
# Extract and check manuscript text
python3 -c "
from infrastructure.validation.pdf_validator import extract_text_from_pdf
text = extract_text_from_pdf('project/output/pdf/project_combined.pdf')
print(f'Extracted {len(text):,} characters')
print(f'First 500 chars: {text[:500]}')
"
```

## Performance Optimization

### Model Selection

**Fast Models** (for quick reviews):
- `llama3:8b` - Fast, good quality
- `qwen3:4b` - Very fast, smaller context

**Quality Models** (for best reviews):
- `llama3-gradient` - Best quality, larger context
- `llama3.1:70b` - Highest quality, very slow

### Generation Options

Adjust in `scripts/06_llm_review.py`:

```python
options = GenerationOptions(
    temperature=0.3,    # Lower = more focused
    max_tokens=4096,    # Reduce for faster generation
)
```

### Streaming Progress

The system now shows real-time progress:
- Token-by-token generation
- Tokens/second rate
- Estimated time remaining
- Progress percentage

## Error Recovery

### Partial Results

If pipeline is interrupted:
- Completed reviews are saved immediately
- Partial reviews are not saved (use streaming for progress)
- Resume pipeline to continue from last completed review

### Checkpoint Integration

LLM reviews are optional stages:
- Pipeline continues even if LLM review fails
- Checkpoint system saves state before LLM stages
- Resume skips completed reviews

## Validation Issues

### Quality Validation Failures

**Symptoms**: Review fails quality checks

**Solutions**:
- System automatically retries with adjusted parameters
- Check validation criteria in `validate_review_quality()`
- Review may be accepted with warnings if retries fail

### Format Compliance

**Symptoms**: Format warnings in logs

**Solutions**:
- Warnings are non-blocking
- Review is still saved and used
- Check for conversational phrases (acceptable but noted)

## Advanced Troubleshooting

### Model-Specific Issues

**Llama3-Gradient**:
- Requires 4.7GB+ GPU memory
- Best for comprehensive reviews
- Slower generation (~40-50 tokens/sec)

**Smaller Models (3B-8B)**:
- Faster generation
- May have lower quality
- Good for quick reviews

### Context Window Limits

**Symptoms**: Truncation warnings

**Solutions**:
- Increase `LLM_MAX_INPUT_LENGTH`
- Set to 0 for unlimited
- Check model context window size

### Network Issues

**Symptoms**: Connection errors

**Solutions**:
- Verify Ollama is accessible: `curl http://localhost:11434`
- Check firewall settings
- Restart Ollama server

## Best Practices

### Development

- Skip LLM reviews during development: Don't use `--pipeline` flag
- Use faster models for quick iterations
- Cache review results

### Production

- Use quality models for final reviews
- Allow full generation time
- Review generated outputs for quality

## See Also

- [`scripts/06_llm_review.py`](../scripts/06_llm_review.py) - Review implementation
- [`infrastructure/llm/`](../infrastructure/llm/) - LLM module documentation
- [`TROUBLESHOOTING_GUIDE.md`](TROUBLESHOOTING_GUIDE.md) - General troubleshooting





