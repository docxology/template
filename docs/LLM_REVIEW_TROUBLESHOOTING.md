# LLM Review Troubleshooting Guide

> **Specialized troubleshooting** for LLM manuscript review and translation features

**Quick Reference:** [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) | [LLM Integration](../infrastructure/llm/AGENTS.md) | [Run Guide](../RUN_GUIDE.md) | [Configuration](CONFIGURATION.md)

This guide provides specialized troubleshooting for LLM-powered manuscript review and translation features. For general troubleshooting, see [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md).

## Overview

The LLM review system uses local Ollama LLMs to:
- Generate scientific manuscript reviews (executive summary, quality review, methodology review, improvement suggestions)
- Translate technical abstracts to multiple languages (Chinese, Hindi, Russian, etc.)

**Key Components:**
- `scripts/06_llm_review.py` - Main orchestrator script
- `infrastructure/llm/` - LLM client and utilities
- Ollama server - Local LLM runtime

## Quick Diagnosis

### Check Ollama Status

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check available models
ollama list

# Test Ollama directly
ollama run llama3-gradient "Hello"
```

### Check LLM Review Script

```bash
# Check script can find Ollama
python3 scripts/06_llm_review.py --reviews-only

# Check with verbose logging
export LOG_LEVEL=0
python3 scripts/06_llm_review.py --reviews-only
```

## Common Issues and Solutions

### Issue: "Ollama not available" or "Connection refused"

**Symptoms:**
```
✗ Ollama not available: Connection refused
✗ LLM review skipped (Ollama unavailable)
```

**Diagnosis:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check Ollama process
ps aux | grep ollama

# Check Ollama service status (if installed as service)
systemctl status ollama  # Linux
brew services list | grep ollama  # macOS
```

**Solutions:**

1. **Start Ollama server:**
   ```bash
   # Start in foreground (for testing)
   ollama serve
   
   # Start in background (macOS/Linux)
   ollama serve &
   
   # Start as service (Linux with systemd)
   sudo systemctl start ollama
   sudo systemctl enable ollama  # Auto-start on boot
   ```

2. **Verify Ollama is accessible:**
   ```bash
   # Test connection
   curl http://localhost:11434/api/tags
   
   # Should return JSON with available models
   ```

3. **Check firewall/network:**
   - Ensure port 11434 is not blocked
   - Check if Ollama is bound to correct interface
   - Verify no proxy interfering with localhost connections

**Prevention:**
- Install Ollama as a system service for automatic startup
- Add Ollama health check to startup scripts
- Document Ollama requirements in project setup

### Issue: "No suitable model found"

**Symptoms:**
```
✗ No suitable model found
✗ Available models: []
✗ LLM review skipped (no models available)
```

**Diagnosis:**
```bash
# List available models
ollama list

# Check model preferences
python3 -c "from infrastructure.llm.utils.ollama import DEFAULT_MODEL_PREFERENCES; print(DEFAULT_MODEL_PREFERENCES)"
```

**Solutions:**

1. **Install a recommended model:**
   ```bash
   # Preferred models (in order of preference)
   ollama pull llama3-gradient:latest  # Large context (256K), recommended
   ollama pull llama3.1:latest         # Good balance
   ollama pull llama2:latest            # Widely available
   ollama pull gemma2:2b                # Fast, small
   ```

2. **Verify model installation:**
   ```bash
   # List installed models
   ollama list
   
   # Test model directly
   ollama run llama3-gradient "Test query"
   ```

3. **Check model preferences:**
   - System prefers models in this order: `llama3-gradient`, `llama3.1`, `llama2`, `gemma2:2b`
   - If you have a different model, it will still work but may not be auto-selected
   - You can manually specify model via environment variable (if supported)

**Prevention:**
- Document model requirements in setup instructions
- Include model installation in project setup script
- Add model availability check to pre-flight validation

### Issue: "Timeout" or "Request timeout"

**Symptoms:**
```
✗ Request timeout after 3 attempts: Timeout after 300s
✗ LLM review failed: Timeout
```

**Diagnosis:**
```bash
# Check current timeout settings
env | grep LLM_REVIEW_TIMEOUT

# Test model response time
time ollama run llama3-gradient "Generate a short test response"
```

**Solutions:**

1. **Increase timeout:**
   ```bash
   # Set longer timeout (in seconds)
   export LLM_REVIEW_TIMEOUT=600  # 10 minutes
   python3 scripts/06_llm_review.py --reviews-only
   ```

2. **Use faster model:**
   ```bash
   # Smaller models are faster
   ollama pull gemma2:2b
   # System will auto-select if available
   ```

3. **Reduce input size:**
   ```bash
   # Limit input to LLM (reduces processing time)
   export LLM_MAX_INPUT_LENGTH=250000  # ~62K tokens
   python3 scripts/06_llm_review.py --reviews-only
   ```

