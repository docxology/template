"""Test fixtures for LLM module tests.

Following No Mocks Policy:
- Tests for pure logic (config, validation, context, templates) use real data
- Integration tests requiring Ollama are marked with @pytest.mark.requires_ollama
- No MagicMock or mocker.patch for business logic testing
"""
import pytest
import os

from infrastructure.llm.config import LLMConfig, GenerationOptions
from infrastructure.llm.core import LLMClient
from infrastructure.llm.context import ConversationContext


@pytest.fixture
def default_config():
    """Create a default LLMConfig for testing."""
    return LLMConfig(
        base_url="http://localhost:11434",
        default_model="llama3",
        fallback_models=["mistral", "phi3"],
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
    return LLMConfig(
        base_url="http://localhost:11434",
        default_model="llama3",
        fallback_models=["mistral"],
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
