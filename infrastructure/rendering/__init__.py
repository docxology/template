"""Rendering Module.

This module provides tools for generating research outputs:
- PDFs (Manuscripts)
- Slides (Beamer/Reveal.js)
- Web (HTML5)
- DOCX (Microsoft Word, via pandoc)
- EPUB (e-reader, via pandoc)

Stable package exports resolve on first use; leaf imports do not initialize
unrelated rendering providers.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

_EXPORTS = {
    "DocxRenderResult": (".docx_renderer", "DocxRenderResult"),
    "EpubRenderResult": (".epub_renderer", "EpubRenderResult"),
    "EXCLUDED_DOC_FILENAMES": (".manuscript_injection", "EXCLUDED_DOC_FILENAMES"),
    "ExportResult": (".docxplus_export", "ExportResult"),
    "ManuscriptRenderCache": (".render_cache", "ManuscriptRenderCache"),
    "RenderManager": (".core", "RenderManager"),
    "RenderCacheError": (".render_cache", "RenderCacheError"),
    "RenderingConfig": (".config", "RenderingConfig"),
    "SectionCacheEntry": (".render_cache", "SectionCacheEntry"),
    "discover_manuscript_files": (".manuscript_discovery", "discover_manuscript_files"),
    "export_project": (".docxplus_export", "export_project"),
    "is_docxplus_available": (".docxplus_export", "is_available"),
    "render_docx": (".docx_renderer", "render_docx"),
    "render_epub": (".epub_renderer", "render_epub"),
    "run_docxplus_export": (".docxplus_stage", "run_docxplus_export"),
    "substitute_manuscript_text": (".manuscript_injection", "substitute_manuscript_text"),
    "verify_figures_exist": (".manuscript_discovery", "verify_figures_exist"),
    "write_resolved_manuscript_tree": (".manuscript_injection", "write_resolved_manuscript_tree"),
}

if TYPE_CHECKING:
    from .config import RenderingConfig
    from .core import RenderManager
    from .docx_renderer import DocxRenderResult, render_docx
    from .docxplus_export import ExportResult, export_project, is_available as is_docxplus_available
    from .docxplus_stage import run_docxplus_export
    from .epub_renderer import EpubRenderResult, render_epub
    from .manuscript_discovery import discover_manuscript_files, verify_figures_exist
    from .manuscript_injection import (
        EXCLUDED_DOC_FILENAMES,
        substitute_manuscript_text,
        write_resolved_manuscript_tree,
    )
    from .render_cache import ManuscriptRenderCache, RenderCacheError, SectionCacheEntry


__all__ = [
    "DocxRenderResult",
    "EpubRenderResult",
    "EXCLUDED_DOC_FILENAMES",
    "ExportResult",
    "ManuscriptRenderCache",
    "RenderManager",
    "RenderCacheError",
    "RenderingConfig",
    "SectionCacheEntry",
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


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXPORTS.keys())
