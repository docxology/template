"""Elsevier/ScienceDirect HTML parser.

Handles PDF URL extraction from Elsevier and ScienceDirect pages.
"""
from __future__ import annotations

import re
from typing import List

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.html_parsers.base import BaseHTMLParser

logger = get_logger(__name__)


class ElsevierParser(BaseHTMLParser):
    """Parser for Elsevier/ScienceDirect pages."""
    
    priority = 100  # High priority for Elsevier
    
    def detect_publisher(self, url: str) -> bool:
        """Check if URL is from Elsevier/ScienceDirect."""
        return any(domain in url.lower() for domain in [
            'sciencedirect.com',
            'elsevier.com',
            'linkinghub.elsevier.com'
        ])
    
    def extract_pdf_urls(self, html_content: bytes, base_url: str) -> List[str]:
        """Extract PDF URLs from Elsevier/ScienceDirect HTML."""
        html_str = self._decode_html(html_content)
        candidates = []
        
        # Strategy 1: Extract PII (Paper Item Identifier) and construct PDF URL
        pii_patterns = [
            r'pii["\']?\s*[:=]\s*["\']([A-Z0-9]+)["\']',
            r'sciencedirect\.com/science/article/pii/([A-Z0-9]+)',
            r'data-pii=["\']([A-Z0-9]+)["\']',
            r'"pii":"([A-Z0-9]+)"',
        ]
        
        for pattern in pii_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for pii in matches:
                if pii:
                    # Construct ScienceDirect PDF URL
                    pdf_url = f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true"
                    if pdf_url not in candidates:
                        candidates.append(pdf_url)
        
        # Strategy 2: Look for direct PDF download links
        pdf_link_patterns = [
            r'href=["\']([^"\']*sciencedirect[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*elsevier[^"\']*\.pdf[^"\']*)["\']',
            r'data-pdf-url=["\']([^"\']*)["\']',
        ]
        
        for pattern in pdf_link_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match and '.pdf' in match.lower():
                    from urllib.parse import urljoin
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        # Strategy 3: Look for download button data attributes
        download_patterns = [
            r'data-download-url=["\']([^"\']*)["\']',
            r'downloadUrl["\']?\s*[:=]\s*["\']([^"\']*\.pdf[^"\']*)["\']',
        ]
        
        for pattern in download_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    from urllib.parse import urljoin
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        # Strategy 4: Generic PDF link search
        candidates.extend(self._find_pdf_links(html_str, base_url))
        
        return self._filter_valid_urls(candidates)

