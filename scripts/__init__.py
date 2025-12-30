"""Scripts package - entry point orchestrators for the build pipeline.

This package contains thin orchestrators that coordinate the template's 
build pipeline stages. All business logic is in infrastructure/ modules.

This package intentionally re-exports a small set of functions for integration
tests (notably the LLM review helpers), while keeping orchestration logic in
thin entry points under `scripts/` and business logic in `infrastructure/`.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Menu option to script mapping (for run.sh interactive menu).
# This documents the relationship between menu choices and underlying entry points.
MENU_SCRIPT_MAPPING = {
    0: {
        "script": "00_setup_environment.py",
        "function": "run_setup_environment",
        "requires_ollama": False,
        "description": "Setup Environment"
    },
    1: {
        "script": "01_run_tests.py",
        "function": "run_all_tests",
        "requires_ollama": False,
        "description": "Run Tests (infrastructure + project)"
    },
    2: {
        "script": "02_run_analysis.py",
        "function": "run_analysis_standalone",
        "requires_ollama": False,
        "description": "Run Analysis"
    },
    3: {
        "script": "03_render_pdf.py",
        "function": "run_pdf_rendering",
        "requires_ollama": False,
        "note": "Requires analysis outputs to be available",
        "description": "Render PDF"
    },
    4: {
        "script": "04_validate_output.py",
        "function": "run_validation_standalone",
        "requires_ollama": False,
        "description": "Validate Output"
    },
    5: {
        "script": "06_llm_review.py",
        "function": "run_llm_review",
        "requires_ollama": True,
        "description": "LLM Review (reviews-only from run.sh)"
    },
    6: {
        "script": "06_llm_review.py",
        "function": "run_llm_translations",
        "requires_ollama": True,
        "description": "LLM Translations (translations-only from run.sh)"
    },
    7: {
        "script": "05_copy_outputs.py",
        "function": "run_copy_outputs_standalone",
        "requires_ollama": False,
        "description": "Copy Outputs"
    },
    8: {
        "script": "execute_pipeline.py",
        "function": "run_full_pipeline",
        "requires_ollama": False,
        "description": "Run Full Pipeline (via execute_pipeline.py)"
    },
}

# Import from infrastructure modules (where functions were moved during refactoring)
from infrastructure.llm.review.generator import (
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
from infrastructure.llm.review.metrics import (
    ReviewMetrics,
    ManuscriptMetrics,
    estimate_tokens,
)
from infrastructure.llm.review.io import (
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

# Re-export validation functions
from infrastructure.llm.validation.format import (
    is_off_topic,
    detect_conversational_phrases,
    check_format_compliance,
)

# Re-export infrastructure utilities for tests
try:
    from infrastructure.llm.core.client import LLMClient
    from infrastructure.llm.core.config import LLMConfig
    from infrastructure.llm.utils.ollama import (
        is_ollama_running,
        select_best_model,
    )
except ImportError:
    # Infrastructure may not be available in all contexts
    pass

# Re-export pipeline orchestrators (preferred entry points)
try:
    from scripts.execute_pipeline import execute_pipeline, execute_single_stage
    from scripts.execute_multi_project import execute_multi_project
except Exception:
    # Avoid hard import failures if scripts are executed in constrained contexts.
    pass

__all__ = [
    "MENU_SCRIPT_MAPPING",
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
    "execute_pipeline",
    "execute_single_stage",
    "execute_multi_project",
]
