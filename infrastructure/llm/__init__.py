"""LLM Module.

This module provides tools for interacting with Local Large Language Models (Ollama)
for research assistance tasks.

Features:
- Multiple response modes: short, long, structured, raw
- Per-query generation options (temperature, seed, stop sequences)
- Conversation context management with system prompt injection
- Research prompt templates
- Comprehensive output validation
- Streaming and non-streaming queries
- Environment variable configuration (OLLAMA_HOST, OLLAMA_MODEL, LLM_*)
"""

from infrastructure.llm.core import LLMClient, ResponseMode
from infrastructure.llm.config import LLMConfig, GenerationOptions
from infrastructure.llm.context import ConversationContext, Message
from infrastructure.llm.templates import ResearchTemplate, get_template
from infrastructure.llm.validation import OutputValidator

__all__ = [
    "LLMClient",
    "ResponseMode",
    "LLMConfig",
    "GenerationOptions",
    "ConversationContext",
    "Message",
    "ResearchTemplate",
    "get_template",
    "OutputValidator",
]

