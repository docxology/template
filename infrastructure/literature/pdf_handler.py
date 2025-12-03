"""PDF handling utilities for literature search."""
from __future__ import annotations

import os
import random
import time
import requests
from pathlib import Path
from typing import Optional, List, Tuple, TYPE_CHECKING

from infrastructure.core.exceptions import FileOperationError, LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.config import LiteratureConfig, BROWSER_USER_AGENTS
from infrastructure.literature.api import SearchResult, UnpaywallSource, ArxivSource, BiorxivSource

if TYPE_CHECKING:
    from infrastructure.literature.library_index import LibraryIndex

logger = get_logger(__name__)


def _is_pdf_content(content: bytes) -> bool:
    """Check if content is a PDF by examining magic bytes.

    Args:
        content: Raw response content bytes.

    Returns:
        True if content starts with PDF magic bytes.
    """
    return content.startswith(b'%PDF')


def _is_html_content(content: bytes) -> bool:
    """Check if content appears to be HTML by examining the beginning.

    Args:
        content: Raw response content bytes.

    Returns:
        True if content appears to be HTML.
    """
    if not content:
        return False

    # Convert to string for easier checking (first 1KB should be enough)
    content_str = content[:1024].decode('utf-8', errors='ignore').lower().strip()

    # Check for common HTML indicators
    html_indicators = [
        '<!doctype html',
        '<html',
        '<head',
        '<body',
        '<div',
        '<script',
        '<meta',
        'text/html',
        '<title>',
        '<?xml',
    ]

    for indicator in html_indicators:
        if indicator in content_str:
            return True

    return False


