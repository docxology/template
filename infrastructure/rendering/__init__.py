"""Rendering Module.

This module provides tools for generating research outputs:
- PDFs (Manuscripts)
- Slides (Beamer/Reveal.js)
- Web (HTML5)
- Posters
"""

from infrastructure.rendering.core import RenderManager
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_discovery import (
    discover_manuscript_files,
    verify_figures_exist,
)

__all__ = [
    "RenderManager",
    "RenderingConfig",
    "discover_manuscript_files",
    "verify_figures_exist",
]

