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
    """Extract PDF URLs from HTML content.

    Searches for PDF links in HTML using multiple strategies:
    - Direct PDF links in <a> tags
    - Meta tags with PDF URLs
    - JavaScript variables containing PDF URLs
    - Publisher-specific patterns (Elsevier, Springer, IEEE, etc.)
    - Common academic site patterns

    Args:
        html_content: Raw HTML content as bytes.
        base_url: Base URL for resolving relative links.

    Returns:
        List of candidate PDF URLs found in HTML.
    """
    candidates: List[str] = []

    try:
        # Convert to string for easier processing
        html_str = html_content.decode('utf-8', errors='ignore')
    except Exception:
        logger.debug("Failed to decode HTML content")
        return candidates

    # Strategy 1: Find <a> tags with PDF links
    # Look for href attributes containing .pdf (case-insensitive)
    pdf_link_patterns = [
        r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
        r'href=["\']([^"\']*pdf[^"\']*)["\']',
    ]

    for pattern in pdf_link_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                # Resolve relative URLs
                full_url = urljoin(base_url, match)
                if full_url not in candidates:
                    candidates.append(full_url)

    # Strategy 2: Meta tags with PDF URLs
    meta_patterns = [
        r'<meta[^>]*content=["\']([^"\']*\.pdf[^"\']*)["\'][^>]*>',
        r'<meta[^>]*pdf[^>]*content=["\']([^"\']*\.pdf[^"\']*)["\'][^>]*>',
    ]

    for pattern in meta_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                full_url = urljoin(base_url, match)
                if full_url not in candidates:
                    candidates.append(full_url)

    # Strategy 3: JavaScript variables containing PDF URLs
    js_patterns = [
        r'pdfUrl["\']?\s*[:=]\s*["\']([^"\']*\.pdf[^"\']*)["\']',
        r'downloadUrl["\']?\s*[:=]\s*["\']([^"\']*\.pdf[^"\']*)["\']',
        r'pdf["\']?\s*[:=]\s*["\']([^"\']*\.pdf[^"\']*)["\']',
    ]

    for pattern in js_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                full_url = urljoin(base_url, match)
                if full_url not in candidates:
                    candidates.append(full_url)

    # Strategy 4: Publisher-specific patterns
    # Elsevier/ScienceDirect - multiple patterns
    elif_patterns = [
        r'pii["\']?\s*[:=]\s*["\']([A-Z0-9]+)["\']',  # PII in JSON/script
        r'sciencedirect\.com/science/article/pii/([A-Z0-9]+)',
    ]

    for pattern in elif_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                pdf_url = f"https://www.sciencedirect.com/science/article/pii/{match}/pdfft?isDTMRedir=true&download=true"
                if pdf_url not in candidates:
                    candidates.append(pdf_url)

    # Springer - look for article IDs
    springer_patterns = [
        r'springer\.com/article/([0-9]+)',
        r'link\.springer\.com/article/10\.\d+/([^/]+)',
    ]

    for pattern in springer_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                # Try to construct PDF URL (format varies)
                pdf_url = f"https://link.springer.com/content/pdf/{match}.pdf"
                if pdf_url not in candidates:
                    candidates.append(pdf_url)

    # IEEE - look for document numbers
    ieee_patterns = [
        r'ieee\.org/document/([0-9]+)',
        r'documentNumber["\']?\s*[:=]\s*["\']?([0-9]+)["\']?',
        r'arnumber["\']?\s*[:=]\s*["\']?([0-9]+)["\']?',
    ]

    for pattern in ieee_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                # Use stampPDF/getPDF.jsp format for arnumber pattern
                if 'arnumber' in pattern:
                    pdf_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?arnumber={match}"
                else:
                    pdf_url = f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={match}"
                if pdf_url not in candidates:
                    candidates.append(pdf_url)

    # ACM - look for article IDs
    acm_patterns = [
        r'acm\.org/doi/([0-9.]+/[0-9]+)',
        r'doi["\']?\s*[:=]\s*["\']?10\.1145/([0-9.]+/[0-9]+)["\']?',
    ]

    for pattern in acm_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                pdf_url = f"https://dl.acm.org/doi/pdf/10.1145/{match}"
                if pdf_url not in candidates:
                    candidates.append(pdf_url)

    # Strategy 5: Common academic site patterns
    # Look for common PDF link text patterns
    pdf_link_text_patterns = [
        r'(?:download|pdf|full.?text|full.?paper)[\s:]*["\']?([^"\']*\.pdf[^"\']*)["\']?',
        r'<a[^>]*>(?:Download|PDF|Full Text|Full Paper)[^<]*</a>[\s\S]*?href=["\']([^"\']*\.pdf[^"\']*)["\']',
    ]

    for pattern in pdf_link_text_patterns:
        matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in matches:
            if match:
                full_url = urljoin(base_url, match)
                if full_url not in candidates:
                    candidates.append(full_url)

    # Remove duplicates while preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)

    # Filter out invalid URL schemes (FTP, file, etc.)
    valid_candidates = []
    for url in unique_candidates:
        # Skip FTP and file URLs
        if url.startswith(("ftp://", "file://")):
            continue
        # Skip protocol-relative URLs that would resolve to invalid schemes
        if url.startswith("//") and not url.startswith("//http"):
            # Protocol-relative URLs are valid if they resolve to http/https
            # They'll be handled by urljoin, so we keep them
            pass
        valid_candidates.append(url)

    return valid_candidates


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

