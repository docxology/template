# LLM Utilities Module

## Overview

The `infrastructure/llm/utils/` directory contains utility functions for Ollama model discovery, server management, and connection health monitoring. These utilities provide the operational support needed for reliable LLM interactions in research workflows.

## Directory Structure

```text
infrastructure/llm/utils/
├── AGENTS.md               # This technical documentation
├── __init__.py            # Package exports
└── ollama.py              # Ollama server and model utilities
```

## Key Components

### Ollama Utilities (`ollama.py`)

**Ollama server and model management utilities:**

#### Server Status Checking

**Connection Health Monitoring:**

```python
def is_ollama_running(base_url: str = "http://localhost:11434", timeout: float = 2.0) -> bool:
    """Check if Ollama server is running and responding.

    Performs a quick health check by querying the /api/tags endpoint.
    Uses short timeout to avoid blocking operations.

    Args:
        base_url: Ollama server URL
        timeout: Request timeout in seconds

    Returns:
        True if server is responding, False otherwise
    """
```

**Detailed Health Assessment:**

```python
def check_ollama_health(base_url: str = "http://localhost:11434",
                       timeout: float = 5.0) -> Dict[str, Any]:
    """Perform detailed Ollama server health check.

    Returns health information including:
    - Server responsiveness
    - Available models
    - API version information
    - Response time metrics

    Args:
        base_url: Ollama server URL
        timeout: Request timeout in seconds

    Returns:
        Dictionary with health status and metadata
    """
```

#### Model Discovery and Selection

**Available Model Listing:**

```python
def get_available_models(base_url: str = "http://localhost:11434",
                        timeout: float = 10.0) -> List[Dict[str, Any]]:
    """Get list of available models from Ollama server.

    Queries the /api/tags endpoint to retrieve all installed models
    with their metadata (size, format, parameters, etc.).

    Args:
        base_url: Ollama server URL
        timeout: Request timeout in seconds

    Returns:
        List of model information dictionaries
    """
```

**Intelligent Model Selection:**

```python
def select_best_model(base_url: str = "http://localhost:11434",
                     preferences: Optional[List[str]] = None,
                     timeout: float = 10.0) -> Optional[str]:
    """Select the best available model based on preferences.

    Iterates through preference list and returns the first available model.
    Uses DEFAULT_MODEL_PREFERENCES if no preferences provided.

    Args:
        base_url: Ollama server URL
        preferences: Ordered list of preferred model names
        timeout: Request timeout in seconds

    Returns:
        Best available model name, or None if no models available
    """
```

**Model Preferences Hierarchy:**

```python
DEFAULT_MODEL_PREFERENCES = [
    "llama3-gradient:latest",  # Large context (256K), reliable, no thinking mode issues
    "llama3.1:latest",        # Good balance of speed and quality
    "llama2:latest",          # Widely available, reliable
    "gemma2:2b",              # Fast, small, good instruction following
    "gemma3:4b",              # Medium size, good quality
    "mistral:latest",         # Alternative
    "codellama:latest",       # Code-focused but can do general tasks
    # Note: qwen3 models use "thinking" mode which requires special handling
]
```

#### Model Preloading and Management

**Model Preloading with Retry:**

```python
def preload_model(model_name: str, base_url: str = "http://localhost:11434",
                 timeout: float = 300.0, max_retries: int = 2) -> Tuple[bool, Optional[str]]:
    """Preload model into memory with retry logic.

    Ensures model is loaded and ready for immediate use.
    Useful for avoiding first-query latency in production.

    Args:
        model_name: Name of model to preload
        base_url: Ollama server URL
        timeout: Maximum time to wait for preload
        max_retries: Number of retry attempts

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
```

**Model Information Retrieval:**

```python
def get_model_info(model_name: str, base_url: str = "http://localhost:11434",
                  timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific model.

    Retrieves model metadata including:
    - Model size and parameters
    - Context window size
    - Quantization format
    - License information

    Args:
        model_name: Name of model to query
        base_url: Ollama server URL
        timeout: Request timeout in seconds

    Returns:
        Model information dictionary, or None if not found
    """
```

