"""Generic HTML parser (fallback).

Handles PDF URL extraction from any HTML page using generic patterns.
This parser always matches and is used as a fallback when publisher-specific
parsers don't match.
"""
from __future__ import annotations

from typing import List

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.html_parsers.base import BaseHTMLParser

logger = get_logger(__name__)


class GenericParser(BaseHTMLParser):
    """Generic parser for any HTML page (fallback)."""
    
    priority = 0  # Lowest priority - always matches
    
    def detect_publisher(self, url: str) -> bool:
        """Always matches (fallback parser)."""
        return True
    
    def extract_pdf_urls(self, html_content: bytes, base_url: str) -> List[str]:
        """Extract PDF URLs using generic patterns."""
        html_str = self._decode_html(html_content)
        candidates = []
        
        # Use all generic strategies from base class
        candidates.extend(self._find_pdf_links(html_str, base_url))
        candidates.extend(self._find_meta_tags(html_str, base_url))
        candidates.extend(self._find_javascript_vars(html_str, base_url))
        
        # Additional generic patterns
        # Look for common PDF link text patterns
        pdf_link_text_patterns = [
            r'(?:download|pdf|full.?text|full.?paper)[\s:]*["\']?([^"\']*\.pdf[^"\']*)["\']?',
            r'<a[^>]*>(?:Download|PDF|Full Text|Full Paper)[^<]*</a>[\s\S]*?href=["\']([^"\']*\.pdf[^"\']*)["\']',
        ]
        
        import re
        from urllib.parse import urljoin
        
        for pattern in pdf_link_text_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        return self._filter_valid_urls(candidates)

