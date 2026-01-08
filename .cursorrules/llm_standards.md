# LLM Integration Standards

## Overview

Standards and patterns for integrating with the LLM infrastructure module (`infrastructure/llm/`). This guide covers Ollama integration, response modes, validation, and manuscript review patterns.

## Architecture

### Module Structure

```
infrastructure/llm/
├── __init__.py           # Public API exports
├── config.py             # LLMConfig, GenerationOptions
├── core.py               # LLMClient main class
├── context.py            # ConversationContext management
├── templates.py          # ResearchTemplate system
├── validation.py         # OutputValidator
├── ollama_utils.py       # Model discovery utilities
├── cli.py                # Command-line interface
├── AGENTS.md             # Detailed documentation
└── README.md             # Quick reference
```

### Key Classes

| Class | Purpose | Import |
|-------|---------|--------|
| `LLMClient` | Main interface for queries | `from infrastructure.llm import LLMClient` |
| `LLMConfig` | Configuration management | `from infrastructure.llm import LLMConfig` |
| `GenerationOptions` | Per-query generation control | `from infrastructure.llm import GenerationOptions` |
| `OutputValidator` | Response validation | `from infrastructure.llm import OutputValidator` |

## Configuration Patterns

### Environment-Based Configuration

```python
from infrastructure.llm import LLMConfig, LLMClient

# Load from environment (recommended)
config = LLMConfig.from_env()
client = LLMClient(config)
```

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen3:4b` | Default model (128K context, fast) |
| `LLM_TEMPERATURE` | `0.7` | Generation temperature |
| `LLM_MAX_TOKENS` | `2048` | Max tokens per response |
| `LLM_SEED` | `None` | Seed for reproducibility |
| `LLM_TIMEOUT` | `60` | Request timeout (seconds) |

### Programmatic Configuration

```python
# Custom configuration
config = LLMConfig(
    base_url="http://localhost:11434",
    default_model="qwen3:4b",
    temperature=0.7,
    max_tokens=2048,
    seed=42,
    system_prompt="You are an expert researcher.",
)

# Override specific settings
fast_config = config.with_overrides(temperature=0.0, timeout=30.0)
```

## Response Mode Selection

### Choose the Right Mode

| Mode | Use When | Token Limit | Method |
|------|----------|-------------|--------|
| **Short** | Quick answers, definitions | < 200 | `query_short()` |
| **Standard** | General queries | Default config | `query()` |
| **Long** | Detailed analysis, reviews | > 4096 | `query_long()` |
| **Structured** | JSON output needed | Varies | `query_structured()` |
| **Raw** | No system prompt needed | Varies | `query_raw()` |

### Mode Examples

```python
# Short response (< 200 tokens)
answer = client.query_short("What is machine learning?")

# Standard response with context
response = client.query("Explain this concept...")

# Long detailed response (> 4096 tokens)
analysis = client.query_long("Provide analysis...")

# Structured JSON response
result = client.query_structured(
    "Extract key points...",
    schema={"type": "object", "properties": {...}}
)

# Raw (no system prompt)
completion = client.query_raw("Complete: The quick brown fox")
```

## Per-Query Generation Options

### Using GenerationOptions

```python
from infrastructure.llm import GenerationOptions

# Deterministic output
opts = GenerationOptions(
    temperature=0.0,
    seed=42,
)
response = client.query(prompt, options=opts)

# Full control
opts = GenerationOptions(
    temperature=0.7,      # Creativity (0.0=deterministic, 2.0=creative)
    max_tokens=4096,      # Max output tokens
    top_p=0.9,            # Nucleus sampling
    top_k=40,             # Top-k sampling
    seed=42,              # Reproducibility seed
    stop=["END", "STOP"], # Stop sequences
    format_json=True,     # Force JSON output
    repeat_penalty=1.1,   # Repetition penalty
    num_ctx=8192,         # Context window
)
```

### Options Precedence

1. Per-query `GenerationOptions` (highest priority)
2. `LLMConfig` defaults
3. Environment variables (via `from_env()`)

## Validation Patterns

### Output Validation

```python
from infrastructure.llm import OutputValidator

# Validate JSON
data = OutputValidator.validate_json(response)

