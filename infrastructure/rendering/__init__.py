"""Rendering Module.

This module provides tools for generating research outputs:
- PDFs (Manuscripts)
- Slides (Beamer/Reveal.js)
- Web (HTML5)
- Posters
"""

from infrastructure.rendering.core import RenderManager
from infrastructure.rendering.config import RenderingConfig

__all__ = ["RenderManager", "RenderingConfig"]

