"""Minimal validation module for literature repo.

This module provides only the PDF text extraction functionality needed
by the literature module. It's a minimal subset of the full validation
module from the template repo.
"""

from .pdf_validator import extract_text_from_pdf, PDFValidationError

__all__ = [
    "extract_text_from_pdf",
    "PDFValidationError",
]

