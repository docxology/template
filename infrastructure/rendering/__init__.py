"""Rendering Module.

This module provides tools for generating research outputs:
- PDFs (Manuscripts)
- Slides (Beamer/Reveal.js)
- Web (HTML5)
- DOCX (Microsoft Word, via pandoc)
- EPUB (e-reader, via pandoc)
"""

from .config import RenderingConfig
from .core import RenderManager
from .docx_renderer import DocxRenderResult, render_docx
from .docxplus_export import ExportResult, export_project, is_available as is_docxplus_available
from .docxplus_stage import run_docxplus_export
from .epub_renderer import EpubRenderResult, render_epub
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
    "DocxRenderResult",
    "EpubRenderResult",
    "EXCLUDED_DOC_FILENAMES",
    "ExportResult",
    "RenderManager",
    "RenderingConfig",
    "discover_manuscript_files",
    "export_project",
    "is_docxplus_available",
    "render_docx",
    "render_epub",
    "run_docxplus_export",
    "substitute_manuscript_text",
    "verify_figures_exist",
    "write_resolved_manuscript_tree",
]