# Validate response length
OutputValidator.validate_short_response(response)  # < 150 tokens
OutputValidator.validate_long_response(response)   # > 500 tokens

# Validate structure
OutputValidator.validate_structure(data, schema)

# validation
OutputValidator.validate_complete(response, mode="structured", schema=schema)
```

### Review Quality Validation

For manuscript reviews, use the validation functions from the review script:

```python
from scripts import validate_review_quality, is_off_topic

# Check for off-topic responses first
if is_off_topic(response):
    # Response is confused - retry with format enforcement
    pass

# Validate review quality (includes format compliance checks)
is_valid, issues, details = validate_review_quality(response, "executive_summary")

if not is_valid:
    for issue in issues:
        print(f"  Issue: {issue}")

# Check format compliance details
format_info = details.get("format_compliance", {})
if format_info.get("emojis_found"):
    print(f"  Emojis detected: {format_info['emojis_found']}")
```

### Off-Topic Detection

Detect when the LLM has gone off-topic:

```python
from scripts import is_off_topic

# Patterns detected:
# - Email format (Re:, Dear, Subject:, From:, To:)
# - AI assistant phrases ("I'm happy to help", "As an AI")
# - Code responses when not expected
# - Casual greetings (Hi, Hello)

if is_off_topic(response):
    # Reset context and retry
    client.reset()
    response = retry_with_format_enforcement(prompt)
```

### Format Compliance Validation

The validation system uses **structure-only validation** for general-purpose use. Emojis and tables are allowed to give LLMs formatting flexibility.

```python
from scripts import (
    detect_conversational_phrases,
    check_format_compliance,
    is_off_topic,
)

# Check for off-topic content first (most critical)
if is_off_topic(response):
    client.reset()  # Reset context
    # Retry with reinforced prompt
    
# Check conversational phrases (warning only)
phrases = detect_conversational_phrases(response)

# Format compliance check (now only conversational phrases)
is_compliant, issues, details = check_format_compliance(response)

# Issues are logged as warnings, not hard failures
if not is_compliant:
    logger.warning(f"Format warnings: {', '.join(issues)}")
```

**Validation Approach:**

| Check | Type | Action on Fail |
|-------|------|----------------|
| Off-topic content | Critical | Retry with context reset |
| Word count below minimum | Structural | Retry |
| Missing required headers | Structural | Retry |
| Conversational phrases | Warning | Log only |
| Emojis | Allowed | No action |
| Tables | Allowed | No action |

**Allowed Formats:**
- Emojis (✅ 🔑 📊 etc.) - useful for visual emphasis
- Markdown tables - useful for structured data
- Any valid markdown formatting

## Manuscript Review Patterns

### Review Generation

```python
from infrastructure.llm import LLMClient, LLMConfig, GenerationOptions

# Initialize client
config = LLMConfig.from_env()
client = LLMClient(config)

# Generation options for reviews
options = GenerationOptions(
    temperature=0.3,       # Low temperature for consistency
    max_tokens=4096,       # Allow long responses
    seed=42,               # Reproducibility
)

# Use query() directly with detailed templates
# Avoid query_long() which adds conflicting instructions
response = client.query(template_prompt, options=options)
```

### Retry with Reinforced Prompt

When off-topic content is detected, the retry includes a reinforced prompt:

```python
# On retry after off-topic detection
if had_off_topic:
    current_prompt = (
        "IMPORTANT: You must review the ACTUAL manuscript text provided below. "
        "Do NOT generate hypothetical content, generic book descriptions, or "
        "unrelated topics. Your review must reference specific content from "
        "the manuscript.\n\n" + prompt
    )
    client.reset()  # Always reset context for off-topic retries
```

The prompt templates now use a **manuscript-first structure** with clear boundary markers:

```
=== MANUSCRIPT BEGIN ===
{full manuscript text}
=== MANUSCRIPT END ===

