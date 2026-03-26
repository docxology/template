"""LaTeX content transformation functions for PDF rendering.

Handles rewriting/fixing of generated LaTeX content:
- Figure path normalization for compilation from output/pdf/
- Math delimiter repair from Pandoc conversion artifacts

This module re-exports from focused sub-modules for backwards compatibility.
"""

from __future__ import annotations

from infrastructure.rendering._pdf_figure_paths import fix_figure_paths as fix_figure_paths
from infrastructure.rendering._pdf_math_delimiters import fix_math_delimiters as fix_math_delimiters

__all__ = [
    "fix_figure_paths",
    "fix_math_delimiters",
]