#### Server Management

**Server Startup (macOS/Linux):**

```python
def start_ollama_server(wait_for_ready: bool = True,
                        timeout: float = 30.0) -> bool:
    """Attempt to start Ollama server if not running.

    Uses subprocess to start 'ollama serve' command.
    Waits for server to become responsive if requested.

    Args:
        wait_for_ready: Whether to wait for server to respond
        timeout: Maximum time to wait for server startup

    Returns:
        True if server started successfully, False otherwise
    """
```

**Server Status:**

```python
def get_server_status(base_url: str = "http://localhost:11434",
                      timeout: float = 5.0) -> Dict[str, Any]:
    """Get Ollama server status.

    Returns detailed server information:
    - Server version and build info
    - Running models and resource usage
    - API endpoints and capabilities
    - System resource information

    Args:
        base_url: Ollama server URL
        timeout: Request timeout in seconds

    Returns:
        Server status dictionary
    """
```

## Integration with LLM Core

### Connection Health Monitoring

**LLMClient Integration:**

```python
# Used by LLMClient for connection verification
from infrastructure.llm.utils.ollama import is_ollama_running, select_best_model

class LLMClient:
    def check_connection(self) -> bool:
        """Check Ollama server connectivity."""
        return is_ollama_running(self.config.base_url)

    def _auto_select_model(self) -> Optional[str]:
        """Automatically select best available model."""
        if is_ollama_running(self.config.base_url):
            return select_best_model(self.config.base_url)
        return None
```

### CLI Interface Support

**Command-Line Model Discovery:**

```python
# Used by infrastructure/llm/cli/main.py
from infrastructure.llm.utils.ollama import get_available_models, select_best_model

def models_command(args):
    """Handle 'models' command."""
    try:
        models = get_available_models()
        if not models:
            print("No models available. Install models with: ollama pull <model-name>")
            return

        print("Available models:")
        for model in models:
            size_mb = model.get('size', 0) / (1024 * 1024)
            print(f"• {model['name']} ({size_mb:.1f}MB)")

        # Show recommended model
        best = select_best_model()
        if best:
            print(f"\nRecommended: {best}")

    except Exception as e:
        print(f"Error listing models: {e}")
```

## Testing

### Utility Function Testing

**Server Status Testing:**

```python
def test_ollama_server_check():
    """Test Ollama server connectivity checking."""
    # Test with running server
    assert is_ollama_running("http://localhost:11434")

    # Test with invalid URL
    assert not is_ollama_running("http://invalid:11434")

    # Test with timeout
    assert not is_ollama_running("http://localhost:11434", timeout=0.001)
```

**Model Selection Testing:**

```python
def test_model_selection():
    """Test intelligent model selection."""
    # Test with preferences
    preferences = ["nonexistent-model", "gemma2:2b", "llama2:latest"]
    selected = select_best_model(preferences=preferences)

    # Should select first available model from preferences
    available_models = get_available_models()
    available_names = [m['name'] for m in available_models]

    if "gemma2:2b" in available_names:
        assert selected == "gemma2:2b"
    elif "llama2:latest" in available_names:
        assert selected == "llama2:latest"
    else:
        assert selected is None
```

**Model Preloading Testing:**

```python
def test_model_preloading():
    """Test model preloading functionality."""
    # Test successful preload
    success, error = preload_model("gemma2:2b", timeout=30.0)
    if success:
        assert error is None
        # Verify model is loaded
        models = get_available_models()
        loaded_names = [m['name'] for m in models if m.get('loaded', False)]
        assert "gemma2:2b" in loaded_names
    else:
        # Preload failed (model not available, etc.)
        assert isinstance(error, str)
```

### Integration Testing

**End-to-End Utility Testing:**

