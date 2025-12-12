"""Base class for HTML parsers.

Provides common functionality for all publisher-specific parsers.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List
from urllib.parse import urljoin

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class BaseHTMLParser(ABC):
    """Abstract base class for HTML parsers.
    
    All publisher-specific parsers inherit from this class and implement
    the required methods for detecting publishers and extracting PDF URLs.
    """
    
    # Priority for parser selection (higher = tried first)
    priority: int = 0
    
    @abstractmethod
    def detect_publisher(self, url: str) -> bool:
        """Check if this parser can handle the given URL.
        
        Args:
            url: URL to check.
            
        Returns:
            True if this parser should handle the URL.
        """
        pass
    
    @abstractmethod
    def extract_pdf_urls(self, html_content: bytes, base_url: str) -> List[str]:
        """Extract PDF URLs from HTML content.
        
        Args:
            html_content: Raw HTML content as bytes.
            base_url: Base URL for resolving relative links.
            
        Returns:
            List of candidate PDF URLs found in HTML.
        """
        pass
    
    def _decode_html(self, html_content: bytes) -> str:
        """Decode HTML content to string.
        
        Args:
            html_content: Raw HTML bytes.
            
        Returns:
            Decoded HTML string.
        """
        try:
            return html_content.decode('utf-8', errors='ignore')
        except Exception:
            try:
                return html_content.decode('latin-1', errors='ignore')
            except Exception:
                logger.debug("Failed to decode HTML content")
                return ""
    
    def _find_pdf_links(self, html_str: str, base_url: str) -> List[str]:
        """Find PDF links in <a> tags.
        
        Args:
            html_str: HTML content as string.
            base_url: Base URL for resolving relative links.
            
        Returns:
            List of PDF URLs found.
        """
        candidates = []
        
        # Pattern for href attributes containing .pdf
        patterns = [
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*pdf[^"\']*)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        return candidates
    
    def _find_meta_tags(self, html_str: str, base_url: str) -> List[str]:
        """Find PDF URLs in meta tags.
        
        Args:
            html_str: HTML content as string.
            base_url: Base URL for resolving relative links.
            
        Returns:
            List of PDF URLs found in meta tags.
        """
        candidates = []
        
        patterns = [
            r'<meta[^>]*content=["\']([^"\']*\.pdf[^"\']*)["\'][^>]*>',
            r'<meta[^>]*pdf[^>]*content=["\']([^"\']*\.pdf[^"\']*)["\'][^>]*>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        return candidates
    
    def _find_javascript_vars(self, html_str: str, base_url: str) -> List[str]:
        """Find PDF URLs in JavaScript variables.
        
        Args:
            html_str: HTML content as string.
            base_url: Base URL for resolving relative links.
            
        Returns:
            List of PDF URLs found in JavaScript.
        """
        candidates = []
        
        patterns = [
            r'pdfUrl["\']?\s*[:=]\s*["\']([^"\']*\.pdf[^"\']*)["\']',
            r'downloadUrl["\']?\s*[:=]\s*["\']([^"\']*\.pdf[^"\']*)["\']',
            r'pdf["\']?\s*[:=]\s*["\']([^"\']*\.pdf[^"\']*)["\']',
            r'pdfLink["\']?\s*[:=]\s*["\']([^"\']*\.pdf[^"\']*)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    full_url = urljoin(base_url, match)
                    if full_url not in candidates:
                        candidates.append(full_url)
        
        return candidates
    
    def _filter_valid_urls(self, urls: List[str]) -> List[str]:
        """Filter out invalid URL schemes.
        
        Args:
            urls: List of candidate URLs.
            
        Returns:
            Filtered list of valid URLs.
        """
        valid = []
        for url in urls:
            # Skip FTP and file URLs
            if url.startswith(("ftp://", "file://")):
                continue
            # Skip empty or malformed URLs
            if not url or not url.startswith(("http://", "https://", "//")):
                continue
            valid.append(url)
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for url in valid:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        
        return unique

