"""
PDF validation module - Minimal version for literature repo.

This module provides PDF text extraction functionality needed by the
literature summarization system. It's a minimal subset of the full
validation module from the template repo.
"""

from pathlib import Path
import io
import contextlib
from infrastructure.core.logging_utils import get_logger


class PDFValidationError(Exception):
    """Raised when PDF validation encounters an error."""
    pass


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract all text content from a PDF file.

    Suppresses harmless pypdf warnings (e.g., "Ignoring wrong pointing object")
    that occur during PDF parsing of malformed objects.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as a single string

    Raises:
        PDFValidationError: If file doesn't exist or text extraction fails
    """
    if not pdf_path.exists():
        raise PDFValidationError(f"PDF file not found: {pdf_path}")

    logger = get_logger(__name__)

    try:
        from pypdf import PdfReader

        with open(pdf_path, 'rb') as file:
            # Capture stderr to suppress pypdf warnings (e.g., "Ignoring wrong pointing object")
            # These are harmless and indicate pypdf is gracefully handling malformed PDF objects
            stderr_capture = io.StringIO()
            with contextlib.redirect_stderr(stderr_capture):
                pdf_reader = PdfReader(file)
                text_parts = []

                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())

            # Log suppressed warnings at DEBUG level for troubleshooting
            captured_warnings = stderr_capture.getvalue().strip()
            if captured_warnings:
                logger.debug(f"Suppressed pypdf warnings for {pdf_path.name}: {captured_warnings}")

            return '\n'.join(text_parts)

    except Exception as e:
        raise PDFValidationError(f"Failed to extract text from PDF: {e}")

