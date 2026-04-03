"""LLM module.

Provides the package surface for local Ollama-backed research workflows.

Module structure:
- core/ - client, config, and context helpers
- templates/ - prompt templates for repeatable tasks
- validation/ - output validation helpers
- review/ - manuscript review generation
- utils/ - Ollama server and model utilities
- cli/ - command-line interface
- prompts/ - prompt fragments

CLI usage:
    uv run python -m infrastructure.llm.cli query "What is machine learning?"
    uv run python -m infrastructure.llm.cli check
    uv run python -m infrastructure.llm.cli models

Usage::

    from infrastructure.llm import LLMClient, OllamaClientConfig, GenerationOptions
    from infrastructure.llm import get_template, validate_complete, is_off_topic
    from infrastructure.llm import generate_review_with_metrics
"""

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig
from infrastructure.llm.review.generator import generate_review_with_metrics
from infrastructure.llm.templates import get_template
from infrastructure.llm.validation import is_off_topic, validate_complete

__all__ = [
    "GenerationOptions",
    "LLMClient",
    "OllamaClientConfig",
    "generate_review_with_metrics",
    "get_template",
    "is_off_topic",
    "validate_complete",
]
