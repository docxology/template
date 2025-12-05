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

# Menu option to script mapping (for run.sh interactive menu)
# This documents the relationship between menu options and Python scripts
# Menu numbering now aligns with script numbering (0-7 for scripts, 8 for pipeline, 9+ for sub-ops)
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
        "note": "Also runs 02_run_analysis.py",
        "description": "Render PDF"
    },
    4: {
        "script": "04_validate_output.py",
        "function": "run_validation_standalone",
        "requires_ollama": False,
        "description": "Validate Output"
    },
    5: {
        "script": "05_copy_outputs.py",
        "function": "run_copy_outputs_standalone",
        "requires_ollama": False,
        "description": "Copy Outputs"
    },
    6: {
        "script": "06_llm_review.py",
        "function": "run_llm_review",
        "requires_ollama": True,
        "description": "LLM Review (reviews and translations)"
    },
    7: {
        "script": "07_literature_search.py",
        "function": "run_literature_search_all",
        "requires_ollama": False,
        "note": "Runs search and summarize (summarize requires Ollama)",
        "description": "Literature Search (all operations)"
    },
    8: {
        "script": "run_all.py",
        "function": "run_full_pipeline",
        "requires_ollama": False,
        "description": "Run Full Pipeline (10 stages: 0-9, via run.sh)"
    },
    9: {
        "script": "07_literature_search.py",
        "args": ["--search-only"],
        "requires_ollama": False,
        "description": "Search only (network only)"
    },
    10: {
        "script": "07_literature_search.py",
        "args": ["--download-only"],
        "requires_ollama": False,
        "description": "Download only (network only)"
    },
    11: {
        "script": "07_literature_search.py",
        "args": ["--summarize"],
        "requires_ollama": True,
        "description": "Summarize (requires Ollama)"
    },
    12: {
        "script": "07_literature_search.py",
        "args": ["--cleanup"],
        "requires_ollama": False,
        "description": "Cleanup (local files only)"
    },
    13: {
        "script": "07_literature_search.py",
        "args": ["--llm-operation"],
        "requires_ollama": True,
        "description": "Advanced LLM operations (requires Ollama)"
    },
}

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
]