```python
def test_complete_ollama_workflow():
    """Test Ollama server interaction workflow."""

    # Check server status
    assert is_ollama_running()

    # Get available models
    models = get_available_models()
    assert isinstance(models, list)
    assert len(models) > 0

    # Select best model
    best_model = select_best_model()
    assert best_model in [m['name'] for m in models]

    # Get detailed server status
    status = get_server_status()
    assert 'version' in status
    assert isinstance(status.get('models', []), list)

    # Test model preloading
    success, error = preload_model(best_model, timeout=60.0)
    # Result depends on model availability and server state
    assert isinstance(success, bool)
    if not success:
        assert isinstance(error, str)
```

## Performance Considerations

### Efficient Operations

**Quick Health Checks:**

- Short timeouts for connectivity tests (2-5 seconds)
- Lightweight API calls for status checks
- Cached results where appropriate
- Non-blocking operations for CLI usage

**Optimized Model Discovery:**

- Single API call to retrieve all models
- Local preference matching without additional requests
- Lazy loading of detailed model information
- Minimal data transfer for model listings

### Resource Management

**Server Interaction Limits:**

- Reasonable timeouts to prevent hanging
- Exponential backoff for retries
- Connection pooling for multiple requests
- Automatic cleanup of failed connections

**Memory Efficiency:**

- Streaming responses for large model lists
- Minimal data structures for model information
- Garbage collection of temporary results
- Efficient string handling for model names

## Error Handling

### Robust Error Recovery

**Network Error Handling:**

```python
def _handle_network_errors(func):
    """Decorator for robust network error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RequestsConnectionError:
            logger.error("Cannot connect to Ollama server")
            return None
        except Timeout:
            logger.warning("Request to Ollama server timed out")
            return None
        except RequestException as e:
            logger.error(f"Ollama server error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Ollama utilities: {e}")
            return None
    return wrapper
```

**Graceful Degradation:**

- Return None/sensible defaults on failures
- Log errors without crashing calling code
- Provide fallback behaviors when possible
- Clear error messages for user debugging

### Logging Integration

**Logging:**

```python
# Debug level for detailed operations
logger.debug(f"Checking Ollama server at {base_url}")

# Info level for important state changes
logger.info(f"Selected model: {best_model}")

# Warning level for recoverable issues
logger.warning(f"Model {model_name} not available, trying next preference")

# Error level for serious issues
logger.error(f"Failed to connect to Ollama server: {error}")
```

## Configuration

### Environment Integration

**Configurable Base URL:**

```bash
# Default Ollama server
export OLLAMA_HOST="http://localhost:11434"

# Custom server location
export OLLAMA_HOST="http://ollama.company.com:8080"
```

**Timeout Configuration:**

```python
# Function parameters allow customization
models = get_available_models(timeout=30.0)  # Longer timeout for slow networks
health = check_ollama_health(timeout=10.0)   # Health checks can be more patient
```

### Model Preferences

**Custom Model Preferences:**

```python
# Override default preferences
custom_preferences = [
    "llama3.1:70b",    # Very large model
    "mixtral:8x7b",    # Mixture of experts
    "gemma3:12b",      # Large single model
    "llama2:70b",      # Alternative large model
]

best_model = select_best_model(preferences=custom_preferences)
```

## Usage Examples

### Basic Server Management

**Health Monitoring:**

```python
from infrastructure.llm.utils.ollama import is_ollama_running, check_ollama_health

# Quick connectivity check
if is_ollama_running():
    print("Ollama server is running")
else:
    print("Ollama server is not accessible")

# Detailed health assessment
health = check_ollama_health()
print(f"Server healthy: {health['healthy']}")
print(f"Available models: {len(health.get('models', []))}")
```

### Model Selection and Management

**Intelligent Model Selection:**

```python
from infrastructure.llm.utils.ollama import select_best_model, get_available_models

# Get all available models
all_models = get_available_models()
print(f"Available models: {len(all_models)}")

# Select best model automatically
best_model = select_best_model()
if best_model:
    print(f"Recommended model: {best_model}")
else:
    print("No suitable models available")
```

**Model Preloading:**

