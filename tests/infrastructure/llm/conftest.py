"""Test fixtures for LLM module tests.

Following No Mocks Policy:
- Tests for pure logic (config, validation, context, templates) use real data
- Integration tests requiring Ollama are marked with @pytest.mark.requires_ollama
- Ollama utilities handle model discovery and selection
"""
import pytest
import os

from infrastructure.llm.config import LLMConfig, GenerationOptions
from infrastructure.llm.core import LLMClient
from infrastructure.llm.context import ConversationContext
from infrastructure.llm.ollama_utils import (
    is_ollama_running,
    select_small_fast_model,
    select_best_model,
    get_model_names,
    ensure_ollama_ready,
)


# Cache for discovered model to avoid repeated API calls
_discovered_model = None
_ollama_available = None


def get_test_model() -> str:
    """Get the best available model for testing.
    
    Caches result to avoid repeated API calls during test session.
    Falls back to 'llama3' if Ollama is not available.
    """
    global _discovered_model
    if _discovered_model is None:
        if is_ollama_running():
            _discovered_model = select_best_model() or "llama3"
        else:
            _discovered_model = "llama3"
    return _discovered_model


def check_ollama_available() -> bool:
    """Check if Ollama is available (cached).
    
    Returns:
        True if Ollama is running and has models, False otherwise.
    """
    global _ollama_available
    if _ollama_available is None:
        _ollama_available = is_ollama_running() and len(get_model_names()) > 0
    return _ollama_available


@pytest.fixture
def default_config():
    """Create a default LLMConfig for testing with discovered model."""
    model = get_test_model()
    available_models = get_model_names() if is_ollama_running() else []
    fallbacks = [m for m in available_models if m != model][:2] or ["mistral", "phi3"]
    
    return LLMConfig(
        base_url="http://localhost:11434",
        default_model=model,
        fallback_models=fallbacks,
        auto_inject_system_prompt=False,
        system_prompt="Test system prompt",
        short_max_tokens=200,
        long_max_tokens=4096,
        temperature=0.7,
        max_tokens=2048,
    )


@pytest.fixture
def config_with_system_prompt():
    """Create a LLMConfig with system prompt injection enabled."""
    model = get_test_model()
    available_models = get_model_names() if is_ollama_running() else []
    fallbacks = [m for m in available_models if m != model][:1] or ["mistral"]
    
    return LLMConfig(
        base_url="http://localhost:11434",
        default_model=model,
        fallback_models=fallbacks,
        auto_inject_system_prompt=True,
        system_prompt="You are a helpful research assistant.",
    )


@pytest.fixture
def generation_options():
    """Create sample GenerationOptions for testing."""
    return GenerationOptions(
        temperature=0.5,
        max_tokens=500,
        seed=42,
        stop=["END"],
    )


@pytest.fixture
def conversation_context():
    """Create a ConversationContext for testing."""
    return ConversationContext(max_tokens=1000)


@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
    ]


@pytest.fixture
def sample_json_responses():
    """Sample JSON response strings for validation testing."""
    return {
        "valid": '{"summary": "Test summary", "items": [1, 2, 3]}',
        "markdown_wrapped": '```json\n{"key": "value"}\n```',
        "invalid": '{"key": "value"',  # Missing closing brace
        "nested": '{"data": {"nested": true}, "list": [1, 2, 3]}',
    }


@pytest.fixture
def sample_schema():
    """Sample JSON schema for structured response validation."""
    return {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "items": {"type": "array"},
            "count": {"type": "integer"},
        },
        "required": ["summary"],
    }


# Environment variable fixtures
@pytest.fixture
def clean_llm_env():
    """Temporarily remove all LLM-related environment variables."""
    env_vars = [
        "OLLAMA_HOST", "OLLAMA_MODEL", "LLM_TEMPERATURE",
        "LLM_MAX_TOKENS", "LLM_CONTEXT_WINDOW", "LLM_TIMEOUT",
        "LLM_NUM_CTX", "LLM_SEED", "LLM_SYSTEM_PROMPT"
    ]
    old_values = {}
    for var in env_vars:
        old_values[var] = os.environ.pop(var, None)
    
    yield
    
    # Restore environment
    for var, value in old_values.items():
        if value is not None:
            os.environ[var] = value


# Marker for tests requiring Ollama
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "requires_ollama: mark test as requiring running Ollama server"
    )
