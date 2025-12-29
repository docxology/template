# LLM CLI Module

## Overview

The `infrastructure/llm/cli/` directory contains the command-line interface for the LLM (Large Language Model) infrastructure. This thin orchestrator provides terminal access to LLM functionality, wrapping the core LLM modules with user-friendly command-line operations.

## Directory Structure

```
infrastructure/llm/cli/
├── AGENTS.md               # This technical documentation
├── __init__.py            # Package initialization
└── main.py                # CLI implementation
```

## CLI Architecture

### Thin Orchestrator Pattern

The CLI follows the **thin orchestrator pattern**:
- **Business Logic**: All LLM operations in `infrastructure.llm.core/`
- **Orchestration**: CLI handles argument parsing and I/O
- **Dependencies**: Imports from core LLM modules
- **Error Handling**: Graceful failure with informative messages

### Main CLI Implementation (`main.py`)

**Command-line interface providing access to LLM functionality:**

#### Core Features
- **Query Commands**: Interactive LLM queries with various modes
- **Connection Testing**: Ollama server connectivity verification
- **Model Management**: Available model discovery and selection
- **Template Application**: Pre-built research prompt templates
- **Configuration**: Environment-based and command-line configuration

#### Supported Commands

**1. Query Command**
```bash
# Basic query
python3 -m infrastructure.llm.cli query "What is machine learning?"

# Response modes
python3 -m infrastructure.llm.cli query --short "Summarize this concept"
python3 -m infrastructure.llm.cli query --long "Explain in detail"
python3 -m infrastructure.llm.cli query --structured --schema research.json

# Streaming output
python3 -m infrastructure.llm.cli query --stream "Write a poem"

# Generation control
python3 -m infrastructure.llm.cli query --temperature 0.0 --seed 42 --max-tokens 500 "Deterministic response"
```

**2. Connection Testing**
```bash
# Check Ollama availability
python3 -m infrastructure.llm.cli check

# Expected output:
# ✓ Connected to Ollama at http://localhost:11434
# ✓ Default model 'gemma3:4b' is available
```

**3. Model Discovery**
```bash
# List available models
python3 -m infrastructure.llm.cli models

# Expected output:
# Available models:
# • gemma3:4b (4.0B parameters, 128K context)
# • llama3.2:3b (3.2B parameters, 128K context)
# • codellama:7b (7.3B parameters, 16K context)
```

**4. Template Application**
```bash
# List available templates
python3 -m infrastructure.llm.cli template --list

# Apply research template
python3 -m infrastructure.llm.cli template summarize_abstract --input "Abstract text here..."

# Template with custom parameters
python3 -m infrastructure.llm.cli template literature_review --papers "paper1,paper2" --focus "methodology"
```

## Command Reference

### Query Command Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--short` | `-s` | Short response (< 150 tokens) | False |
| `--long` | `-l` | Long response (> 500 tokens) | False |
| `--structured` | | JSON-structured response | False |
| `--stream` | | Stream response in real-time | False |
| `--model` | `-m` | Override default model | Auto-detected |
| `--temperature` | `-t` | Sampling temperature (0.0-2.0) | 0.7 |
| `--max-tokens` | | Maximum tokens to generate | Mode-dependent |
| `--seed` | | Random seed for reproducibility | None |
| `--schema` | | JSON schema file for structured mode | None |
| `--system-prompt` | | Custom system prompt | Default research assistant |

### Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--verbose`, `-v` | Enable verbose logging | False |
| `--quiet`, `-q` | Suppress non-essential output | False |
| `--config` | Path to config file | Environment-based |

## Implementation Details

### Command Structure

**Main Entry Point:**
```python
def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM CLI for research assistance",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global options
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--quiet', '-q', action='store_true')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query the LLM')
    # ... query options ...

    # Check command
    check_parser = subparsers.add_parser('check', help='Check Ollama connection')

    # Models command
    models_parser = subparsers.add_parser('models', help='List available models')

    # Template command
    template_parser = subparsers.add_parser('template', help='Apply research templates')

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if args.command == 'query':
        query_command(args)
    elif args.command == 'check':
        check_command(args)
    # ... other commands ...
```

### Query Command Implementation

**Query Execution Flow:**
1. **Configuration Loading**: Load from environment and apply overrides
2. **Model Selection**: Auto-detect best model or use specified model
3. **Connection Verification**: Ensure Ollama server is available
4. **Option Building**: Construct `GenerationOptions` from arguments
5. **Query Execution**: Call appropriate LLMClient method
6. **Output Handling**: Display results with appropriate formatting