TASK: [specific review task]
REQUIREMENTS: [structural requirements]
```

This structure ensures the LLM focuses on the actual manuscript content.

### Validation for Different Review Types

```python
def validate_review_quality(response: str, review_type: str) -> Tuple[bool, List[str]]:
    issues = []
    
    # Always check off-topic first
    if is_off_topic(response):
        issues.append("Response appears off-topic or confused")
        return False, issues
    
    # Type-specific validation
    if review_type == "executive_summary":
        # Check for required sections
        headers = ["Overview", "Key Contributions", "Methodology", "Results", "Significance"]
        found = sum(1 for h in headers if h.lower() in response.lower())
        if found < 3:
            issues.append(f"Missing expected structure (found {found}/5)")
    
    elif review_type == "quality_review":
        # Check for scoring
        if not re.search(r'\*\*Score:\s*\d\*\*|Score:\s*\d', response, re.I):
            issues.append("Missing scoring rubric")
    
    elif review_type == "improvement_suggestions":
        # Check for priority sections
        priorities = ["high priority", "medium priority", "low priority"]
        found = sum(1 for p in priorities if p in response.lower())
        if found < 2:
            issues.append(f"Missing priority sections (found {found}/3)")
    
    elif review_type == "translation":
        # Check for English abstract and translation sections
        has_english = any([
            "english abstract" in response.lower(),
            "## english" in response.lower(),
        ])
        has_translation = any([
            "translation" in response.lower(),
            "chinese" in response.lower(),
            "hindi" in response.lower(),
            "russian" in response.lower(),
        ])
        if not has_english:
            issues.append("Missing English abstract section")
        if not has_translation:
            issues.append("Missing translation section")
    
    return len(issues) == 0, issues
```

## Error Handling

### LLM-Specific Exceptions

```python
from infrastructure.core.exceptions import (
    LLMConnectionError,
    LLMTemplateError,
    ValidationError,
    ContextLimitError,
)

try:
    response = client.query(prompt)
except LLMConnectionError as e:
    # Ollama not running or unreachable
    logger.error(f"Connection failed: {e.context}")
    # Fallback or graceful degradation
except ContextLimitError as e:
    # Context too long
    client.reset()
    response = client.query(prompt)  # Retry with fresh context
except ValidationError as e:
    # Response validation failed
    logger.warning(f"Validation issue: {e}")
```

### Connection Checking

```python
from infrastructure.llm import is_ollama_running, select_best_model

# Check before starting
if not is_ollama_running():
    print("Ollama not running - start with: ollama serve")
    sys.exit(1)

# Select best available model
model = select_best_model()
if not model:
    print("No Ollama models found - pull with: ollama pull qwen3:4b")
    sys.exit(1)

config = LLMConfig(default_model=model)
```

## Testing Standards

### No Mocks Policy

Following the project's **No Mocks Policy**, LLM tests use:

1. **Pure Logic Tests** - Configuration, validation, context (no network)
2. **Integration Tests** - Marked with `@pytest.mark.requires_ollama`

### Test Examples

```python
import pytest

# Pure logic test (no Ollama required)
def test_config_from_env(clean_llm_env):
    """Test configuration loading."""
    os.environ["OLLAMA_HOST"] = "http://test:11434"
    config = LLMConfig.from_env()
    assert config.base_url == "http://test:11434"

# Integration test (requires Ollama)
@pytest.mark.requires_ollama
class TestLLMIntegration:
    @pytest.fixture(autouse=True)
    def check_ollama(self):
        if not is_ollama_running():
            pytest.skip("Ollama not running")
    
    def test_query(self):
        client = LLMClient()
        response = client.query("Hello")
        assert len(response) > 0
```

### Running Tests

```bash
# Pure logic tests only (fast, no Ollama required)
pytest tests/infrastructure/llm/ -m "not requires_ollama" -v

# All tests (requires running Ollama)
pytest tests/infrastructure/llm/ -v

# Integration tests only
pytest tests/infrastructure/llm/ -m requires_ollama -v

# With coverage
pytest tests/infrastructure/llm/ --cov=infrastructure/llm --cov-report=html
```

## Streaming Patterns

### Basic Streaming

```python
# Stream response to stdout
for chunk in client.stream_query("Write a poem about AI"):
    print(chunk, end="", flush=True)
print()  # Final newline
```

### Streaming with Options

```python
opts = GenerationOptions(temperature=0.9, seed=42)

for chunk in client.stream_query("Creative writing...", options=opts):
    print(chunk, end="", flush=True)
```

### Mode-Specific Streaming

```python
# Short mode streaming
for chunk in client.stream_short("Quick answer..."):
    process_chunk(chunk)

