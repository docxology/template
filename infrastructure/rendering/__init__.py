"""Rendering Module.

This module provides tools for generating research outputs:
- PDFs (Manuscripts)
- Slides (Beamer/Reveal.js)
- Web (HTML5)
- Posters
"""

from .config import RenderingConfig
from .core import RenderManager
from .manuscript_discovery import (
    discover_manuscript_files,
    verify_figures_exist,
)
from .manuscript_injection import (
    EXCLUDED_DOC_FILENAMES,
    substitute_manuscript_text,
    write_resolved_manuscript_tree,
)


__all__ = [
    "EXCLUDED_DOC_FILENAMES",
    "RenderManager",
    "RenderingConfig",
    "discover_manuscript_files",
    "substitute_manuscript_text",
    "verify_figures_exist",
    "write_resolved_manuscript_tree",
]