**Mode-Specific Logic:**
```python
def query_command(args):
    """Handle query command execution."""
    # Load configuration
    config = LLMConfig.from_env()

    # Apply command-line overrides
    if args.model:
        config = config.with_overrides(default_model=args.model)

    # Auto-select best model if none specified
    if not args.model and is_ollama_running():
        best_model = select_best_model()
        if best_model:
            config = config.with_overrides(default_model=best_model)

    # Create client
    client = LLMClient(config)

    # Verify connection
    if not client.check_connection():
        print("❌ Error: Cannot connect to Ollama server", file=sys.stderr)
        print("💡 Start Ollama with: ollama serve", file=sys.stderr)
        sys.exit(1)

    # Build generation options
    options = GenerationOptions(
        temperature=args.temperature,
        max_tokens=get_max_tokens_for_mode(args),
        seed=args.seed if args.seed is not None else None,
        # ... other options
    )

    # Execute query based on mode
    if args.stream:
        stream_response(client, args.prompt, args, options)
    else:
        execute_query(client, args.prompt, args, options)
```

### Response Mode Handling

**Short Mode (< 150 tokens):**
```python
if args.short:
    response = client.query_short(args.prompt, options=options)
    # Additional validation for short responses
```

**Long Mode (> 500 tokens):**
```python
if args.long:
    response = client.query_long(args.prompt, options=options)
    # Additional validation for comprehensive responses
```

**Structured Mode (JSON):**
```python
if args.structured:
    schema = load_json_schema(args.schema)
    response = client.query_structured(args.prompt, schema=schema, options=options)
    # JSON validation and pretty printing
```

**Streaming Mode:**
```python
if args.stream:
    for chunk in client.stream_query(args.prompt, options=options):
        print(chunk, end="", flush=True)
    print()  # Final newline
```

## Configuration Integration

### Environment Variable Support

**CLI Respects All LLM Environment Variables:**
```bash
# Model and connection
OLLAMA_HOST=http://localhost:11434 OLLAMA_MODEL=gemma3:4b python3 -m infrastructure.llm.cli query "test"

# Generation parameters
LLM_TEMPERATURE=0.0 LLM_SEED=42 python3 -m infrastructure.llm.cli query "deterministic output"

# Context and limits
LLM_CONTEXT_WINDOW=131072 LLM_MAX_TOKENS=4096 python3 -m infrastructure.llm.cli query "long context"
```

### Command-Line Overrides

**CLI Arguments Override Environment:**
```bash
# Override model selection
python3 -m infrastructure.llm.cli query --model llama3.2:3b "test query"

# Override generation parameters
python3 -m infrastructure.llm.cli query --temperature 0.0 --max-tokens 100 "constrained response"
```

## Error Handling and User Experience

### Connection Error Handling

**Graceful Connection Failures:**
```python
# Connection check with helpful error messages
if not client.check_connection():
    print("❌ Error: Cannot connect to Ollama server", file=sys.stderr)
    print("💡 Start Ollama with: ollama serve", file=sys.stderr)
    print("💡 Check status with: python3 -m infrastructure.llm.cli check", file=sys.stderr)
    sys.exit(1)
```

### Model Availability Checking

**Automatic Model Selection:**
```python
# Auto-discover best available model
if is_ollama_running():
    best_model = select_best_model()
    if best_model:
        print(f"📋 Using model: {best_model}")
        config = config.with_overrides(default_model=best_model)
    else:
        print("⚠️  No suitable models found. Install with: ollama pull gemma3:4b")
```

### Input Validation

**Prompt Validation:**
```python
if not args.prompt or not args.prompt.strip():
    print("❌ Error: Query prompt cannot be empty", file=sys.stderr)
    sys.exit(1)

if len(args.prompt.strip()) < 3:
    print("⚠️  Warning: Very short prompt may produce poor results")
```

## Output Formatting

### Response Display

**Standard Output:**
```python
# Direct output for piping/scripting
print(response)
```

**Verbose Mode:**
```python
if args.verbose:
    print(f"📋 Model: {client.config.default_model}")
    print(f"🌡️  Temperature: {options.temperature}")
    print(f"🎯 Max tokens: {options.max_tokens}")
    print(f"🔢 Seed: {options.seed}")
    print("-" * 50)
print(response)
```

### Structured Output

**JSON Mode Formatting:**
```python
if args.structured:
    try:
        # Parse and validate JSON
        data = json.loads(response)
        # Pretty print for readability
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print("❌ Error: Response is not valid JSON", file=sys.stderr)
        print(response, file=sys.stderr)
        sys.exit(1)
```

## Integration with Core Modules

### Dependencies

**Core LLM Infrastructure:**
- `infrastructure.llm.core.client` - LLMClient for queries
- `infrastructure.llm.core.config` - Configuration management
- `infrastructure.llm.utils.ollama` - Ollama utilities
- `infrastructure.llm.templates` - Template system

**Shared Infrastructure:**
- `infrastructure.core.logging_utils` - Logging integration
- `infrastructure.core.exceptions` - Error handling

### Import Structure

