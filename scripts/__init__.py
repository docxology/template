"""Scripts package - entry point orchestrators for the build pipeline.

This package contains thin orchestrators that coordinate the template's 
build pipeline stages. All business logic is in infrastructure/ modules.

Exports from 06_llm_review.py for testing:
- ReviewMetrics, ManuscriptMetrics, SessionMetrics: Metrics dataclasses
- estimate_tokens: Token estimation function
- get_max_input_length: Environment configuration
- Review generation and saving functions
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Load 06_llm_review.py dynamically since the name starts with a digit
# Register it in sys.modules first so dataclasses can find it
_script_path = Path(__file__).parent / "06_llm_review.py"
_module_name = "scripts.llm_review"
_spec = importlib.util.spec_from_file_location(_module_name, _script_path)
_llm_review = importlib.util.module_from_spec(_spec)
sys.modules[_module_name] = _llm_review
_spec.loader.exec_module(_llm_review)

# Export from the loaded module
DEFAULT_MAX_INPUT_LENGTH = _llm_review.DEFAULT_MAX_INPUT_LENGTH
ReviewMetrics = _llm_review.ReviewMetrics
ManuscriptMetrics = _llm_review.ManuscriptMetrics
SessionMetrics = _llm_review.SessionMetrics
estimate_tokens = _llm_review.estimate_tokens
get_max_input_length = _llm_review.get_max_input_length
log_stage = _llm_review.log_stage
check_ollama_availability = _llm_review.check_ollama_availability
extract_manuscript_text = _llm_review.extract_manuscript_text
generate_review_with_metrics = _llm_review.generate_review_with_metrics
generate_executive_summary = _llm_review.generate_executive_summary
generate_quality_review = _llm_review.generate_quality_review
generate_methodology_review = _llm_review.generate_methodology_review
generate_improvement_suggestions = _llm_review.generate_improvement_suggestions
save_review_outputs = _llm_review.save_review_outputs
generate_review_summary = _llm_review.generate_review_summary
validate_review_quality = _llm_review.validate_review_quality
is_off_topic = _llm_review.is_off_topic
detect_emojis = _llm_review.detect_emojis
detect_tables = _llm_review.detect_tables
detect_conversational_phrases = _llm_review.detect_conversational_phrases
detect_hallucinated_sections = _llm_review.detect_hallucinated_sections
check_format_compliance = _llm_review.check_format_compliance
main = _llm_review.main

# Re-export infrastructure utilities for tests
try:
    from infrastructure.llm import (
        LLMClient,
        LLMConfig,
        is_ollama_running,
        select_best_model,
    )
except ImportError:
    # Infrastructure may not be available in all contexts
    pass

__all__ = [
    "DEFAULT_MAX_INPUT_LENGTH",
    "ReviewMetrics",
    "ManuscriptMetrics", 
    "SessionMetrics",
    "estimate_tokens",
    "get_max_input_length",
    "log_stage",
    "check_ollama_availability",
    "extract_manuscript_text",
    "generate_review_with_metrics",
    "generate_executive_summary",
    "generate_quality_review",
    "generate_methodology_review",
    "generate_improvement_suggestions",
    "save_review_outputs",
    "generate_review_summary",
    "validate_review_quality",
    "is_off_topic",
    "detect_emojis",
    "detect_tables",
    "detect_conversational_phrases",
    "detect_hallucinated_sections",
    "check_format_compliance",
    "main",
]