def _extract_pdf_urls_from_html(html_content: bytes, base_url: str) -> List[str]:
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
    import re
    from urllib.parse import urljoin, urlparse

    candidates: List[str] = []
    candidates_set = set()  # Use set for O(1) lookups

    # Limit HTML size to prevent catastrophic backtracking with very large content
    # Most real-world HTML pages are < 1MB, so limit to first 1MB for performance
    MAX_HTML_SIZE = 1024 * 1024  # 1MB
    if len(html_content) > MAX_HTML_SIZE:
        logger.debug(f"HTML content too large ({len(html_content)} bytes), limiting to {MAX_HTML_SIZE} bytes")
        html_content = html_content[:MAX_HTML_SIZE]

    try:
        # Convert to string for easier processing
        html_str = html_content.decode('utf-8', errors='ignore')
    except Exception:
        logger.debug("Failed to decode HTML content")
        return candidates

    # Convert to lowercase for case-insensitive matching
    html_lower = html_str.lower()

    # Early exit if no PDF-related content found
    # Check for PDF-related content or publisher identifiers
    has_pdf_content = (
        'pdf' in html_lower or
        '.pdf' in html_lower or
        'pii' in html_lower or
        'arnumber' in html_lower or
        'doi' in html_lower
    )
    if not has_pdf_content:
        return candidates

    # Helper function to add candidate URLs
    def add_candidate(url: str):
        """Add URL to candidates if not already present."""
        full_url = urljoin(base_url, url)
        if full_url not in candidates_set:
            candidates_set.add(full_url)
            candidates.append(full_url)

    # Strategy 1: Find <a> tags with PDF links
    # Look for href attributes containing .pdf (case-insensitive)
    # Use non-greedy quantifiers and limit match scope to prevent backtracking
    pdf_link_patterns = [
        r'href=["\']([^"\']*?\.pdf[^"\']*?)["\']',  # Non-greedy to prevent backtracking
        r'href=["\']([^"\']*?pdf[^"\']*?)["\']',   # Non-greedy to prevent backtracking
    ]

    for pattern in pdf_link_patterns:
        try:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    add_candidate(match)
        except re.error:
            # Skip pattern if it causes regex errors
            logger.debug(f"Regex pattern failed: {pattern}")
            continue

    # Strategy 2: Meta tags with PDF URLs
    # Use non-greedy quantifiers and limit scope to prevent catastrophic backtracking
    meta_patterns = [
        r'<meta[^>]*?content=["\']([^"\']*?\.pdf[^"\']*?)["\'][^>]*?>',  # Non-greedy
        r'<meta[^>]*?pdf[^>]*?content=["\']([^"\']*?\.pdf[^"\']*?)["\'][^>]*?>',  # Non-greedy
    ]

    for pattern in meta_patterns:
        try:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    add_candidate(match)
        except re.error:
            logger.debug(f"Regex pattern failed: {pattern}")
            continue

    # Strategy 3: JavaScript variables containing PDF URLs
    # Use non-greedy quantifiers to prevent backtracking
    js_patterns = [
        r'pdfUrl["\']?\s*[:=]\s*["\']([^"\']*?\.pdf[^"\']*?)["\']',  # Non-greedy
        r'downloadUrl["\']?\s*[:=]\s*["\']([^"\']*?\.pdf[^"\']*?)["\']',  # Non-greedy
        r'pdf["\']?\s*[:=]\s*["\']([^"\']*?\.pdf[^"\']*?)["\']',  # Non-greedy
    ]

    for pattern in js_patterns:
        try:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    add_candidate(match)
        except re.error:
            logger.debug(f"Regex pattern failed: {pattern}")
            continue

    # Strategy 4: Publisher-specific patterns
    # Elsevier/ScienceDirect - multiple patterns
    elif_patterns = [
        r'pii["\']?\s*[:=]\s*["\']([A-Z0-9]+)["\']',  # PII in JSON/script
        r'/science/article/pii/([A-Z0-9]+)',  # URL pattern
        r'data-pii=["\']([A-Z0-9]+)["\']',  # Data attribute
        r'article-pii["\']?\s*:\s*["\']([A-Z0-9]+)["\']',  # JSON field
    ]
    for pattern in elif_patterns:
        elif_matches = re.findall(pattern, html_str, re.IGNORECASE)
        for pii in elif_matches:
            pdf_url = f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true"
            if pdf_url not in candidates_set:
                candidates_set.add(pdf_url)
                candidates.append(pdf_url)

    # Springer - multiple patterns
    springer_patterns = [
        r'/chapter/pdf/([^"\']+)',
        r'/article/([^"\']+)/pdf',
        r'/content/pdf/([^"\']+)',
    ]
    for pattern in springer_patterns:
        springer_matches = re.findall(pattern, html_str, re.IGNORECASE)
        for match in springer_matches:
            pdf_url = f"https://link.springer.com/content/pdf/{match}"
            if pdf_url not in candidates_set:
                candidates_set.add(pdf_url)
                candidates.append(pdf_url)

    # IEEE Xplore - multiple patterns
    ieee_patterns = [
        r'arnumber["\']?\s*[:=]\s*["\'](\d+)["\']',
        r'/document/(\d+)/',
        r'/abstract/document/(\d+)/',
    ]
    for pattern in ieee_patterns:
        ieee_matches = re.findall(pattern, html_str, re.IGNORECASE)
        for arnumber in ieee_matches:
            pdf_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?arnumber={arnumber}"
            if pdf_url not in candidates_set:
                candidates_set.add(pdf_url)
                candidates.append(pdf_url)

    # Wiley Online Library - multiple patterns
    wiley_patterns = [
        r'doi["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        r'/doi/([^"\']+)/pdf',
        r'/doi/pdf/([^"\']+)',
    ]
    for pattern in wiley_patterns:
        wiley_matches = re.findall(pattern, html_str, re.IGNORECASE)
        for doi in wiley_matches:
            # Clean DOI
            doi_clean = doi.replace('doi:', '').replace('http://dx.doi.org/', '').replace('https://doi.org/', '')
            pdf_url = f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi_clean}"
            if pdf_url not in candidates_set:
                candidates_set.add(pdf_url)
                candidates.append(pdf_url)

    # Nature/Springer Nature
    nature_patterns = [
        r'/articles/([^"\']+)',
        r'/nature communications/articles/([^"\']+)',
    ]
    for pattern in nature_patterns:
        nature_matches = re.findall(pattern, html_str, re.IGNORECASE)
        for article_id in nature_matches:
            if not article_id.endswith('.pdf'):
                pdf_url = f"https://www.nature.com/articles/{article_id}.pdf"
                if pdf_url not in candidates_set:
                    candidates_set.add(pdf_url)
                    candidates.append(pdf_url)

    # PLOS ONE
    plos_pattern = r'/plosone/article\?id=([^"\']+)'
    plos_matches = re.findall(plos_pattern, html_str, re.IGNORECASE)
    for article_id in plos_matches:
        pdf_url = f"https://journals.plos.org/plosone/article/file?id={article_id}&type=printable"
        if pdf_url not in candidates_set:
            candidates_set.add(pdf_url)
            candidates.append(pdf_url)

    # Frontiers in Psychology and other Frontiers journals
    frontiers_patterns = [
        r'/articles/([^"\']+)/full',
        r'frontiersin\.org/articles/([^"\']+)',
    ]
    for pattern in frontiers_patterns:
        frontiers_matches = re.findall(pattern, html_str, re.IGNORECASE)
        for article_id in frontiers_matches:
            if '/full' in article_id:
                article_id = article_id.replace('/full', '')
            pdf_url = f"https://www.frontiersin.org/articles/{article_id}/pdf"
            if pdf_url not in candidates_set:
                candidates_set.add(pdf_url)
                candidates.append(pdf_url)

    # Entropy (MDPI)
    entropy_patterns = [
        r'entropy[^"]*article/([^"\']+)',
        r'/entropy/article/([^"\']+)',
    ]
    for pattern in entropy_patterns:
        entropy_matches = re.findall(pattern, html_str, re.IGNORECASE)
        for article_id in entropy_matches:
            pdf_url = f"https://www.mdpi.com/1099-4300/{article_id}/pdf"
            if pdf_url not in candidates_set:
                candidates_set.add(pdf_url)
                candidates.append(pdf_url)

    # Strategy 5: Common academic patterns
    # Look for "Download PDF" links
    # Limit match scope to prevent excessive backtracking
    download_patterns = [
        r'href=["\']([^"\']*?)["\'][^>]*?>.*?download.*?pdf',  # Non-greedy, limit scope
        r'href=["\']([^"\']*?)["\'][^>]*?>.*?pdf.*?download',  # Non-greedy, limit scope
        r'href=["\']([^"\']*?\.pdf[^"\']*?)["\'][^>]*?>.*?download',  # Non-greedy
        r'href=["\']([^"\']*?pdf[^"\']*?)["\'][^>]*?>.*?download',  # Non-greedy
    ]

    for pattern in download_patterns:
        try:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match and not match.startswith('javascript:'):
                    add_candidate(match)
        except re.error:
            logger.debug(f"Regex pattern failed: {pattern}")
            continue

    # Strategy 6: Look for PDF links in common HTML structures
    # Check for links with "pdf" in URL or text
    # Use non-greedy quantifiers to prevent backtracking
    pdf_href_patterns = [
        r'href=["\']([^"\']*?pdf[^"\']*?)["\']',  # Non-greedy
        r'href=["\']([^"\']*?\.pdf[^"\']*?)["\']',  # Non-greedy
    ]

    for pattern in pdf_href_patterns:
        try:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    add_candidate(match)
        except re.error:
            logger.debug(f"Regex pattern failed: {pattern}")
            continue

    # Strategy 7: Look for JavaScript onclick handlers that might contain PDF URLs
    # Use non-greedy quantifiers and limit scope
    js_onclick_patterns = [
        r'onclick=["\'][^"\']*?window\.open\(["\']([^"\']*?pdf[^"\']*?)["\']',  # Non-greedy
        r'onclick=["\'][^"\']*?location\.href=["\']([^"\']*?pdf[^"\']*?)["\']',  # Non-greedy
        r'onclick=["\'][^"\']*?pdf[^"\']*?["\']([^"\']*?pdf[^"\']*?)["\']',  # Non-greedy
    ]

    for pattern in js_onclick_patterns:
        try:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    add_candidate(match)
        except re.error:
            logger.debug(f"Regex pattern failed: {pattern}")
            continue

    # Strategy 8: Look for data attributes that might contain PDF URLs
    # Use non-greedy quantifiers
    data_attr_patterns = [
        r'data-pdf-url=["\']([^"\']*?)["\']',  # Non-greedy
        r'data-download-url=["\']([^"\']*?pdf[^"\']*?)["\']',  # Non-greedy
        r'data-file-url=["\']([^"\']*?pdf[^"\']*?)["\']',  # Non-greedy
    ]

    for pattern in data_attr_patterns:
        try:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    add_candidate(match)
        except re.error:
            logger.debug(f"Regex pattern failed: {pattern}")
            continue

    # Strategy 9: Look for meta tags with PDF URLs (additional patterns)
    # Use non-greedy quantifiers to prevent backtracking
    meta_pdf_patterns = [
        r'<meta[^>]*?property=["\']og:pdf["\'][^>]*?content=["\']([^"\']*?)["\']',  # Non-greedy
        r'<meta[^>]*?name=["\']citation_pdf_url["\'][^>]*?content=["\']([^"\']*?)["\']',  # Non-greedy
        r'<meta[^>]*?pdf.*?content=["\']([^"\']*?)["\']',  # Non-greedy
    ]

    for pattern in meta_pdf_patterns:
        try:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            for match in matches:
                if match:
                    add_candidate(match)
        except re.error:
            logger.debug(f"Regex pattern failed: {pattern}")
            continue

    # Filter and validate URLs
    valid_candidates = []
    for url in candidates:
        # Basic validation: must be absolute URL and contain pdf
        if url.startswith(('http://', 'https://')) and ('pdf' in url.lower() or url.endswith('.pdf')):
            # Avoid obviously invalid URLs
            if not any(skip in url.lower() for skip in ['javascript:', 'mailto:', '#']):
                valid_candidates.append(url)

    logger.debug(f"Extracted {len(valid_candidates)} PDF URLs from HTML")
    return valid_candidates


def _doi_to_pdf_urls(doi: str) -> List[str]:
    """Convert a DOI to potential PDF download URLs for common publishers.

    Args:
        doi: The DOI string (with or without doi.org prefix)

    Returns:
        List of potential PDF URLs for the DOI
    """
    # Clean the DOI
    doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '').replace('doi:', '')

    candidates = []

    # Elsevier/ScienceDirect
    if doi.startswith('10.1016/') or doi.startswith('10.1017/'):
        # Extract PII from DOI for ScienceDirect
        parts = doi.split('/')
        if len(parts) >= 2:
            pii = parts[-1]
            candidates.append(f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true")

    # Springer
    if 'springer' in doi.lower() or doi.startswith('10.1007/') or doi.startswith('10.1038/'):
        candidates.append(f"https://link.springer.com/content/pdf/{doi}.pdf")

    # Wiley
    if doi.startswith('10.1002/') or doi.startswith('10.1111/') or 'wiley' in doi.lower():
        candidates.append(f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}")

    # PLOS
    if doi.startswith('10.1371/'):
        candidates.append(f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable")

    # Frontiers
    if doi.startswith('10.3389/'):
        candidates.append(f"https://www.frontiersin.org/articles/{doi}/pdf")

    # MDPI
    if doi.startswith('10.3390/'):
        candidates.append(f"https://www.mdpi.com/article/10.3390/{doi.split('/', 1)[1]}/pdf")

    # Nature
    if doi.startswith('10.1038/'):
        candidates.append(f"https://www.nature.com/articles/{doi}.pdf")

    # Oxford University Press
    if doi.startswith('10.1093/'):
        candidates.append(f"https://academic.oup.com/view-pdf/doi/{doi}")

    # Generic DOI resolver fallback
    candidates.append(f"https://doi.org/{doi}")

    return candidates


def _transform_pdf_url(url: str) -> List[str]:
    """Transform URL to multiple candidate PDF URLs for known sources.

    Generates a list of alternative URLs to try when the primary URL fails.
    Handles PMC, Europe PMC, and other common academic sources.

    Args:
        url: Original URL that might be an HTML landing page.

    Returns:
        List of candidate URLs to try, in priority order.
    """
    import re

    candidates: List[str] = []

    # Extract PMC ID from various URL patterns
    pmc_id = None

    # Pattern 1: www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/
    pmc_match = re.search(r'(?:www\.)?ncbi\.nlm\.nih\.gov/pmc/articles/(PMC\d+)', url)
    if pmc_match:
        pmc_id = pmc_match.group(1)

    # Pattern 2: pmc.ncbi.nlm.nih.gov/articles/PMC123456/
    if not pmc_id:
        pmc_match = re.search(r'pmc\.ncbi\.nlm\.nih\.gov/articles/(PMC\d+)', url)
        if pmc_match:
            pmc_id = pmc_match.group(1)

    # Pattern 3: europepmc.org/article/PMC/123456 or europepmc.org/articles/PMC123456
    if not pmc_id:
        pmc_match = re.search(r'europepmc\.org/(?:article|articles)/(?:PMC/)?(\d+|PMC\d+)', url)
        if pmc_match:
            pmc_id_raw = pmc_match.group(1)
            pmc_id = pmc_id_raw if pmc_id_raw.startswith('PMC') else f"PMC{pmc_id_raw}"

    # Generate PMC URL candidates if we found a PMC ID
    if pmc_id:
        # Direct NCBI PDF endpoints (multiple patterns publishers use)
        candidates.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/")
        candidates.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/main.pdf")

        # PMC new domain
        candidates.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/pdf/")
        candidates.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/pdf/main.pdf")

        # Europe PMC (often more accessible)
        candidates.append(f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmc_id}&blobtype=pdf")
        candidates.append(f"https://europepmc.org/articles/{pmc_id}?pdf=render")

        # FTP-style direct access (older papers)
        pmc_num = pmc_id.replace('PMC', '')
        candidates.append(f"https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/{pmc_num}.pdf")

    # Handle Elsevier/ScienceDirect patterns
    sd_match = re.search(r'sciencedirect\.com/science/article/pii/([A-Z0-9]+)', url, re.IGNORECASE)
    if sd_match:
        pii = sd_match.group(1)
        # Elsevier open access PDF endpoint (works for some OA papers)
        candidates.append(f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true")

    # Handle MDPI patterns (often open access)
    mdpi_match = re.search(r'mdpi\.com/(\d+-\d+)/(\d+)/(\d+)/(\d+)', url)
    if mdpi_match:
        journal, volume, issue, article = mdpi_match.groups()
        candidates.append(f"https://www.mdpi.com/{journal}/{volume}/{issue}/{article}/pdf")

    # Handle Frontiers patterns (open access)
    frontiers_match = re.search(r'frontiersin\.org/(?:articles|journals)/.+/full$', url)
    if frontiers_match:
        candidates.append(url.replace('/full', '/pdf'))

    # Handle arXiv patterns (ensure we have the PDF link)
    # arXiv IDs can be: YYMM.NNNNN (new format) or category/YYMMNNN (old format)
    arxiv_match = re.search(r'arxiv\.org/abs/((?:\d{4}\.\d{4,5})|(?:\w+-\w+/\d{7}))(?:v\d+)?', url)
    if arxiv_match:
        arxiv_id = arxiv_match.group(1)
        candidates.append(f"https://arxiv.org/pdf/{arxiv_id}.pdf")
        candidates.append(f"https://export.arxiv.org/pdf/{arxiv_id}.pdf")

    # Handle bioRxiv/medRxiv patterns
    biorxiv_match = re.search(r'(biorxiv|medrxiv)\.org/content/([\d.]+v?\d*)', url)
    if biorxiv_match:
        server, content_id = biorxiv_match.groups()
        candidates.append(f"https://www.{server}.org/content/{content_id}.full.pdf")

    # Remove duplicates while preserving order, and exclude original URL
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen and c != url:
            seen.add(c)
            unique_candidates.append(c)

    return unique_candidates


class PDFHandler:
    """Handles PDF downloading and text extraction.
    
    Downloads PDFs using citation keys as filenames for consistency
    with the BibTeX and library index. Supports retry logic, User-Agent
    rotation, and multiple fallback strategies for failed downloads:
    
    Fallback Order:
    1. Primary URL (from search result)
    2. Transformed URLs (PMC variants, arXiv, bioRxiv patterns)
    3. Unpaywall lookup (open access versions)
    4. arXiv title search (find preprint by title)
    5. bioRxiv/medRxiv DOI lookup (find preprint by DOI)
    """

    def __init__(self, config: LiteratureConfig, library_index: Optional["LibraryIndex"] = None):
        """Initialize PDF handler.
        
        Args:
            config: Literature configuration.
            library_index: Optional LibraryIndex for citation key generation and tracking.
        """
        self.config = config
        self._library_index = library_index
        
        # Initialize fallback sources
        self._unpaywall: Optional[UnpaywallSource] = None
        if config.use_unpaywall and config.unpaywall_email:
            self._unpaywall = UnpaywallSource(config)
        
        # arXiv fallback for title-based search
        self._arxiv = ArxivSource(config)
        
        # bioRxiv/medRxiv fallback for DOI-based lookup
        self._biorxiv = BiorxivSource(config)
        
        self._ensure_download_dir()

    def set_library_index(self, library_index: "LibraryIndex") -> None:
        """Set the library index for coordinated operations.

        Args:
            library_index: LibraryIndex instance to use.
        """
        self._library_index = library_index

    def parse_html_for_pdf(self, html_content: bytes, base_url: str) -> List[str]:
        """Parse HTML content to extract PDF URLs.

        Uses multiple strategies to find PDF links in HTML content:
        - Direct PDF links in <a> tags
        - Meta tags with PDF URLs
        - JavaScript variables containing PDF URLs
        - Publisher-specific patterns

        Args:
            html_content: Raw HTML content as bytes.
            base_url: Base URL for resolving relative links.

        Returns:
            List of candidate PDF URLs found in HTML.
        """
        return _extract_pdf_urls_from_html(html_content, base_url)

    def _ensure_download_dir(self) -> None:
        """Ensure download directory exists."""
        try:
            os.makedirs(self.config.download_dir, exist_ok=True)
        except OSError as e:
            raise FileOperationError(
                f"Failed to create download directory: {e}",
                context={"path": self.config.download_dir}
            )

    def _get_user_agent(self) -> str:
        """Get User-Agent string for requests.
        
        Returns a browser-like User-Agent if configured, otherwise
        the default API User-Agent.
        
        Returns:
            User-Agent string.
        """
        if self.config.use_browser_user_agent and BROWSER_USER_AGENTS:
            return random.choice(BROWSER_USER_AGENTS)
        return self.config.user_agent
    
    def _categorize_error(self, error: Exception, status_code: Optional[int] = None) -> Tuple[str, str]:
        """Categorize an error into failure reason and message.

        Args:
            error: The exception that occurred.
            status_code: HTTP status code if available.

        Returns:
            Tuple of (failure_reason, failure_message).
        """
        error_str = str(error)

        # Check for specific error messages first
        if "Received HTML instead of PDF" in error_str:
            return ("html_response", f"HTML received instead of PDF: {error_str}")
        elif "no working PDF URLs found in content" in error_str:
            return ("html_no_pdf_link", f"HTML page contains no PDF links: {error_str}")
        elif "Content-Type mismatch" in error_str:
            return ("content_mismatch", f"Content-Type header doesn't match actual content: {error_str}")

        # Check HTTP status codes
        if status_code == 403:
            return ("access_denied", f"403 Forbidden: {error_str}")
        elif status_code == 404:
            return ("not_found", f"404 Not Found: {error_str}")
        elif status_code == 429:
            return ("rate_limited", f"429 Too Many Requests: {error_str}")
        elif status_code == 502:
            return ("server_error", f"502 Bad Gateway: {error_str}")
        elif status_code == 503:
            return ("server_error", f"503 Service Unavailable: {error_str}")
        elif status_code and status_code >= 500:
            return ("server_error", f"Server error {status_code}: {error_str}")

        # Check exception types and messages
        elif "timeout" in error_str.lower() or isinstance(error, requests.exceptions.Timeout):
            return ("timeout", f"Request timed out: {error_str}")
        elif isinstance(error, requests.exceptions.ConnectionError):
            return ("network_error", f"Connection error: {error_str}")
        elif isinstance(error, requests.exceptions.RequestException):
            return ("network_error", f"Request failed: {error_str}")
        elif "redirect" in error_str.lower() and "loop" in error_str.lower():
            return ("redirect_loop", f"Redirect loop detected: {error_str}")
        else:
            return ("unknown", error_str)

    def download_pdf(
        self,
        url: Optional[str],
        filename: Optional[str] = None,
        result: Optional[SearchResult] = None
    ) -> Path:
        """Download PDF from URL with enhanced retry logic and fallback strategies.

        Attempts to download with exponential backoff retry and multiple fallback strategies.
        For 403 Forbidden errors, tries alternative User-Agents and request methods.
        If configured, will try Unpaywall as fallback when primary download fails.

        Args:
            url: URL to download from.
            filename: Optional filename (default: derived from result or URL).
            result: Optional SearchResult for citation key naming.

        Returns:
            Path to downloaded file.

        Raises:
            LiteratureSearchError: If all download attempts fail.
        """
        # Determine filename
        if not filename:
            if result and self._library_index:
                # Use citation key as filename
                citation_key = self._library_index.generate_citation_key(
                    result.title, result.authors, result.year
                )
                filename = f"{citation_key}.pdf"
            elif result:
                # Generate key locally
                filename = self._generate_filename_from_result(result)
            else:
                # Fall back to URL-based naming
                filename = url.split('/')[-1]
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'

        output_path = Path(self.config.download_dir) / filename

        if output_path.exists():
            logger.info(f"PDF already exists: {output_path}")
            # Update library index with path if available
            if result and self._library_index:
                citation_key = filename.replace('.pdf', '')
                self._library_index.update_pdf_path(citation_key, str(output_path))
            return output_path

        # Build list of URLs to try (primary + transformed + Unpaywall fallback)
        urls_to_try: List[str] = []
        attempted_urls: List[str] = []
        last_error: Optional[Exception] = None
        last_failure_reason: Optional[str] = None

        # Handle case where no primary URL is provided
        if url is None:
            logger.debug("No primary URL provided, using fallback strategies only")
        else:
            # Add transformed URLs (multiple candidates for PMC, etc.)
            transformed_urls = _transform_pdf_url(url)

            # For URLs that look like abstract pages, prioritize transformed versions
            if transformed_urls and ('abs' in url.lower() or 'abstract' in url.lower()):
                # For abstract URLs, try transformed versions first
                urls_to_try.extend(transformed_urls)
                if url not in urls_to_try:
                    urls_to_try.append(url)  # Add original as fallback
                logger.debug(f"Prioritizing transformed URLs for abstract URL: {url}")
            else:
                # For direct PDF URLs or unknown patterns, try original first
                urls_to_try.append(url)
                for transformed_url in transformed_urls:
                    if transformed_url not in urls_to_try:
                        logger.debug(f"Adding transformed PDF URL: {transformed_url}")
                        urls_to_try.append(transformed_url)

        # Add DOI-based PDF URLs if DOI is available
        if result and result.doi:
            doi_urls = _doi_to_pdf_urls(result.doi)
            for doi_url in doi_urls:
                if doi_url not in urls_to_try:
                    logger.debug(f"Adding DOI-based PDF URL: {doi_url}")
                    urls_to_try.append(doi_url)

        # Add Unpaywall fallback if configured and DOI available
        if self._unpaywall and result and result.doi:
            unpaywall_url = self._unpaywall.get_pdf_url(result.doi)
            if unpaywall_url and unpaywall_url not in urls_to_try:
                logger.debug(f"Adding Unpaywall fallback URL: {unpaywall_url}")
                urls_to_try.append(unpaywall_url)

        # Try each URL with enhanced retry logic including 403 error recovery
        primary_urls_failed = False
        if urls_to_try:
            for try_url in urls_to_try:
                download_result = self._download_with_enhanced_retry(try_url, output_path)
                attempted_urls.extend(download_result[3])  # Add all attempted URLs

                if download_result[0]:  # Success
                    # Log file size and location
                    try:
                        file_size = output_path.stat().st_size
                        logger.info(f"Downloaded: {filename} ({file_size:,} bytes) -> {output_path}")
                    except Exception as e:
                        logger.warning(f"Could not get file size for {output_path}: {e}")

                    # Update library index with path
                    if result and self._library_index:
                        citation_key = filename.replace('.pdf', '')
                        self._library_index.update_pdf_path(citation_key, str(output_path))
                    return output_path
                else:
                    last_error = download_result[1]
                    last_failure_reason = download_result[2]
                    logger.debug(f"Download failed from {try_url}: {last_failure_reason}")
                    primary_urls_failed = True
        else:
            # No primary URLs provided, go directly to fallbacks
            primary_urls_failed = True
            logger.debug("No primary URLs provided, attempting fallback strategies")

        # Primary URLs failed or none provided - try preprint server fallbacks
        # These are more expensive (require API calls), so only used after URL-based attempts fail
        
        # Fallback 4: arXiv title search
        if result and result.title:
            arxiv_result = self._get_arxiv_fallback(result)
            if arxiv_result:
                attempted_urls.append(f"arXiv title search: {arxiv_result}")
                download_result = self._download_with_enhanced_retry(arxiv_result, output_path)
                attempted_urls.extend(download_result[3])
                
                if download_result[0]:
                    try:
                        file_size = output_path.stat().st_size
                        logger.info(f"Downloaded via arXiv fallback: {filename} ({file_size:,} bytes)")
                    except Exception:
                        pass
                    
                    if result and self._library_index:
                        citation_key = filename.replace('.pdf', '')
                        self._library_index.update_pdf_path(citation_key, str(output_path))
                    return output_path
                else:
                    last_error = download_result[1]
                    last_failure_reason = download_result[2]
        
        # Fallback 5: bioRxiv/medRxiv DOI lookup
        if result and result.doi:
            biorxiv_result = self._get_biorxiv_fallback(result)
            if biorxiv_result:
                attempted_urls.append(f"bioRxiv/medRxiv DOI lookup: {biorxiv_result}")
                download_result = self._download_with_enhanced_retry(biorxiv_result, output_path)
                attempted_urls.extend(download_result[3])
                
                if download_result[0]:
                    try:
                        file_size = output_path.stat().st_size
                        logger.info(f"Downloaded via bioRxiv fallback: {filename} ({file_size:,} bytes)")
                    except Exception:
                        pass
                    
                    if result and self._library_index:
                        citation_key = filename.replace('.pdf', '')
                        self._library_index.update_pdf_path(citation_key, str(output_path))
                    return output_path
                else:
                    last_error = download_result[1]
                    last_failure_reason = download_result[2]

        # All attempts failed
        error_msg = f"Failed to download PDF after trying {len(urls_to_try)} URL(s) plus fallbacks"
        if last_error:
            error_msg = f"{error_msg}: {last_error}"

        raise LiteratureSearchError(
            error_msg,
            context={
                "attempted_urls": attempted_urls,
                "output_path": str(output_path),
                "failure_reason": last_failure_reason
            }
        )
    
    def _get_arxiv_fallback(self, result: SearchResult) -> Optional[str]:
        """Try to find an arXiv preprint version by title search.

        Args:
            result: SearchResult with title to search for.

        Returns:
            PDF URL if arXiv preprint found, else None.
        """
        if not result.title:
            return None

        try:
            logger.debug(f"Trying arXiv fallback for: {result.title[:50]}...")
            arxiv_match = self._arxiv.search_by_title(result.title)

            if arxiv_match:
                # Use pdf_url if available, otherwise transform the abstract URL
                if arxiv_match.pdf_url:
                    logger.info(f"Found arXiv preprint with PDF URL: {arxiv_match.url}")
                    return arxiv_match.pdf_url
                else:
                    # Transform abstract URL to PDF URL
                    transformed_urls = _transform_pdf_url(arxiv_match.url)
                    if transformed_urls:
                        logger.info(f"Found arXiv preprint, transformed to PDF URL: {arxiv_match.url} -> {transformed_urls[0]}")
                        return transformed_urls[0]

            return None
        except Exception as e:
            logger.debug(f"arXiv fallback failed: {e}")
            return None
    
    def _get_biorxiv_fallback(self, result: SearchResult) -> Optional[str]:
        """Try to find a bioRxiv/medRxiv preprint version by DOI.
        
        Args:
            result: SearchResult with DOI to look up.
            
        Returns:
            PDF URL if preprint found, else None.
        """
        if not result.doi:
            return None
        
        try:
            logger.debug(f"Trying bioRxiv/medRxiv fallback for DOI: {result.doi}")
            biorxiv_match = self._biorxiv.search_by_doi(result.doi)
            
            if biorxiv_match and biorxiv_match.pdf_url:
                logger.info(f"Found bioRxiv/medRxiv preprint: {biorxiv_match.url}")
                return biorxiv_match.pdf_url
            
            # Also try title search as fallback
            if result.title:
                biorxiv_match = self._biorxiv.search_by_title(result.title)
                if biorxiv_match and biorxiv_match.pdf_url:
                    logger.info(f"Found bioRxiv/medRxiv preprint by title: {biorxiv_match.url}")
                    return biorxiv_match.pdf_url
            
            return None
        except Exception as e:
            logger.debug(f"bioRxiv/medRxiv fallback failed: {e}")
            return None
    
    def _download_with_enhanced_retry(
        self,
        url: str,
        output_path: Path
    ) -> Tuple[bool, Optional[Exception], Optional[str], List[str]]:
        """Attempt to download from URL with enhanced retry logic and 403 error recovery.

        Includes multiple fallback strategies for 403 Forbidden errors:
        - Different User-Agents
        - Minimal headers
        - HEAD request first
        - Referer header spoofing

        Args:
            url: URL to download from.
            output_path: Where to save the file.

        Returns:
            Tuple of (success, error, failure_reason, attempted_urls).
        """
        last_error: Optional[Exception] = None
        last_failure_reason: Optional[str] = None
        attempted_urls: List[str] = []

        # Try standard download first
        result = self._download_single_attempt(url, output_path, attempt_type="standard")
        attempted_urls.append(url)

        if result[0]:  # Success
            return (True, None, None, attempted_urls)

        last_error = result[1]
        last_failure_reason = result[2]

        # If HTML received or access denied, try fallback strategies
        if last_failure_reason in ["html_response", "html_no_pdf_link", "access_denied"]:
            if last_failure_reason == "access_denied":
                logger.debug(f"403 Forbidden detected, trying enhanced recovery for {url}")
            else:
                logger.debug(f"HTML response detected, trying fallback URLs for {url}")

            # Strategy 0: Try transformed URLs (for HTML responses)
            if last_failure_reason in ["html_response", "html_no_pdf_link"]:
                transformed_urls = _transform_pdf_url(url)
                for i, transformed_url in enumerate(transformed_urls[:3]):  # Try up to 3 transformed URLs
                    logger.debug(f"Trying transformed URL {i+1}: {transformed_url}")
                    result = self._download_single_attempt(
                        transformed_url, output_path, attempt_type=f"transformed_{i+1}"
                    )
                    attempted_urls.append(transformed_url)

                    if result[0]:
                        logger.info(f"Success with transformed URL")
                        return (True, None, None, attempted_urls)

            # Strategy 1: Try different User-Agents
            for user_agent in BROWSER_USER_AGENTS[:3]:  # Try first 3 different User-Agents
                logger.debug(f"Trying with User-Agent: {user_agent[:50]}...")
                result = self._download_single_attempt(
                    url, output_path, attempt_type="user_agent",
                    custom_headers={"User-Agent": user_agent}
                )
                attempted_urls.append(f"{url} (User-Agent: {user_agent[:20]}...)")

                if result[0]:
                    return (True, None, None, attempted_urls)

            # Strategy 2: Try with minimal headers (no Accept-Language, etc.)
            logger.debug(f"Trying minimal headers")
            result = self._download_single_attempt(
                url, output_path, attempt_type="minimal",
                custom_headers={
                    "User-Agent": random.choice(BROWSER_USER_AGENTS),
                    "Accept": "application/pdf,*/*"
                }
            )
            attempted_urls.append(f"{url} (minimal)")

            if result[0]:
                return (True, None, None, attempted_urls)

            # Strategy 3: Try HEAD request first to check if URL is accessible
            try:
                logger.debug(f"Trying HEAD request")
                head_response = requests.head(
                    url,
                    timeout=self.config.timeout,
                    headers={"User-Agent": random.choice(BROWSER_USER_AGENTS)},
                    allow_redirects=True
                )
                if head_response.status_code == 200:
                    # HEAD succeeded, try GET again with same User-Agent
                    result = self._download_single_attempt(
                        url, output_path, attempt_type="head_ok",
                        custom_headers={"User-Agent": head_response.request.headers.get("User-Agent", "")}
                    )
                    attempted_urls.append(f"{url} (head_ok)")

                    if result[0]:
                        return (True, None, None, attempted_urls)
            except Exception as e:
                logger.debug(f"HEAD failed: {e}")

            # Strategy 4: Try with referer spoofing (pretend we're coming from Google)
            logger.debug(f"Trying referer spoofing")
            result = self._download_single_attempt(
                url, output_path, attempt_type="referer",
                custom_headers={
                    "User-Agent": random.choice(BROWSER_USER_AGENTS),
                    "Accept": "application/pdf,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.google.com/"
                }
            )
            attempted_urls.append(f"{url} (referer)")

            if result[0]:
                return (True, None, None, attempted_urls)

            # Strategy 5: Try academic referers (pretend we're coming from university sites)
            academic_referers = [
                "https://scholar.google.com/",
                "https://www.semanticscholar.org/",
                "https://www.researchgate.net/",
                "https://arxiv.org/",
                "https://www.academia.edu/"
            ]

            for referer in academic_referers[:2]:  # Try first 2 academic referers
                logger.debug(f"Trying academic referer: {referer}")
                result = self._download_single_attempt(
                    url, output_path, attempt_type="academic_referer",
                    custom_headers={
                        "User-Agent": random.choice(BROWSER_USER_AGENTS),
                        "Accept": "application/pdf,*/*",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": referer
                    }
                )
                attempted_urls.append(f"{url} (academic_referer: {referer.split('//')[1].split('/')[0]})")

                if result[0]:
                    return (True, None, None, attempted_urls)

            # Strategy 6: Try DOI-based direct access (for some publishers)
            if result and hasattr(result, 'doi') and result.doi:
                doi = result.doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
                doi_urls = _doi_to_pdf_urls(result.doi)  # Use the enhanced DOI function

                for doi_url in doi_urls[:3]:  # Try first 3 DOI-based URLs
                    logger.debug(f"Trying DOI-based URL: {doi_url}")
                    result = self._download_single_attempt(
                        doi_url, output_path, attempt_type="doi_direct"
                    )
                    attempted_urls.append(f"{doi_url} (doi_direct)")

                    if result[0]:
                        return (True, None, None, attempted_urls)

        # If not 403 or all recovery strategies failed, try standard retries
        else:
            # Enhanced retry logic based on failure type
            max_retries = self.config.download_retry_attempts

            for attempt in range(1, max_retries + 1):
                delay = self.config.download_retry_delay * (2 ** (attempt - 1))

                # For 403 errors, try different strategies on retry
                if last_failure_reason == "access_denied":
                    # Try with different user agent on each retry
                    user_agents = BROWSER_USER_AGENTS[attempt-1::3]  # Different agents each time
                    if user_agents:
                        custom_agent = user_agents[0]
                        logger.debug(f"Retry {attempt} with different User-Agent, waiting {delay:.1f}s")
                        time.sleep(delay)

                        result = self._download_single_attempt(
                            url, output_path,
                            attempt_type=f"retry_{attempt}_agent",
                            custom_headers={"User-Agent": custom_agent}
                        )
                        attempted_urls.append(f"{url} (retry {attempt}, agent: {custom_agent[:20]}...)")

                        if result[0]:
                            return (True, None, None, attempted_urls)

                        last_error = result[1]
                        last_failure_reason = result[2]
                        continue

                # For other errors, standard retry
                logger.debug(f"Standard retry attempt {attempt}, waiting {delay:.1f}s")
                time.sleep(delay)

                result = self._download_single_attempt(url, output_path, attempt_type=f"retry_{attempt}")
                attempted_urls.append(f"{url} (retry {attempt})")

                if result[0]:
                    return (True, None, None, attempted_urls)

                last_error = result[1]
                last_failure_reason = result[2]

        return (False, last_error, last_failure_reason, attempted_urls)

    def _download_single_attempt(
        self,
        url: str,
        output_path: Path,
        attempt_type: str = "standard",
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Optional[Exception], Optional[str]]:
        """Single download attempt with specific configuration.

        Args:
            url: URL to download from.
            output_path: Where to save the file.
            attempt_type: Description of this attempt type for logging.
            custom_headers: Custom headers to use instead of defaults.

        Returns:
            Tuple of (success, error, failure_reason).
        """
        try:
            logger.debug(f"Download attempt ({attempt_type}) from {url}")

            # Use custom headers if provided, otherwise default
            headers = custom_headers or {
                "User-Agent": self._get_user_agent(),
                "Accept": "application/pdf,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }

            response = requests.get(
                url,
                stream=True,
                timeout=self.config.timeout,
                headers=headers,
                allow_redirects=True
            )

            # Check for errors
            if response.status_code >= 400:
                failure_reason, _ = self._categorize_error(
                    Exception(f"HTTP {response.status_code}"),
                    response.status_code
                )
                return (False, Exception(f"HTTP {response.status_code}"), failure_reason)

            # Verify we got a PDF (or at least something substantial)
            content_type = response.headers.get("Content-Type", "")
            content_length = response.headers.get("Content-Length")

            # Read first chunk to check for PDF magic bytes and HTML content
            content_sample = response.content[:2048] if hasattr(response, 'content') else b''

            # Enhanced validation: check both content-type header and actual content
            is_html_by_header = "text/html" in content_type.lower()
            is_html_by_content = _is_html_content(content_sample)
            is_pdf_by_content = _is_pdf_content(content_sample)

            # If we got HTML instead of PDF, try to extract PDF URLs from the HTML
            if (is_html_by_header or is_html_by_content) and not is_pdf_by_content:
                logger.debug(f"HTML response from {url}, extracting PDF URLs")

                # Try to extract PDF URLs from the HTML content
                html_pdf_urls = self.parse_html_for_pdf(response.content, url)

                if html_pdf_urls:
                    logger.debug(f"Found {len(html_pdf_urls)} PDF URLs in HTML")

                    # Try each extracted URL (limit to first few to avoid too many attempts)
                    for i, pdf_url in enumerate(html_pdf_urls[:3]):  # Try up to 3 extracted URLs
                        logger.debug(f"Trying HTML PDF URL {i+1}: {pdf_url}")
                        try:
                            # Recursively try the extracted URL (but avoid infinite recursion)
                            if pdf_url != url:  # Don't retry the same URL
                                recursive_result = self._download_single_attempt(
                                    pdf_url, output_path, attempt_type=f"html_{i+1}"
                                )
                                if recursive_result[0]:  # Success
                                    logger.info(f"Downloaded PDF from HTML URL")
                                    return recursive_result
                                else:
                                    logger.debug(f"HTML URL failed: {recursive_result[2]}")
                        except Exception as e:
                            logger.debug(f"HTML URL error: {e}")
                            continue

                    # If we got here, all extracted URLs failed
                    logger.warning(f"HTML page contains no working PDF URLs")
                    return (False, Exception("HTML page contains no working PDF URLs"), "html_no_pdf_link")
                else:
                    logger.warning(f"HTML received instead of PDF")
                    return (False, Exception("HTML received instead of PDF"), "html_response")

            # If content-type suggests PDF but content looks like HTML, also fail
            if not is_html_by_header and is_html_by_content and not is_pdf_by_content:
                logger.warning(f"Content-Type mismatch: HTML received instead of PDF")
                return (False, Exception("Content-Type mismatch: HTML received instead of PDF"), "content_mismatch")

            # Write the file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify file was written and has content
            if not output_path.exists() or output_path.stat().st_size == 0:
                logger.warning(f"Downloaded file is empty: {output_path}")
                if output_path.exists():
                    output_path.unlink()
                return (False, Exception("Downloaded file is empty"), "empty_file")

            # Verify the file actually contains a PDF (check magic bytes)
            try:
                with open(output_path, 'rb') as f:
                    file_header = f.read(4)
                if not _is_pdf_content(file_header):
                    logger.warning(f"Downloaded file is not a PDF (missing %PDF magic bytes): {output_path}")
                    output_path.unlink()
                    return (False, Exception("File is not a valid PDF"), "invalid_response")
            except Exception as e:
                logger.warning(f"Failed to validate downloaded file: {e}")
                if output_path.exists():
                    output_path.unlink()
                return (False, e, "validation_error")

            return (True, None, None)

        except requests.exceptions.HTTPError as e:
            failure_reason, _ = self._categorize_error(e, e.response.status_code if e.response else None)
            return (False, e, failure_reason)
        except requests.exceptions.Timeout as e:
            return (False, e, "timeout")
        except requests.exceptions.RequestException as e:
            failure_reason, _ = self._categorize_error(e)
            return (False, e, failure_reason)
        except OSError as e:
            error = FileOperationError(
                f"Failed to write PDF file: {e}",
                context={"path": str(output_path)}
            )
            return (False, error, "file_error")

    def _generate_filename_from_result(self, result: SearchResult) -> str:
        """Generate filename from search result using citation key format.
        
        Args:
            result: Search result.
            
        Returns:
            Filename string with .pdf extension.
        """
        # Get first author's last name
        if result.authors:
            first_author = result.authors[0]
            parts = first_author.replace(",", " ").split()
            author = parts[-1].lower() if parts else "anonymous"
        else:
            author = "anonymous"
        
        # Sanitize
        author = "".join(c for c in author if c.isalnum())
        
        year = str(result.year) if result.year else "nodate"
        
        # First significant word from title
        title_words = result.title.lower().split()
        skip_words = {"a", "an", "the", "on", "in", "of", "for", "to", "and", "with"}
        title_word = "paper"
        for word in title_words:
            clean_word = "".join(c for c in word if c.isalnum())
            if clean_word and clean_word not in skip_words:
                title_word = clean_word
                break
        
        return f"{author}{year}{title_word}.pdf"

    def download_paper(self, result: SearchResult) -> Optional[Path]:
        """Download PDF for a search result.
        
        Convenience method that extracts pdf_url from result.
        
        Args:
            result: Search result with pdf_url.
            
        Returns:
            Path to downloaded file, or None if no PDF URL.
        """
        if not result.pdf_url:
            logger.warning(f"No PDF URL for paper: {result.title}")
            return None
        
        return self.download_pdf(result.pdf_url, result=result)

    def extract_citations(self, pdf_path: Path) -> list[str]:
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