**Clean Separation:**
```python
# Core functionality imports
from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import LLMConfig, GenerationOptions

# Utility imports
from infrastructure.llm.utils.ollama import select_best_model, is_ollama_running

# Shared infrastructure
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMConnectionError
```

## Testing

### CLI Testing

**Command Testing:**
```python
def test_query_command(capsys):
    """Test query command execution."""
    # Mock LLM client
    with patch('infrastructure.llm.cli.LLMClient') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.query.return_value = "Test response"

        # Execute command
        args = argparse.Namespace(prompt="test query", short=False, long=False, ...)
        query_command(args)

        # Verify output
        captured = capsys.readouterr()
        assert "Test response" in captured.out
```

**Error Testing:**
```python
def test_connection_failure(capsys):
    """Test graceful connection failure."""
    with patch('infrastructure.llm.cli.LLMClient') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.check_connection.return_value = False

        args = argparse.Namespace(prompt="test", ...)
        with pytest.raises(SystemExit):
            query_command(args)

        captured = capsys.readouterr()
        assert "Cannot connect to Ollama" in captured.err
```

## Performance Considerations

### Response Time Optimization

**Connection Reuse:**
- LLMClient maintains connection across queries
- Avoids reconnection overhead
- Context preservation for follow-up queries

**Streaming for Large Responses:**
- Real-time output for long responses
- Reduced memory usage for large content
- User feedback during generation

### Resource Management

**Memory Efficiency:**
- Streaming responses prevent large memory allocation
- Context pruning for long conversations
- Automatic cleanup of resources

## Troubleshooting

### Common Issues

**Connection Problems:**
```bash
# Check Ollama status
python3 -m infrastructure.llm.cli check

# If not running:
ollama serve  # Start in another terminal

# Check model availability
python3 -m infrastructure.llm.cli models
```

**Model Issues:**
```bash
# Install required model
ollama pull gemma3:4b

# Check model loading
ollama ps
```

**Configuration Issues:**
```bash
# Check environment variables
env | grep -E "(OLLAMA|LLM)_"

# Test with explicit configuration
OLLAMA_HOST=http://localhost:11434 python3 -m infrastructure.llm.cli check
```

### Debug Mode

**Verbose Operation:**
```bash
# Enable debug logging
LOG_LEVEL=0 python3 -m infrastructure.llm.cli query --verbose "debug test"

# Check detailed connection info
python3 -c "
from infrastructure.llm.core.client import LLMClient
client = LLMClient()
print(f'Connected: {client.check_connection()}')
print(f'Available models: {client.get_available_models()}')
"
```

## Usage Examples

### Basic Research Assistance

**Quick Queries:**
```bash
# Define a concept
python3 -m infrastructure.llm.cli query --short "What is a neural network?"

# Get detailed explanation
python3 -m infrastructure.llm.cli query --long "Explain backpropagation algorithm"

# Structured analysis
python3 -m infrastructure.llm.cli query --structured "Analyze this dataset" --schema analysis_schema.json
```

### Research Workflow Integration

**Manuscript Review:**
```bash
# Review paper section
cat manuscript/methodology.md | python3 -m infrastructure.llm.cli query "Review this methodology section for clarity and completeness"

# Generate abstract summary
python3 -m infrastructure.llm.cli template summarize_abstract --input "$(cat manuscript/abstract.md)"
```

### Development Assistance

**Code Documentation:**
```bash
# Generate docstring
python3 -m infrastructure.llm.cli query "Generate a Python docstring for this function" --input "$(cat src/analysis.py)"
```

## Future Enhancements

### Planned Features

**Enhanced CLI Capabilities:**
- **Interactive Mode**: Multi-turn conversations
- **Batch Processing**: Multiple queries from file
- **Output Formatting**: Markdown, JSON, CSV export
- **Template Management**: Custom template creation and management
- **History**: Query history and favorites

**Integration Improvements:**
- **Pipe Support**: Accept input from stdin
- **File Output**: Save responses to files
- **Progress Indication**: Progress bars for long operations
- **Error Recovery**: Automatic retry with backoff

## See Also

**Related Documentation:**
- [`../core/AGENTS.md`](../core/AGENTS.md) - Core LLM functionality
- [`../templates/AGENTS.md`](../templates/AGENTS.md) - Template system
- [`../utils/AGENTS.md`](../utils/AGENTS.md) - LLM utilities

**System Documentation:**
- [`../../../AGENTS.md`](../../../AGENTS.md) - LLM module overview
- [`../../../infrastructure/core/AGENTS.md`](../../../infrastructure/core/AGENTS.md) - Core infrastructure
- [`../../../../docs/operational/LLM_REVIEW_TROUBLESHOOTING.md`](../../../../docs/operational/LLM_REVIEW_TROUBLESHOOTING.md) - LLM troubleshooting guide