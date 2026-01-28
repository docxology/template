"""LLM Module.

This module provides tools for interacting with Local Large Language Models (Ollama)
for research assistance tasks.

Module Structure:
- core/ - Core LLM functionality (client, config, context)
- templates/ - Prompt templates for research tasks
- validation/ - Output validation and quality checks
- review/ - Manuscript review generation system
- utils/ - Utility functions (Ollama management)
- cli/ - Command-line interface
- prompts/ - Prompt fragment system

CLI Usage:
    python3 -m infrastructure.llm.cli.main query "What is machine learning?"
    python3 -m infrastructure.llm.cli.main check
    python3 -m infrastructure.llm.cli.main models

Direct imports (recommended):
    from infrastructure.llm.core.client import LLMClient
    from infrastructure.llm.core.config import LLMConfig, GenerationOptions
    from infrastructure.llm.templates import get_template
    from infrastructure.llm.validation import OutputValidator
"""

# Convenience re-exports from submodules (use direct imports for better clarity)
from infrastructure.llm.core import (ConversationContext, GenerationOptions,
                                     LLMClient, LLMConfig, Message,
                                     ResponseMode, strip_thinking_tags)
from infrastructure.llm.templates import (REVIEW_MIN_WORDS,
                                          TRANSLATION_LANGUAGES,
                                          ManuscriptExecutiveSummary,
                                          ManuscriptImprovementSuggestions,
                                          ManuscriptMethodologyReview,
                                          ManuscriptQualityReview,
                                          ManuscriptTranslationAbstract,
                                          PaperSummarization, ResearchTemplate,
                                          get_template)
from infrastructure.llm.utils import (check_model_loaded, ensure_ollama_ready,
                                      get_available_models, get_model_info,
                                      get_model_names, is_ollama_running,
                                      preload_model, select_best_model,
                                      select_small_fast_model,
                                      start_ollama_server)
from infrastructure.llm.validation import (CONVERSATIONAL_PATTERNS,
                                           OFF_TOPIC_PATTERNS_ANYWHERE,
                                           OFF_TOPIC_PATTERNS_START,
                                           ON_TOPIC_SIGNALS, OutputValidator,
                                           calculate_unique_content_ratio,
                                           check_format_compliance,
                                           deduplicate_sections,
                                           detect_conversational_phrases,
                                           detect_repetition,
                                           extract_structured_sections,
                                           has_on_topic_signals, is_off_topic,
                                           validate_response_structure,
                                           validate_section_completeness)

# Optional prompt system imports
try:
    from infrastructure.llm.prompts import PromptComposer, PromptFragmentLoader
except ImportError:
    # Prompt system not available - set to None for optional usage
    PromptFragmentLoader = None  # type: ignore
    PromptComposer = None  # type: ignore

# Review generation modules
from infrastructure.llm.review import (ManuscriptMetrics, ReviewMetrics,
                                       SessionMetrics, StreamingMetrics,
                                       calculate_format_compliance_summary,
                                       calculate_quality_summary,
                                       check_ollama_availability,
                                       create_review_client, estimate_tokens,
                                       extract_action_items,
                                       extract_manuscript_text,
                                       generate_executive_summary,
                                       generate_improvement_suggestions,
                                       generate_methodology_review,
                                       generate_quality_review,
                                       generate_review_summary,
                                       generate_review_with_metrics,
                                       generate_translation,
                                       get_manuscript_review_system_prompt,
                                       get_max_input_length,
                                       get_review_max_tokens,
                                       get_review_timeout, save_review_outputs,
                                       save_single_review,
                                       validate_review_quality, warmup_model)

__all__ = [
    # Core client
    "LLMClient",
    "ResponseMode",
    "strip_thinking_tags",
    # Configuration
    "LLMConfig",
    "GenerationOptions",
    # Context management
    "ConversationContext",
    "Message",
    # Templates
    "ResearchTemplate",
    "get_template",
    "PaperSummarization",
    # Manuscript review templates
    "ManuscriptExecutiveSummary",
    "ManuscriptQualityReview",
    "ManuscriptMethodologyReview",
    "ManuscriptImprovementSuggestions",
    "ManuscriptTranslationAbstract",
    "REVIEW_MIN_WORDS",
    "TRANSLATION_LANGUAGES",
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
    # Enhanced validation functions
    "validate_section_completeness",
    "extract_structured_sections",
    "validate_response_structure",
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
    # Prompt system (optional)
    "PromptFragmentLoader",
    "PromptComposer",
    # Review metrics
    "ReviewMetrics",
    "ManuscriptMetrics",
    "SessionMetrics",
    "StreamingMetrics",
    "estimate_tokens",
    # Review generation
    "get_manuscript_review_system_prompt",
    "get_max_input_length",
    "get_review_timeout",
    "get_review_max_tokens",
    "validate_review_quality",
    "create_review_client",
    "check_ollama_availability",
    "warmup_model",
    "extract_manuscript_text",
    "generate_review_with_metrics",
    "generate_executive_summary",
    "generate_quality_review",
    "generate_methodology_review",
    "generate_improvement_suggestions",
    "generate_translation",
    # Review I/O
    "extract_action_items",
    "calculate_format_compliance_summary",
    "calculate_quality_summary",
    "save_review_outputs",
    "save_single_review",
    "generate_review_summary",
]
