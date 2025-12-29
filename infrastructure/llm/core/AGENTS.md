# LLM Core Module

## Overview

The `infrastructure/llm/core/` directory contains the fundamental components of the Large Language Model (LLM) infrastructure. This module provides the core client interface, configuration management, and conversation context handling that forms the foundation for all LLM operations in the research template.

## Directory Structure

```
infrastructure/llm/core/
├── AGENTS.md               # This technical documentation
├── __init__.py            # Package exports
├── client.py              # Main LLMClient class and query methods
├── config.py              # Configuration management and options
└── context.py             # Conversation context and message handling
```

## Key Components

### LLMClient (`client.py`)

**Main interface for interacting with Large Language Models:**

#### Core Functionality

**Client Initialization:**
```python
class LLMClient:
    """Main interface for LLM queries and interactions."""

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize with configuration."""
        self.config = config or LLMConfig.from_env()
        self.context = ConversationContext()
        self._check_connection()
```

**Query Methods:**
```python
def query(self, prompt: str, options: Optional[GenerationOptions] = None) -> str:
    """Standard conversational query with context management."""

def query_short(self, prompt: str, options: Optional[GenerationOptions] = None) -> str:
    """Short response query (< 150 tokens)."""

def query_long(self, prompt: str, options: Optional[GenerationOptions] = None) -> str:
    """Long response query (> 500 tokens)."""

def query_structured(self, prompt: str, schema: dict,
                    options: Optional[GenerationOptions] = None) -> dict:
    """JSON-structured response with schema validation."""
```

**Streaming Support:**
```python
def stream_query(self, prompt: str, options: Optional[GenerationOptions] = None) -> Iterator[str]:
    """Stream response in real-time."""

def stream_short(self, prompt: str, options: Optional[GenerationOptions] = None) -> Iterator[str]:
    """Stream short responses."""

def stream_long(self, prompt: str, options: Optional[GenerationOptions] = None) -> Iterator[str]:
    """Stream long responses."""
```

**Context Management:**
```python
def set_system_prompt(self, prompt: str):
    """Set new system prompt and reset context."""

def reset(self):
    """Reset conversation context."""

def _inject_system_prompt(self, messages: List[dict]) -> List[dict]:
    """Inject system prompt into message list."""
```

#### Response Processing

**Thinking Tag Handling:**
```python
def strip_thinking_tags(response: str) -> str:
    """Remove thinking/reasoning tags from LLM responses.

    Handles various thinking tag formats:
    - <thinking>...</thinking>
    - <reasoning>...</reasoning>
    - <thought>...</thought>
    """
```

### LLMConfig (`config.py`)

**Configuration management for LLM operations:**

#### Configuration Classes

**LLMConfig - Main Configuration:**
```python
@dataclass
class LLMConfig:
    """Configuration for LLM client."""

    # Connection settings
    base_url: str = "http://localhost:11434"
    default_model: str = "gemma3:4b"

    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 2048
    context_window: int = 131072  # 128K context

    # System prompt settings
    system_prompt: str = "You are an expert research assistant."
    auto_inject_system_prompt: bool = True

    # Token limits by mode
    short_max_tokens: int = 200
    long_max_tokens: int = 16384

    # Response processing
    timeout: float = 60.0
    seed: Optional[int] = None

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Create configuration from environment variables."""
```

**GenerationOptions - Per-Query Settings:**
```python
@dataclass
class GenerationOptions:
    """Options for individual LLM queries."""

    temperature: float = None
    max_tokens: int = None
    top_p: float = 0.9
    top_k: int = 40
    seed: int = None
    stop: List[str] = None
    format_json: bool = False
    repeat_penalty: float = 1.1
    num_ctx: int = None

    def to_ollama_options(self, config: LLMConfig) -> dict:
        """Convert to Ollama API format."""
```

#### Environment Integration

**Environment Variable Support:**
```python
# Supported environment variables
OLLAMA_HOST=http://localhost:11434    # Ollama server URL
OLLAMA_MODEL=gemma3:4b                # Default model
LLM_TEMPERATURE=0.7                   # Generation temperature
LLM_MAX_TOKENS=2048                   # Maximum tokens
LLM_CONTEXT_WINDOW=131072             # Context window size
LLM_SYSTEM_PROMPT="..."               # Custom system prompt
LLM_TIMEOUT=60.0                      # Request timeout
LLM_SEED=42                           # Random seed
```

### ConversationContext (`context.py`)

**Multi-turn conversation management:**

#### Message Handling