4. **Check system resources:**
   ```bash
   # Check CPU/memory usage
   top
   htop  # If available
   
   # Check disk space
   df -h
   ```

**Prevention:**
- Set appropriate timeouts based on model size
- Monitor system resources during LLM operations
- Use smaller models for faster iteration

### Issue: "Manuscript PDF not found"

**Symptoms:**
```
✗ Manuscript PDF not found: project/output/pdf/project_combined.pdf
✗ LLM review skipped (no manuscript PDF)
```

**Diagnosis:**
```bash
# Check if PDF exists
ls -la project/output/pdf/project_combined.pdf

# Check PDF generation
python3 scripts/03_render_pdf.py
```

**Solutions:**

1. **Generate manuscript PDF first:**
   ```bash
   # Run PDF rendering stage
   python3 scripts/03_render_pdf.py
   
   # Or run full pipeline up to PDF stage
   python3 scripts/run_all.py
   ```

2. **Verify PDF location:**
   ```bash
   # Check expected location
   ls -la project/output/pdf/
   
   # Check for alternative names
   ls -la project/output/pdf/*.pdf
   ```

3. **Check PDF generation logs:**
   ```bash
   # Review PDF generation output
   tail -50 project/output/pdf/*_compile.log
   ```

**Prevention:**
- Ensure PDF generation completes before LLM review
- Add PDF existence check to pre-flight validation
- Document PDF generation as prerequisite

### Issue: "PDF text extraction failed"

**Symptoms:**
```
✗ Failed to extract text from PDF
✗ PDF may be corrupted or encrypted
```

**Diagnosis:**
```bash
# Test PDF readability
python3 -c "
from pathlib import Path
import PyPDF2
with open('project/output/pdf/project_combined.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    print(f'Pages: {len(reader.pages)}')
    print(f'Text from first page: {reader.pages[0].extract_text()[:100]}')
"
```

**Solutions:**

1. **Check PDF is not corrupted:**
   ```bash
   # Try opening PDF manually
   open project/output/pdf/project_combined.pdf  # macOS
   xdg-open project/output/pdf/project_combined.pdf  # Linux
   ```

2. **Regenerate PDF:**
   ```bash
   # Clean and regenerate
   rm -rf project/output/pdf/*
   python3 scripts/03_render_pdf.py
   ```

3. **Check PDF encryption:**
   - Ensure PDF is not password-protected
   - Verify PDF generation doesn't add encryption

**Prevention:**
- Validate PDF after generation
- Test text extraction in PDF generation tests
- Add PDF integrity checks

### Issue: "Review generation failed" or "Empty response"

**Symptoms:**
```
✗ Review generation failed: Empty response from model
✗ Quality review: <empty>
```

**Diagnosis:**
```bash
# Test model directly
ollama run llama3-gradient "Write a 200-word summary of a research paper"

# Check model is loaded
ollama ps
```

**Solutions:**

1. **Check model is loaded:**
   ```bash
   # List loaded models
   ollama ps
   
   # Preload model
   ollama run llama3-gradient "test"
   ```

2. **Increase max tokens:**
   ```bash
   # Allow longer responses
   export LLM_LONG_MAX_TOKENS=8192
   python3 scripts/06_llm_review.py --reviews-only
   ```

3. **Check model memory:**
   ```bash
   # Check available memory
   free -h  # Linux
   vm_stat  # macOS
   
   # Use smaller model if memory constrained
   ollama pull gemma2:2b
   ```

4. **Verify model quality:**
   ```bash
   # Test model with simple query
   ollama run llama3-gradient "Hello, can you write a paragraph?"
   ```

**Prevention:**
- Preload models before first use
- Set appropriate token limits
- Monitor model memory usage
- Use models appropriate for system resources

### Issue: "Translation failed" or "Translation language not configured"

**Symptoms:**
```
✗ Translation failed: Language 'zh' not configured
✗ Translations skipped (no languages configured)
```

**Diagnosis:**
```bash
# Check translation configuration
cat project/manuscript/config.yaml | grep -A 10 "llm:"

# Check environment variables
env | grep TRANSLATION
```

**Solutions:**

1. **Configure translations in config.yaml:**
   ```yaml
   # project/manuscript/config.yaml
   llm:
     translations:
       enabled: true
       languages:
         - zh  # Chinese (Simplified)
         - hi  # Hindi
         - ru  # Russian
   ```

2. **Or disable translations:**
   ```yaml
   # project/manuscript/config.yaml
   llm:
     translations:
       enabled: false
   ```

3. **Run translations only:**
   ```bash
   # Run translations separately
   python3 scripts/06_llm_review.py --translations-only
   ```

**Prevention:**
- Document translation configuration in setup
- Add translation config validation
- Provide example config.yaml with translations