```python
from infrastructure.llm.utils.ollama import preload_model

# Preload model for faster first query
success, error = preload_model("gemma3:4b")

if success:
    print("Model preloaded successfully")
else:
    print(f"Preload failed: {error}")
```

### Server Management

**Server Status Monitoring:**

```python
from infrastructure.llm.utils.ollama import get_server_status

# Get server information
status = get_server_status()
print(f"Ollama version: {status.get('version', 'unknown')}")
print(f"Running models: {len(status.get('running_models', []))}")

# Check system resources
if 'system' in status:
    print(f"CPU usage: {status['system'].get('cpu_percent', 'unknown')}%")
    print(f"Memory usage: {status['system'].get('memory_percent', 'unknown')}%")
```

### Integration with LLM Client

**Seamless Integration:**

```python
from infrastructure.llm.core import LLMClient
from infrastructure.llm.utils.ollama import select_best_model, is_ollama_running

# Create client with automatic model selection
client = LLMClient()

# Auto-select best model if server is running
if is_ollama_running():
    best_model = select_best_model()
    if best_model:
        client.config = client.config.with_overrides(default_model=best_model)
        print(f"Using model: {best_model}")

# Use client normally
response = client.query("Explain quantum computing")
```

## Troubleshooting

### Common Issues

**Server Connection Problems:**

```bash
# Check if Ollama is installed
which ollama

# Check if server is running
curl http://localhost:11434/api/tags

# Start server manually
ollama serve
```

**Model Availability Issues:**

```bash
# List installed models
ollama list

# Pull a model
ollama pull gemma3:4b

# Check model loading
ollama ps
```

**Timeout Issues:**

```python
# Increase timeout for slow connections
models = get_available_models(timeout=30.0)
health = check_ollama_health(timeout=15.0)
```

### Debug Information

**Verbose Logging:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for Ollama utilities
from infrastructure.llm.utils.ollama import get_available_models
models = get_available_models()  # Will show detailed debug logs
```

**Diagnostic Function:**

```python
def diagnose_ollama_setup():
    """Ollama setup diagnosis."""
    from infrastructure.llm.utils.ollama import (
        is_ollama_running, get_available_models,
        check_ollama_health, get_server_status
    )

    print("=== Ollama Setup Diagnosis ===")

    # Check server
    running = is_ollama_running()
    print(f"Server running: {running}")

    if running:
        # Check health
        health = check_ollama_health()
        print(f"Server healthy: {health.get('healthy', False)}")

        # Check models
        models = get_available_models()
        print(f"Available models: {len(models)}")

        # Show status
        status = get_server_status()
        print(f"Server version: {status.get('version', 'unknown')}")

    return running
```

## Future Enhancements

### Planned Improvements

**Server Management:**

- **Automatic Server Restart**: Detect and restart crashed servers
- **Load Balancing**: Distribute requests across multiple Ollama instances
- **Model Auto-Update**: Automatically pull latest model versions
- **Resource Monitoring**: Track and report server resource usage

**Advanced Model Management:**

- **Model Performance Profiling**: Benchmark models for specific tasks
- **Dynamic Model Selection**: Choose models based on task requirements
- **Model Health Monitoring**: Detect and handle model loading failures
- **Custom Model Registry**: Support for private/custom models

**Network Resilience:**

- **Connection Pooling**: Reuse connections for better performance
- **Retry Strategies**: Intelligent retry with exponential backoff
- **Offline Mode**: Graceful degradation when server unavailable
- **Proxy Support**: Work through corporate proxies and VPNs

## See Also

**Related Documentation:**

- [`../core/AGENTS.md`](../core/AGENTS.md) - LLM core functionality
- [`../cli/AGENTS.md`](../cli/AGENTS.md) - CLI interface
- [`../templates/AGENTS.md`](../templates/AGENTS.md) - Template system

**System Documentation:**

- [`../../../AGENTS.md`](../../../AGENTS.md) - LLM module overview
- [`../../../docs/operational/llm-review-troubleshooting.md`](../../../docs/operational/llm-review-troubleshooting.md) - LLM troubleshooting guide
