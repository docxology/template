"""File I/O and output formatting for LLM review generation.

Note:
    This module re-exports from ``formatting`` and ``saving`` sub-modules.
    All existing imports continue to work unchanged.
"""

from __future__ import annotations

from infrastructure.llm.review.formatting import (
    _build_combined_review_content,
    _build_review_header,
    _build_review_metadata,
)
from infrastructure.llm.review.review_analysis import (
    calculate_format_compliance_summary,
    calculate_quality_summary,
    extract_action_items,
)
from infrastructure.llm.review.saving import (
    generate_review_summary,
    save_review_outputs,
    save_single_review,
)

# Re-export SessionMetrics for backwards compatibility with:
#   from infrastructure.llm.review.io import SessionMetrics
from infrastructure.llm.review.metrics import SessionMetrics  # noqa: F401

__all__ = [
    # review_analysis (re-exported for backwards compat)
    "calculate_format_compliance_summary",
    "calculate_quality_summary",
    "extract_action_items",
    # saving
    "generate_review_summary",
    "save_review_outputs",
    "save_single_review",
    # metrics (re-exported for backwards compat)
    "SessionMetrics",
]
