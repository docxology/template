"""Content validation subpackage."""

from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.content.figure_validator import validate_figure_registry
from infrastructure.validation.content.markdown_validator import (
    validate_citations,
    validate_images,
    validate_markdown,
    validate_math,
    validate_pandoc_pitfalls,
    validate_refs,
)
from infrastructure.validation.content.pdf_validator import (
    extract_text_from_pdf,
    scan_for_issues,
    validate_pdf_rendering,
)

__all__ = [
    "discover_markdown_files",
    "extract_text_from_pdf",
    "scan_for_issues",
    "validate_citations",
    "validate_figure_registry",
    "validate_images",
    "validate_markdown",
    "validate_math",
    "validate_pandoc_pitfalls",
    "validate_pdf_rendering",
    "validate_refs",
]
