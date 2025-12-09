"""Wiley Online Library HTML parser.

Handles PDF URL extraction from Wiley Online Library pages.
"""
from __future__ import annotations

import re
from typing import List
from urllib.parse import urljoin

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.html_parsers.base import BaseHTMLParser

logger = get_logger(__name__)


class WileyParser(BaseHTMLParser):
    """Parser for Wiley Online Library pages."""
    
    priority = 75  # High priority for Wiley
    
    def detect_publisher(self, url: str) -> bool:
        """Check if URL is from Wiley."""
        return any(domain in url.lower() for domain in [
            'wiley.com',
            'onlinelibrary.wiley.com',
            'wileyonlinelibrary.com'
        ])
    
    def extract_pdf_urls(self, html_content: bytes, base_url: str) -> List[str]:
        """Extract PDF URLs from Wiley Online Library HTML."""
        html_str = self._decode_html(html_content)
        candidates = []
        
        # Strategy 1: Extract DOI and construct PDF URL
        doi_patterns = [
            r'onlinelibrary\.wiley\.com/doi/([0-9.]+/[^/]+)',
            r'doi["\']?\s*[:=]\s*["\']?10\.\d+/([^"\']+)["\']?',
            r'data-doi=["\']10\.\d+/([^"\']+)["\']',
        ]
        
        for pattern in doi_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for doi_suffix in matches:
                if doi_suffix:
                    # Extract DOI prefix from URL if available
                    doi_prefix_match = re.search(r'10\.(\d+)/', html_str)
                    prefix = doi_prefix_match.group(1) if doi_prefix_match else "1002"
                    pdf_url = f"https://onlinelibrary.wiley.com/doi/pdfdirect/10.{prefix}/{doi_suffix}"
                    if pdf_url not in candidates:
                        candidates.append(pdf_url)
        
        # Strategy 2: Extract article ID
        article_patterns = [
            r'articleId["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'data-article-id=["\']([^"\']+)["\']',
            r'wiley\.com/doi/([^/]+)',
        ]
        
        for pattern in article_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for article_id in matches:
                if article_id:
                    pdf_url = f"https://onlinelibrary.wiley.com/doi/pdfdirect/{article_id}"
                    if pdf_url not in candidates:
                        candidates.append(pdf_url)
        
        # Strategy 3: Direct PDF links
        candidates.extend(self._find_pdf_links(html_str, base_url))
        
        # Strategy 4: Look for download links
        download_patterns = [
            r'href=["\']([^"\']*wiley[^"\']*pdf[^"\']*)["\']',
            r'pdfUrl["\']?\s*[:=]\s*["\']([^"\']*wiley[^"\']*)["\']',
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

