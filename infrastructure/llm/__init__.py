"""LLM Module.

This module provides tools for interacting with Local Large Language Models (Ollama)
for research assistance tasks.

Features:
- Multiple response modes: short, long, structured
- Conversation context management
- Research prompt templates
- Comprehensive output validation
- Streaming and non-streaming queries
"""

from infrastructure.llm.core import LLMClient, ResponseMode
from infrastructure.llm.config import LLMConfig
from infrastructure.llm.context import ConversationContext, Message
from infrastructure.llm.templates import ResearchTemplate, get_template
from infrastructure.llm.validation import OutputValidator

__all__ = [
    "LLMClient",
    "ResponseMode",
    "LLMConfig",
    "ConversationContext",
    "Message",
    "ResearchTemplate",
    "get_template",
    "OutputValidator",
]