# Long mode streaming
for chunk in client.stream_long("Detailed explanation..."):
    process_chunk(chunk)
```

## Template System

### Built-in Templates

| Template | Purpose | Parameters |
|----------|---------|------------|
| `summarize_abstract` | Summarize research abstracts | `text` |
| `literature_review` | Synthesize multiple summaries | `summaries` |
| `code_doc` | Generate Python docstrings | `code` |
| `data_interpret` | Interpret statistical results | `stats` |
| `manuscript_translation_abstract` | Generate technical abstract and translate to target language | `text`, `target_language` |

### Using Templates

```python
# Apply a template
summary = client.apply_template(
    "summarize_abstract",
    text=abstract_text
)

# List available templates
from infrastructure.llm.templates import TEMPLATE_REGISTRY
print(list(TEMPLATE_REGISTRY.keys()))
```

### Creating Custom Templates

```python
from infrastructure.llm.templates import ResearchTemplate

class MethodologyReview(ResearchTemplate):
    template_str = """Analyze the methodology of this research:

${content}

Provide your analysis with these sections:
## Strengths
## Weaknesses  
## Suggestions for Improvement
"""

# Register and use
template = MethodologyReview()
result = template.render(content=methodology_text)
```

### Translation Templates

The system includes a translation template for generating technical abstracts in multiple languages:

```python
from infrastructure.llm import ManuscriptTranslationAbstract, TRANSLATION_LANGUAGES

# Supported languages
TRANSLATION_LANGUAGES = {
    "zh": "Chinese (Simplified)",
    "hi": "Hindi",
    "ru": "Russian",
}

# Generate translation
template = ManuscriptTranslationAbstract()
prompt = template.render(
    text=manuscript_text,
    target_language=TRANSLATION_LANGUAGES["zh"]
)
response = client.query(prompt, options=options)
```

**Configuration:**

Translations are configured in `project/manuscript/config.yaml`:

```yaml
llm:
  translations:
    enabled: true
    languages:
      - zh  # Chinese (Simplified)
      - hi  # Hindi
      - ru  # Russian
```

The translation template generates:
1. A 200-400 word technical abstract in English
2. A translation in the target language
3. Both sections with proper headers

## Context Management

### Automatic Context

```python
client = LLMClient()

# Multi-turn conversation (context maintained)
response1 = client.query("What is X?")
response2 = client.query("Can you elaborate?")  # Has context from response1
```

### Manual Context Control

```python
# Reset context (clears history, re-injects system prompt)
client.reset()

# Query with fresh context
response = client.query("New topic", reset_context=True)

# Change system prompt
client.set_system_prompt("You are now a different persona...")
```

## Common Failure Modes

### Off-Topic Detection

The most critical failure mode is when the LLM generates content unrelated to the manuscript. Off-topic patterns include:

| Pattern Type | Examples | Action |
|--------------|----------|--------|
| **AI refusal** | "I can't help", "I don't have access" | Retry with context reset |
| **Generic content** | "This book is", "Chapter 1 deals with" | Retry with reinforced prompt |
| **External URLs** | http://, https:// links | Retry (indicates hallucination) |
| **Unrelated code** | CMakeLists.txt, .cpp files | Retry |
| **Form/registration** | "must be 18 years old", "valid email" | Retry |

### Repetition Detection

LLMs can sometimes get stuck in output loops, repeating the same content. The validation system detects this:

| Unique Ratio | Severity | Action |
|--------------|----------|--------|
| > 80% | Normal | Pass validation |
| 50-80% | Warning | Log warning, continue |
| < 50% | Error | Fail validation, retry |

```python
from infrastructure.llm import detect_repetition, deduplicate_sections

# Check for repetition
has_rep, duplicates, unique_ratio = detect_repetition(response)

if unique_ratio < 0.5:
    # Severe repetition - retry with different temperature
    client.reset()
    response = client.query(prompt, options=GenerationOptions(temperature=0.5))

# Post-process to clean up any remaining repetition
cleaned = deduplicate_sections(response, max_repetitions=2)
```

The validation is automatically integrated into `validate_review_quality()`:

```python
is_valid, issues, details = validate_review_quality(response, "executive_summary")

