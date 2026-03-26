"""Repetition detection functions for LLM output validation.

This module re-exports from focused submodules:
- similarity: text similarity algorithms (Jaccard, TF-cosine, n-gram, hybrid)
- detection: repetition detection, unique-content ratio, section deduplication
"""

from __future__ import annotations

from infrastructure.llm.validation.detection import (
    RepetitionResult,
    calculate_unique_content_ratio,
    deduplicate_sections,
    detect_repetition,
)
from infrastructure.llm.validation.similarity import (
    _calculate_similarity,
    _jaccard_similarity,
    _normalize_for_comparison,
    _sequence_similarity,
    _tf_cosine_similarity,
)

__all__ = [
    # Public API
    "RepetitionResult",
    "calculate_unique_content_ratio",
    "deduplicate_sections",
    "detect_repetition",
    # Internal helpers (re-exported for backwards compatibility)
    "_calculate_similarity",
    "_jaccard_similarity",
    "_normalize_for_comparison",
    "_sequence_similarity",
    "_tf_cosine_similarity",
]
