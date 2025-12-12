"""ACM Digital Library HTML parser.

Handles PDF URL extraction from ACM Digital Library pages.
"""
from __future__ import annotations

import re
from typing import List
from urllib.parse import urljoin

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.html_parsers.base import BaseHTMLParser

logger = get_logger(__name__)


class ACMParser(BaseHTMLParser):
    """Parser for ACM Digital Library pages."""
    
    priority = 80  # High priority for ACM
    
    def detect_publisher(self, url: str) -> bool:
        """Check if URL is from ACM."""
        return any(domain in url.lower() for domain in [
            'acm.org',
            'dl.acm.org',
            'portal.acm.org'
        ])
    
    def extract_pdf_urls(self, html_content: bytes, base_url: str) -> List[str]:
        """Extract PDF URLs from ACM Digital Library HTML."""
        html_str = self._decode_html(html_content)
        candidates = []
        
        # Strategy 1: Extract DOI and construct PDF URL
        doi_patterns = [
            r'acm\.org/doi/([0-9.]+/[0-9]+)',
            r'dl\.acm\.org/doi/([0-9.]+/[0-9]+)',
            r'doi["\']?\s*[:=]\s*["\']?10\.1145/([0-9.]+/[0-9]+)["\']?',
            r'data-doi=["\']10\.1145/([0-9.]+/[0-9]+)["\']',
        ]
        
        for pattern in doi_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for doi_suffix in matches:
                if doi_suffix:
                    # ACM PDF URL format
                    pdf_url = f"https://dl.acm.org/doi/pdf/10.1145/{doi_suffix}"
                    if pdf_url not in candidates:
                        candidates.append(pdf_url)
        
        # Strategy 2: Extract article ID
        article_patterns = [
            r'acm\.org/citation\.cfm\?id=([0-9]+)',
            r'articleId["\']?\s*[:=]\s*["\']([0-9]+)["\']',
            r'data-article-id=["\']([0-9]+)["\']',
        ]
        
        for pattern in article_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for article_id in matches:
                if article_id:
                    pdf_url = f"https://dl.acm.org/doi/pdf/{article_id}"
                    if pdf_url not in candidates:
                        candidates.append(pdf_url)
        
        # Strategy 3: Direct PDF links
        candidates.extend(self._find_pdf_links(html_str, base_url))
        
        # Strategy 4: Look for download links
        download_patterns = [
            r'href=["\']([^"\']*acm[^"\']*pdf[^"\']*)["\']',
            r'pdfUrl["\']?\s*[:=]\s*["\']([^"\']*acm[^"\']*)["\']',
            r'data-pdf-url=["\']([^"\']*)["\']',
        ]
        
        for pattern in download_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        return self._filter_valid_urls(candidates)

