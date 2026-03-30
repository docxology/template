"""Repetition detection functions for LLM output validation.

Re-exports the public API from ``detection`` (repetition detection algorithms).
The ``similarity`` submodule provides lower-level text similarity helpers used
internally by ``detection``; its functions are private and not re-exported here.
"""

from __future__ import annotations

from infrastructure.llm.validation.detection import (
    RepetitionResult,
    calculate_unique_content_ratio,
    deduplicate_sections,
    detect_repetition,
)
__all__ = [
    "RepetitionResult",
    "calculate_unique_content_ratio",
    "deduplicate_sections",
    "detect_repetition",
]
