"""PDF text extraction and parsing utilities."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List
from urllib.parse import urljoin

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def extract_pdf_urls_from_html(html_content: bytes, base_url: str) -> List[str]:
    """Extract PDF URLs from HTML content using modular parser system.

    Uses publisher-specific parsers when available, falls back to generic parser.
    This function maintains backwards compatibility while using the new modular system.

    Args:
        html_content: Raw HTML content as bytes.
        base_url: Base URL for resolving relative links.

    Returns:
        List of candidate PDF URLs found in HTML.
    """
    try:
        from infrastructure.literature.html_parsers import extract_pdf_urls_modular
        return extract_pdf_urls_modular(html_content, base_url)
    except ImportError:
        # Fallback to old implementation if new parsers not available
        logger.warning("Modular HTML parsers not available, using fallback")
        return _extract_pdf_urls_fallback(html_content, base_url)


def _extract_pdf_urls_fallback(html_content: bytes, base_url: str) -> List[str]:
    """Fallback implementation for PDF URL extraction."""
    candidates: List[str] = []

    try:
        html_str = html_content.decode('utf-8', errors='ignore')
    except Exception:
        logger.debug("Failed to decode HTML content")
        return candidates

    # Basic PDF link extraction
    pdf_link_patterns = [
        r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
    ]

    for pattern in pdf_link_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                full_url = urljoin(base_url, match)
                if full_url not in candidates:
                    candidates.append(full_url)

    return candidates


def extract_citations(pdf_path: Path) -> List[str]:
    """Extract citations from PDF.
    
    Note: This is a placeholder for actual PDF parsing logic.
    Real implementation would use pypdf or similar.
    
    Args:
        pdf_path: Path to PDF file.
        
    Returns:
        List of extracted citations (empty for now).
    """
    if not pdf_path.exists():
        raise FileOperationError("PDF file not found", context={"path": str(pdf_path)})
        
    logger.warning(f"Citation extraction not implemented for {pdf_path}")
    return []

