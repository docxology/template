"""Springer Link HTML parser.

Handles PDF URL extraction from Springer Link pages.
"""
from __future__ import annotations

import re
from typing import List
from urllib.parse import urljoin

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.html_parsers.base import BaseHTMLParser

logger = get_logger(__name__)


class SpringerParser(BaseHTMLParser):
    """Parser for Springer Link pages."""
    
    priority = 90  # High priority for Springer
    
    def detect_publisher(self, url: str) -> bool:
        """Check if URL is from Springer."""
        return any(domain in url.lower() for domain in [
            'springer.com',
            'link.springer.com',
            'springerlink.com'
        ])
    
    def extract_pdf_urls(self, html_content: bytes, base_url: str) -> List[str]:
        """Extract PDF URLs from Springer Link HTML."""
        html_str = self._decode_html(html_content)
        candidates = []
        
        # Strategy 1: Extract article ID and construct PDF URL
        article_id_patterns = [
            r'springer\.com/article/([0-9]+)',
            r'link\.springer\.com/article/10\.\d+/([^/]+)',
            r'link\.springer\.com/content/pdf/10\.\d+/([^/]+)\.pdf',
            r'articleId["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'data-article-id=["\']([^"\']+)["\']',
        ]
        
        for pattern in article_id_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for article_id in matches:
                if article_id:
                    # Try different Springer PDF URL formats
                    pdf_urls = [
                        f"https://link.springer.com/content/pdf/10.1007/{article_id}.pdf",
                        f"https://link.springer.com/content/pdf/{article_id}.pdf",
                        f"https://link.springer.com/article/{article_id}/pdf",
                    ]
                    for pdf_url in pdf_urls:
                        if pdf_url not in candidates:
                            candidates.append(pdf_url)
        
        # Strategy 2: Look for DOI and construct PDF URL
        doi_patterns = [
            r'doi["\']?\s*[:=]\s*["\']10\.(\d+)/([^"\']+)["\']',
            r'data-doi=["\']10\.(\d+)/([^"\']+)["\']',
            r'link\.springer\.com/article/10\.(\d+)/([^/]+)',
        ]
        
        for pattern in doi_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    prefix, suffix = match
                    pdf_url = f"https://link.springer.com/content/pdf/10.{prefix}/{suffix}.pdf"
                    if pdf_url not in candidates:
                        candidates.append(pdf_url)
        
        # Strategy 3: Direct PDF links
        candidates.extend(self._find_pdf_links(html_str, base_url))
        
        # Strategy 4: Look for download button
        download_patterns = [
            r'data-pdf-url=["\']([^"\']*)["\']',
            r'pdfDownloadUrl["\']?\s*[:=]\s*["\']([^"\']*)["\']',
            r'href=["\']([^"\']*springer[^"\']*pdf[^"\']*)["\']',
        ]
        
        for pattern in download_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        return self._filter_valid_urls(candidates)