### Issue: "Review quality validation failed"

**Symptoms:**
```
✗ Review quality validation failed: Too repetitive
✗ Review regenerated (attempt 2/3)
```

**Diagnosis:**
```bash
# Check review output
cat project/output/llm/quality_review.md

# Check validation logs
export LOG_LEVEL=0
python3 scripts/06_llm_review.py --reviews-only
```

**Solutions:**

1. **Review validation is automatic:**
   - System automatically retries if quality is poor
   - Up to 3 attempts per review
   - Validation checks for repetition, length, format

2. **If validation consistently fails:**
   - Check model quality (try different model)
   - Increase max tokens for longer responses
   - Review validation thresholds (may need adjustment)

3. **Manual review:**
   ```bash
   # Review generated content
   cat project/output/llm/executive_summary.md
   cat project/output/llm/quality_review.md
   ```

**Prevention:**
- Use high-quality models for reviews
- Set appropriate token limits
- Monitor validation failure rates

### Issue: "Context window exceeded" or "Input too long"

**Symptoms:**
```
✗ Input exceeds context window: 300000 chars > 262144 limit
✗ Truncating input to fit context window
```

**Diagnosis:**
```bash
# Check manuscript size
wc -c project/output/pdf/project_combined.pdf

# Check input length limit
env | grep LLM_MAX_INPUT_LENGTH
```

**Solutions:**

1. **Increase context window (if model supports):**
   ```bash
   # For models with large context (e.g., llama3-gradient: 256K)
   export LLM_CONTEXT_WINDOW=262144
   python3 scripts/06_llm_review.py --reviews-only
   ```

2. **Limit input size:**
   ```bash
   # Reduce input to fit smaller models
   export LLM_MAX_INPUT_LENGTH=100000  # ~25K tokens
   python3 scripts/06_llm_review.py --reviews-only
   ```

3. **Use model with larger context:**
   ```bash
   # Install model with large context window
   ollama pull llama3-gradient:latest  # 256K context
   ```

**Prevention:**
- Use models with large context windows for long manuscripts
- Set appropriate input length limits
- Document model context window requirements

### Issue: "Model thinking mode" (qwen3 models)

**Symptoms:**
```
✗ Model response contains thinking tokens
✗ Review contains <think>...</think> tags
```

**Diagnosis:**
- Some models (e.g., qwen3) use "thinking" mode
- Thinking tokens appear in output
- System should handle this automatically

**Solutions:**

1. **Use recommended models:**
   - System prefers models without thinking mode
   - `llama3-gradient`, `llama3.1`, `llama2` don't use thinking mode

2. **If using qwen3:**
   - System attempts to strip thinking tokens
   - May require manual cleanup if stripping fails

**Prevention:**
- Use recommended models from DEFAULT_MODEL_PREFERENCES
- Avoid models with thinking mode for reviews
- Document model compatibility

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
python3 scripts/06_llm_review.py --reviews-only
```

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
python3 -c "from infrastructure.llm.core.client import LLMClient; print('OK')"

# Check Ollama utilities
python3 -c "from infrastructure.llm.utils.ollama import is_ollama_running; print(is_ollama_running())"

# Test LLM client
python3 -c "
from infrastructure.llm.core.client import LLMClient
client = LLMClient()
print('Available:', client.check_connection())
"
```

### Check PDF and Text Extraction

```bash
# Check PDF exists
ls -la project/output/pdf/project_combined.pdf

# Test PDF text extraction
python3 -c "
from pathlib import Path
import PyPDF2
pdf_path = Path('project/output/pdf/project_combined.pdf')
if pdf_path.exists():
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f'Pages: {len(reader.pages)}')
        print(f'First 200 chars: {reader.pages[0].extract_text()[:200]}')
else:
    print('PDF not found')
"
```

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

## Getting Help

### Check Logs

```bash
# Enable debug logging
export LOG_LEVEL=0
python3 scripts/06_llm_review.py --reviews-only 2>&1 | tee llm_review.log

# Review log file
cat llm_review.log | grep -i error
```

### Review Generated Files

```bash
# Check review outputs
ls -la project/output/llm/

# Review metadata
cat project/output/llm/review_metadata.json

# Check individual reviews
cat project/output/llm/executive_summary.md
cat project/output/llm/quality_review.md
```

### Common Error Patterns

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

## See Also

- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - General troubleshooting
- [LLM Integration](../infrastructure/llm/AGENTS.md) - LLM system documentation
- [Run Guide](../RUN_GUIDE.md) - Pipeline orchestration
- [Configuration](CONFIGURATION.md) - Configuration system
- [LLM Standards](../.cursorrules/llm_standards.md) - LLM development standards

---

**Last Updated**: Documentation review 2025-01-03
**Status**: Complete troubleshooting guide for LLM review features