**Message Classes:**
```python
@dataclass
class Message:
    """Individual conversation message."""
    role: str      # "user", "assistant", "system"
    content: str   # Message content

class ConversationContext:
    """Manages conversation history and context."""

    def __init__(self, max_tokens: int = 131072):
        self.messages: List[Message] = []
        self.max_tokens = max_tokens
        self.token_counter = self._get_token_counter()

    def add_message(self, role: str, content: str):
        """Add message to conversation."""

    def get_messages(self) -> List[dict]:
        """Get messages in API format."""

    def clear(self):
        """Clear all messages."""

    def _prune_old_messages(self):
        """Prune old messages to stay within token limit."""
```

#### Token Management

**Context Window Management:**
```python
def _should_prune(self) -> bool:
    """Check if context pruning is needed."""
    total_tokens = sum(self.token_counter(msg['content'])
                      for msg in self.messages)
    return total_tokens > self.max_tokens * 0.9  # 90% threshold

def _prune_context(self):
    """Prune context to fit within token limits."""
    # Keep system message if present
    system_msg = None
    if self.messages and self.messages[0].role == "system":
        system_msg = self.messages[0]

    # Remove oldest messages until under limit
    while self._should_prune() and len(self.messages) > 1:
        # Remove oldest non-system message
        for i, msg in enumerate(self.messages):
            if msg.role != "system":
                self.messages.pop(i)
                break

    # Re-inject system message
    if system_msg and (not self.messages or self.messages[0].role != "system"):
        self.messages.insert(0, system_msg)
```

## Integration with LLM Infrastructure

### Connection to Higher-Level Modules

**Used by Template System (`infrastructure/llm/templates/`):**
```python
# Templates use LLMClient for research-specific queries
template = ResearchTemplate()
response = template.apply(client, **variables)
```

**Used by CLI Interface (`infrastructure/llm/cli/`):**
```python
# CLI wraps LLMClient for command-line usage
client = LLMClient()
response = client.query_short(args.prompt, options=cli_options)
```

**Used by Review System (`infrastructure/llm/review/`):**
```python
# Review system uses structured queries
review = client.query_structured(review_prompt, schema=review_schema)
```

### Response Mode Implementation

**Mode-Specific Token Limits:**
```python
def _get_max_tokens_for_mode(self, mode: ResponseMode, options: GenerationOptions) -> int:
    """Get appropriate max tokens for response mode."""
    if options and options.max_tokens:
        return options.max_tokens

    mode_limits = {
        ResponseMode.SHORT: self.config.short_max_tokens,
        ResponseMode.LONG: self.config.long_max_tokens,
        ResponseMode.STRUCTURED: self.config.long_max_tokens,
    }

    return mode_limits.get(mode, self.config.max_tokens)
```

## Testing

### Test Coverage

**Core Functionality Tests:**
```python
def test_llm_client_initialization():
    """Test LLMClient initialization with config."""
    config = LLMConfig(base_url="http://test:11434", default_model="test-model")
    client = LLMClient(config)

    assert client.config.base_url == "http://test:11434"
    assert client.config.default_model == "test-model"

def test_conversation_context_management():
    """Test conversation context handling."""
    context = ConversationContext()

    context.add_message("user", "Hello")
    context.add_message("assistant", "Hi there")

    messages = context.get_messages()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"

def test_generation_options_conversion():
    """Test conversion of options to Ollama format."""
    options = GenerationOptions(
        temperature=0.8,
        max_tokens=1000,
        top_p=0.9,
        format_json=True
    )

    ollama_opts = options.to_ollama_options(LLMConfig())
    assert ollama_opts["temperature"] == 0.8
    assert ollama_opts["num_predict"] == 1000
    assert ollama_opts["top_p"] == 0.9
    assert ollama_opts["format"] == "json"
```

### Integration Testing

**End-to-End Query Testing:**
```python
def test_llm_client_query_integration():
    """Test complete LLM query workflow."""
    # This would require a mock Ollama server
    # Tests connection, request formatting, response processing

def test_context_pruning():
    """Test automatic context pruning."""
    context = ConversationContext(max_tokens=1000)

    # Add many messages
    for i in range(100):
        context.add_message("user", f"Message {i} with some content " * 10)

    # Should automatically prune when getting messages
    messages = context.get_messages()

    # Verify total tokens are within limit
    total_tokens = sum(len(msg["content"].split()) for msg in messages)
    assert total_tokens <= 1000
```

## Performance Considerations

### Connection Management

**Efficient Resource Usage:**
- Persistent HTTP connections to Ollama
- Connection pooling for multiple requests
- Automatic reconnection on failures
- Timeout management to prevent hanging