# Check repetition details
if details.get("repetition", {}).get("has_repetition"):
    print(f"Warning: {details['repetition']['unique_ratio']:.0%} unique content")
```

### Troubleshooting

**Issue: Response is completely off-topic (hallucinated content)**
```python
# Detected by is_off_topic() - checks for:
# - AI refusal phrases ("I can't help")
# - Generic book/guide language
# - External URLs
# - Unrelated programming content

# Resolution: Context reset + reinforced prompt on retry
if had_off_topic:
    client.reset()
    current_prompt = "IMPORTANT: Review the ACTUAL manuscript..." + prompt
```

**Issue: Response too short**

The validation system uses minimum word counts to ensure substantive reviews:

| Review Type | Minimum Words | Template Target | Notes |
|------------|---------------|-----------------|-------|
| executive_summary | 250 | 400-600 | Full manuscript overview |
| quality_review | 300 | 500-700 | Detailed quality assessment |
| methodology_review | 300 | 500-700 | Methods and structure analysis |
| improvement_suggestions | 200 | 500-800 | Focused actionable items |
| translation | 400 | 200-400 (English) + translation | Technical abstract + target language |

```python
# Small models (3B-8B) get 20% lower thresholds automatically
# e.g., improvement_suggestions minimum: 200 → 160 for small models
```

**Issue: Missing required headers**
```python
# Each review type expects specific headers
# Validation is flexible - accepts variations:
# "Overview" OR "Summary" OR "Introduction"
# "Methodology" OR "Methods" OR "Approach"

# Only requires 1+ sections to pass (very flexible)
```

**Issue: Conversational AI phrases**
```python
# Detected phrases like:
# "Based on the document you shared"
# "I'll help you understand"
# "Let me know if you need more"

# These are logged as warnings only - not retry triggers
```

## Best Practices

### DO

```python
# Use environment configuration
config = LLMConfig.from_env()

# Use GenerationOptions for per-query control
opts = GenerationOptions(temperature=0.0, seed=42)

# Validate responses before using
is_valid, issues = validate_review_quality(response, review_type)

# Check off-topic before structural validation
if is_off_topic(response):
    # Retry immediately
    
# Use format enforcement on retry
if attempt > 0:
    prompt = FORMAT_ENFORCEMENT[type] + original_prompt

# Check connection before long operations
if not is_ollama_running():
    handle_no_ollama()
```

### DON'T

```python
# Don't use query_long() with detailed templates (double instructions)
response = client.query_long(detailed_template)  # BAD

# Don't skip off-topic detection
is_valid, issues = validate_review_quality(response, type)  # Check off-topic first

# Don't ignore validation failures
if not is_valid:
    pass  # BAD - should retry or handle

# Don't hardcode model names unnecessarily
config = LLMConfig(default_model="some-model")  # Use env vars or from_env() instead

# Don't mock LLM responses in tests
with patch("infrastructure.llm.LLMClient"):  # NEVER use mocks
```

## Checklist

### Before Using LLM

- [ ] Ollama running (`ollama serve`)
- [ ] Model available (`ollama list`)
- [ ] Environment variables configured
- [ ] Error handling in place

### For Review Generation

- [ ] Use `query()` not `query_long()` with detailed templates
- [ ] Implement off-topic detection
- [ ] Add format enforcement for retries
- [ ] Validate response structure
- [ ] Track best response across retries
- [ ] Log validation issues

### For Testing

- [ ] Pure logic tests without network
- [ ] Integration tests marked `@pytest.mark.requires_ollama`
- [ ] No mocks or patches
- [ ] Clean environment fixtures
- [ ] Coverage for all validation paths

## See Also

- [infrastructure_modules.md](infrastructure_modules.md) - Module development standards
- [testing_standards.md](testing_standards.md) - Testing patterns
- [error_handling.md](error_handling.md) - Exception handling
- [python_logging.md](python_logging.md) - Logging standards
- [../infrastructure/llm/AGENTS.md](../infrastructure/llm/AGENTS.md) - Detailed LLM documentation
- [../infrastructure/llm/README.md](../infrastructure/llm/README.md) - Quick reference

---

**Version**: 1.1.0  
**Last Updated**: 2025-12-02  
**Status**: (includes translation feature)  
**Maintainer**: Template Team

