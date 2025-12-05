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

# Import from infrastructure modules (where functions were moved during refactoring)
from infrastructure.llm.review_generator import (
    DEFAULT_MAX_INPUT_LENGTH,
    get_max_input_length,
    check_ollama_availability,
    extract_manuscript_text,
    generate_executive_summary,
    generate_quality_review,
    generate_methodology_review,
    generate_improvement_suggestions,
    validate_review_quality,
)
from infrastructure.core.logging_utils import log_stage
from infrastructure.llm.review_metrics import (
    ReviewMetrics,
    ManuscriptMetrics,
    estimate_tokens,
)
from infrastructure.llm.review_io import (
    SessionMetrics,
    save_review_outputs,
    generate_review_summary,
)

# Load 06_llm_review.py dynamically for main() function and ReviewMode enum
# Register it in sys.modules first so dataclasses can find it
_script_path = Path(__file__).parent / "06_llm_review.py"
_module_name = "scripts.llm_review"
_spec = importlib.util.spec_from_file_location(_module_name, _script_path)
_llm_review = importlib.util.module_from_spec(_spec)
sys.modules[_module_name] = _llm_review
_spec.loader.exec_module(_llm_review)

# Export main function and ReviewMode from the script
main = _llm_review.main
ReviewMode = _llm_review.ReviewMode

# Re-export validation functions for backward compatibility
from infrastructure.llm.validation_format import (
    is_off_topic,
    detect_conversational_phrases,
    check_format_compliance,
)

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
    "check_ollama_availability",
    "extract_manuscript_text",
    "generate_executive_summary",
    "generate_quality_review",
    "generate_methodology_review",
    "generate_improvement_suggestions",
    "validate_review_quality",
    "save_review_outputs",
    "generate_review_summary",
    "log_stage",
    "is_off_topic",
    "detect_conversational_phrases",
    "check_format_compliance",
    "main",
    "ReviewMode",
]
