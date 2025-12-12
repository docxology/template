"""IEEE Xplore HTML parser.

Handles PDF URL extraction from IEEE Xplore pages.
"""
from __future__ import annotations

import re
from typing import List
from urllib.parse import urljoin

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.html_parsers.base import BaseHTMLParser

logger = get_logger(__name__)


class IEEEParser(BaseHTMLParser):
    """Parser for IEEE Xplore pages."""
    
    priority = 85  # High priority for IEEE
    
    def detect_publisher(self, url: str) -> bool:
        """Check if URL is from IEEE."""
        return any(domain in url.lower() for domain in [
            'ieee.org',
            'ieeexplore.ieee.org',
            'ieeexploreapi.ieee.org'
        ])
    
    def extract_pdf_urls(self, html_content: bytes, base_url: str) -> List[str]:
        """Extract PDF URLs from IEEE Xplore HTML."""
        html_str = self._decode_html(html_content)
        candidates = []
        
        # Strategy 1: Extract document number (arnumber) and construct PDF URL
        arnumber_patterns = [
            r'arnumber["\']?\s*[:=]\s*["\']?([0-9]+)["\']?',
            r'ieee\.org/document/([0-9]+)',
            r'ieeexplore\.ieee\.org/document/([0-9]+)',
            r'documentNumber["\']?\s*[:=]\s*["\']?([0-9]+)["\']?',
            r'data-arnumber=["\']([0-9]+)["\']',
        ]
        
        for pattern in arnumber_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for arnumber in matches:
                if arnumber:
                    # IEEE PDF URL format
                    pdf_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?arnumber={arnumber}"
                    if pdf_url not in candidates:
                        candidates.append(pdf_url)
                    # Alternative format
                    alt_url = f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnumber}"
                    if alt_url not in candidates:
                        candidates.append(alt_url)
        
        # Strategy 2: Direct PDF links
        candidates.extend(self._find_pdf_links(html_str, base_url))
        
        # Strategy 3: Look for PDF download API endpoints
        api_patterns = [
            r'pdfUrl["\']?\s*[:=]\s*["\']([^"\']*ieee[^"\']*\.pdf[^"\']*)["\']',
            r'downloadUrl["\']?\s*[:=]\s*["\']([^"\']*ieee[^"\']*)["\']',
            r'href=["\']([^"\']*ieeexplore[^"\']*pdf[^"\']*)["\']',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        return self._filter_valid_urls(candidates)

