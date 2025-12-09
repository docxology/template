"""Modular HTML parsers for extracting PDF URLs from publisher pages.

Provides publisher-specific parsers for common academic publishers:
- Elsevier/ScienceDirect
- Springer
- IEEE
- ACM
- Wiley
- Generic fallback

Parser Interface:
    - detect_publisher(url: str) -> bool: Check if parser applies
    - extract_pdf_urls(html: bytes, base_url: str) -> List[str]: Extract URLs
    - priority: int: Parser priority (higher = tried first)
"""
from __future__ import annotations

from typing import List

from infrastructure.literature.html_parsers.base import BaseHTMLParser
from infrastructure.literature.html_parsers.elsevier import ElsevierParser
from infrastructure.literature.html_parsers.springer import SpringerParser
from infrastructure.literature.html_parsers.ieee import IEEEParser
from infrastructure.literature.html_parsers.acm import ACMParser
from infrastructure.literature.html_parsers.wiley import WileyParser
from infrastructure.literature.html_parsers.generic import GenericParser

__all__ = [
    "BaseHTMLParser",
    "ElsevierParser",
    "SpringerParser",
    "IEEEParser",
    "ACMParser",
    "WileyParser",
    "GenericParser",
    "get_parser_for_url",
    "extract_pdf_urls_modular",
]


def get_parser_for_url(url: str) -> BaseHTMLParser:
    """Get the appropriate parser for a given URL.
    
    Tries parsers in priority order until one matches.
    
    Args:
        url: URL to get parser for.
        
    Returns:
        BaseHTMLParser instance that can handle the URL.
    """
    # Ordered by priority (higher priority first)
    parsers = [
        ElsevierParser(),
        SpringerParser(),
        IEEEParser(),
        ACMParser(),
        WileyParser(),
        GenericParser(),  # Always matches, so last
    ]
    
    for parser in parsers:
        if parser.detect_publisher(url):
            return parser
    
    # Fallback to generic (should never reach here)
    return GenericParser()


def extract_pdf_urls_modular(html_content: bytes, base_url: str) -> List[str]:
    """Extract PDF URLs using modular parser system.
    
    Automatically detects publisher and uses appropriate parser.
    
    Args:
        html_content: Raw HTML content as bytes.
        base_url: Base URL for resolving relative links.
        
    Returns:
        List of candidate PDF URLs found in HTML.
    """
    parser = get_parser_for_url(base_url)
    return parser.extract_pdf_urls(html_content, base_url)

