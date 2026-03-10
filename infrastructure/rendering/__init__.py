"""Rendering Module.

This module provides tools for generating research outputs:
- PDFs (Manuscripts)
- Slides (Beamer/Reveal.js)
- Web (HTML5)
- Posters
"""

from __future__ import annotations

from .config import RenderingConfig
from .core import RenderManager
from .manuscript_discovery import (
    discover_manuscript_files,
    verify_figures_exist,
)


__all__ = [
    "RenderManager",
    "RenderingConfig",
    "discover_manuscript_files",
    "verify_figures_exist",
]
