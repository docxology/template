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
- Command-line interface for interactive queries

CLI Usage:
    python3 -m infrastructure.llm.cli query "What is machine learning?"
    python3 -m infrastructure.llm.cli check
    python3 -m infrastructure.llm.cli models
"""

from infrastructure.llm.core import LLMClient, ResponseMode
from infrastructure.llm.config import LLMConfig, GenerationOptions
from infrastructure.llm.context import ConversationContext, Message
from infrastructure.llm.templates import (
    ResearchTemplate,
    get_template,
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
    ManuscriptMethodologyReview,
    ManuscriptImprovementSuggestions,
    REVIEW_MIN_WORDS,
)
from infrastructure.llm.validation import (
    OutputValidator,
    detect_repetition,
    calculate_unique_content_ratio,
    deduplicate_sections,
    is_off_topic,
    has_on_topic_signals,
    detect_conversational_phrases,
    check_format_compliance,
    OFF_TOPIC_PATTERNS_START,
    OFF_TOPIC_PATTERNS_ANYWHERE,
    CONVERSATIONAL_PATTERNS,
    ON_TOPIC_SIGNALS,
)
from infrastructure.llm.ollama_utils import (
    is_ollama_running,
    start_ollama_server,
    get_available_models,
    get_model_names,
    select_best_model,
    select_small_fast_model,
    ensure_ollama_ready,
    get_model_info,
    check_model_loaded,
    preload_model,
)

__all__ = [
    # Core client
    "LLMClient",
    "ResponseMode",
    # Configuration
    "LLMConfig",
    "GenerationOptions",
    # Context management
    "ConversationContext",
    "Message",
    # Templates
    "ResearchTemplate",
    "get_template",
    # Manuscript review templates
    "ManuscriptExecutiveSummary",
    "ManuscriptQualityReview",
    "ManuscriptMethodologyReview",
    "ManuscriptImprovementSuggestions",
    "REVIEW_MIN_WORDS",
    # Validation
    "OutputValidator",
    "detect_repetition",
    "calculate_unique_content_ratio",
    "deduplicate_sections",
    "is_off_topic",
    "has_on_topic_signals",
    "detect_conversational_phrases",
    "check_format_compliance",
    # Validation patterns (for testing/extension)
    "OFF_TOPIC_PATTERNS_START",
    "OFF_TOPIC_PATTERNS_ANYWHERE",
    "CONVERSATIONAL_PATTERNS",
    "ON_TOPIC_SIGNALS",
    # Ollama utilities
    "is_ollama_running",
    "start_ollama_server",
    "get_available_models",
    "get_model_names",
    "select_best_model",
    "select_small_fast_model",
    "ensure_ollama_ready",
    "get_model_info",
    "check_model_loaded",
    "preload_model",
]

