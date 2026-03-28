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
__all__ = [
    "RepetitionResult",
    "calculate_unique_content_ratio",
    "deduplicate_sections",
    "detect_repetition",
]
