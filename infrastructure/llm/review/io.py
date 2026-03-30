"""File I/O and output formatting for LLM review generation.

This is the **preferred import path** for review I/O helpers. It consolidates
the public API of the ``review_analysis``, ``saving``, and ``metrics``
sub-modules so callers do not need to know the internal split.

All existing imports (``from infrastructure.llm.review.io import ...``)
continue to work unchanged.
"""

from __future__ import annotations

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
