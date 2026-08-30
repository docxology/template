"""Compatibility facade for accessible semantic slide rendering.

The implementation is partitioned by responsibility so geometry, table
composition, frame orchestration, and Reveal.js post-processing remain small,
reviewable units. Existing callers intentionally keep this module as their
single import surface.
"""

from __future__ import annotations

from infrastructure.rendering._slides_accessibility_ast import (
    _estimated_visible_characters as _estimated_visible_characters,
)
from infrastructure.rendering._slides_accessibility_composition import (
    compose_accessible_pandoc_document,
    load_and_compose_pandoc_json,
)
from infrastructure.rendering._slides_accessibility_contracts import (
    AccessibleSlideComposition,
    AccessibleSlidePolicy,
)
from infrastructure.rendering._slides_accessibility_reveal import (
    accessible_reveal_output_issues,
    enhance_accessible_reveal,
)


__all__ = [
    "AccessibleSlideComposition",
    "AccessibleSlidePolicy",
    "accessible_reveal_output_issues",
    "compose_accessible_pandoc_document",
    "enhance_accessible_reveal",
    "load_and_compose_pandoc_json",
]