### Memory Management

**Context Optimization:**
- Automatic pruning of conversation history
- Token-aware message management
- Memory-efficient message storage
- Configurable context window limits

### Response Processing

**Streaming Efficiency:**
- Real-time token processing
- Memory-efficient streaming
- Early validation of response format
- Progressive response building

## Error Handling

### Connection Errors

**Robust Error Recovery:**
```python
def _handle_connection_error(self, error: Exception) -> None:
    """Handle connection-related errors."""
    if isinstance(error, requests.ConnectionError):
        logger.error(f"Connection failed to {self.config.base_url}")
        raise LLMConnectionError("Cannot connect to Ollama server")
    elif isinstance(error, requests.Timeout):
        logger.error(f"Request timeout after {self.config.timeout}s")
        raise LLMTimeoutError(f"Request timed out after {self.config.timeout}s")
    elif isinstance(error, requests.HTTPError):
        status_code = error.response.status_code
        logger.error(f"HTTP error {status_code}: {error.response.text}")
        raise LLMHTTPError(f"HTTP {status_code} error", status_code=status_code)
```

### Response Validation

**Content Validation:**
```python
def _validate_response(self, response: str, mode: ResponseMode) -> str:
    """Validate and clean LLM response."""

    # Remove thinking tags
    response = strip_thinking_tags(response)

    # Mode-specific validation
    if mode == ResponseMode.STRUCTURED:
        # Validate JSON structure
        response = self._ensure_json_response(response)
    elif mode == ResponseMode.SHORT:
        # Check token limit
        if self._count_tokens(response) > self.config.short_max_tokens:
            logger.warning(f"Short response exceeded token limit: {len(response)}")

    return response.strip()
```

## Configuration Examples

### Basic Configuration

**Minimal Setup:**
```bash
# Environment variables for basic usage
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="gemma3:4b"
export LLM_TEMPERATURE="0.7"
```

### Advanced Configuration

**Full Configuration:**
```python
config = LLMConfig(
    base_url="http://localhost:11434",
    default_model="gemma3:4b",
    temperature=0.7,
    max_tokens=2048,
    context_window=131072,
    system_prompt="You are an expert research assistant specializing in data analysis and scientific methodology.",
    auto_inject_system_prompt=True,
    short_max_tokens=200,
    long_max_tokens=16384,
    timeout=60.0,
    seed=42
)
```

### Research-Specific Configuration

**Academic Writing Configuration:**
```python
academic_config = LLMConfig(
    system_prompt="""You are an expert academic writer specializing in research manuscripts.
    Provide clear, precise, and well-structured responses following academic conventions.
    Use formal language and provide citations when discussing research methods.""",
    temperature=0.3,  # Lower temperature for more consistent academic writing
    max_tokens=4096,  # Allow longer responses for detailed explanations
    seed=12345       # Reproducible outputs for academic work
)
```

## Usage Examples

### Basic Query

**Simple Conversational Query:**
```python
from infrastructure.llm.core import LLMClient

client = LLMClient()
response = client.query("What is the difference between supervised and unsupervised learning?")
print(response)
```

### Structured Research Query

**JSON-Structured Response:**
```python
schema = {
    "type": "object",
    "properties": {
        "method": {"type": "string"},
        "advantages": {"type": "array", "items": {"type": "string"}},
        "disadvantages": {"type": "array", "items": {"type": "string"}},
        "use_cases": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["method", "advantages", "disadvantages"]
}

response = client.query_structured(
    "Analyze the k-means clustering algorithm",
    schema=schema
)
print(f"Method: {response['method']}")
print(f"Advantages: {response['advantages']}")
```

### Context-Aware Research Discussion

**Multi-Turn Conversation:**
```python
# Start research discussion
client.query("Let's analyze statistical methods for hypothesis testing")

# Follow up with context preserved
client.query("What about the assumptions for ANOVA?")

# Continue the research conversation
client.query("How do these assumptions affect the validity of results?")
```

## See Also

**Related Documentation:**
- [`../AGENTS.md`](../AGENTS.md) - LLM module overview
- [`../templates/AGENTS.md`](../templates/AGENTS.md) - Template system
- [`../cli/AGENTS.md`](../cli/AGENTS.md) - CLI interface
- [`../review/AGENTS.md`](../review/AGENTS.md) - Review system

**System Documentation:**
- [`../../../infrastructure/core/AGENTS.md`](../../../infrastructure/core/AGENTS.md) - Core infrastructure
- [`../../../docs/development/TESTING_GUIDE.md`](../../../docs/development/TESTING_GUIDE.md) - Testing guide