"""Rendering Module.

This module provides tools for generating research outputs:
- PDFs (Manuscripts)
- Slides (Beamer/Reveal.js)
- Web (HTML5)
- Posters
"""

from typing import Optional

from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager
from infrastructure.rendering.manuscript_discovery import (
    discover_manuscript_files, verify_figures_exist)


def get_render_manager(config: Optional[RenderingConfig] = None) -> RenderManager:
    """Get a RenderManager instance.

    Args:
        config: Optional rendering configuration

    Returns:
        RenderManager instance
    """
    return RenderManager(config)


__all__ = [
    "RenderManager",
    "RenderingConfig",
    "discover_manuscript_files",
    "verify_figures_exist",
    "get_render_manager",
]
