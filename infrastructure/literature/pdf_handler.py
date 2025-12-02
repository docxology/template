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
from infrastructure.literature.api import SearchResult, UnpaywallSource

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


def _transform_pdf_url(url: str) -> str:
    """Transform HTML landing pages to direct PDF URLs for known sources.

    Args:
        url: Original URL that might be an HTML landing page.

    Returns:
        Transformed URL pointing to PDF, or original URL if no transformation applies.
    """
    import re

    # PMC articles: convert HTML article page to PDF
    # Example: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/
    # -> https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/pdf/
    pmc_match = re.search(r'www\.ncbi\.nlm\.nih\.gov/pmc/articles/(PMC[^/]+)/?', url)
    if pmc_match:
        pmc_id = pmc_match.group(1)
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"

    # DOI.org redirects often go to HTML landing pages
    # For now, just return the original - we'll handle redirects in the download logic

    return url


class PDFHandler:
    """Handles PDF downloading and text extraction.
    
    Downloads PDFs using citation keys as filenames for consistency
    with the BibTeX and library index. Supports retry logic, User-Agent
    rotation, and Unpaywall fallback for failed downloads.
    """

    def __init__(self, config: LiteratureConfig, library_index: Optional["LibraryIndex"] = None):
        """Initialize PDF handler.
        
        Args:
            config: Literature configuration.
            library_index: Optional LibraryIndex for citation key generation and tracking.
        """
        self.config = config
        self._library_index = library_index
        self._unpaywall: Optional[UnpaywallSource] = None
        if config.use_unpaywall and config.unpaywall_email:
            self._unpaywall = UnpaywallSource(config)
        self._ensure_download_dir()

    def set_library_index(self, library_index: "LibraryIndex") -> None:
        """Set the library index for coordinated operations.
        
        Args:
            library_index: LibraryIndex instance to use.
        """
        self._library_index = library_index

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
        
        if status_code == 403:
            return ("access_denied", f"403 Forbidden: {error_str}")
        elif status_code == 404:
            return ("not_found", f"404 Not Found: {error_str}")
        elif status_code == 429:
            return ("rate_limited", f"429 Too Many Requests: {error_str}")
        elif "timeout" in error_str.lower() or isinstance(error, requests.exceptions.Timeout):
            return ("timeout", f"Request timed out: {error_str}")
        elif isinstance(error, requests.exceptions.ConnectionError):
            return ("network_error", f"Connection error: {error_str}")
        elif isinstance(error, requests.exceptions.RequestException):
            return ("network_error", f"Request failed: {error_str}")
        else:
            return ("unknown", error_str)

    def download_pdf(
        self,
        url: str,
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
        urls_to_try: List[str] = [url]
        attempted_urls: List[str] = []
        last_error: Optional[Exception] = None
        last_failure_reason: Optional[str] = None

        # Add transformed URL if different from original
        transformed_url = _transform_pdf_url(url)
        if transformed_url != url:
            logger.debug(f"Adding transformed PDF URL: {transformed_url}")
            urls_to_try.append(transformed_url)

        # Add Unpaywall fallback if configured and DOI available
        if self._unpaywall and result and result.doi:
            unpaywall_url = self._unpaywall.get_pdf_url(result.doi)
            if unpaywall_url and unpaywall_url not in urls_to_try:
                logger.debug(f"Adding Unpaywall fallback URL: {unpaywall_url}")
                urls_to_try.append(unpaywall_url)

        # Try each URL with enhanced retry logic including 403 error recovery
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

        # All attempts failed
        error_msg = f"Failed to download PDF after trying {len(urls_to_try)} URL(s)"
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

        # If 403 Forbidden, try enhanced recovery strategies
        if last_failure_reason == "access_denied":
            logger.debug(f"403 Forbidden detected, trying enhanced recovery for {url}")

            # Strategy 1: Try different User-Agents
            for user_agent in BROWSER_USER_AGENTS[:3]:  # Try first 3 different User-Agents
                logger.debug(f"Trying with User-Agent: {user_agent[:50]}...")
                result = self._download_single_attempt(
                    url, output_path, attempt_type="user_agent",
                    custom_headers={"User-Agent": user_agent}
                )
                attempted_urls.append(f"{url} (User-Agent: {user_agent[:20]}...)")

                if result[0]:
                    logger.info(f"Success with alternative User-Agent")
                    return (True, None, None, attempted_urls)

            # Strategy 2: Try with minimal headers (no Accept-Language, etc.)
            logger.debug(f"Trying with minimal headers...")
            result = self._download_single_attempt(
                url, output_path, attempt_type="minimal_headers",
                custom_headers={
                    "User-Agent": random.choice(BROWSER_USER_AGENTS),
                    "Accept": "application/pdf,*/*"
                }
            )
            attempted_urls.append(f"{url} (minimal headers)")

            if result[0]:
                logger.info(f"Success with minimal headers")
                return (True, None, None, attempted_urls)

            # Strategy 3: Try HEAD request first to check if URL is accessible
            try:
                logger.debug(f"Trying HEAD request first...")
                head_response = requests.head(
                    url,
                    timeout=self.config.timeout,
                    headers={"User-Agent": random.choice(BROWSER_USER_AGENTS)},
                    allow_redirects=True
                )
                if head_response.status_code == 200:
                    # HEAD succeeded, try GET again with same User-Agent
                    result = self._download_single_attempt(
                        url, output_path, attempt_type="head_success",
                        custom_headers={"User-Agent": head_response.request.headers.get("User-Agent", "")}
                    )
                    attempted_urls.append(f"{url} (after HEAD success)")

                    if result[0]:
                        logger.info(f"Success after HEAD request")
                        return (True, None, None, attempted_urls)
            except Exception as e:
                logger.debug(f"HEAD request failed: {e}")

            # Strategy 4: Try with referer spoofing (pretend we're coming from Google)
            logger.debug(f"Trying with referer spoofing...")
            result = self._download_single_attempt(
                url, output_path, attempt_type="referer_spoof",
                custom_headers={
                    "User-Agent": random.choice(BROWSER_USER_AGENTS),
                    "Accept": "application/pdf,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.google.com/"
                }
            )
            attempted_urls.append(f"{url} (referer spoof)")

            if result[0]:
                logger.info(f"Success with referer spoofing")
                return (True, None, None, attempted_urls)

        # If not 403 or all recovery strategies failed, try standard retries
        else:
            # Standard retry logic for other error types
            for attempt in range(1, self.config.download_retry_attempts + 1):
                delay = self.config.download_retry_delay * (2 ** (attempt - 1))
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

            # If we clearly got HTML instead of PDF, fail immediately
            if (is_html_by_header or is_html_by_content) and not is_pdf_by_content:
                logger.warning(f"Received HTML instead of PDF from {url} ({attempt_type})")
                logger.debug(f"Content-Type: {content_type}, HTML detected: {is_html_by_content}, PDF detected: {is_pdf_by_content}")
                return (False, Exception("Received HTML instead of PDF"), "invalid_response")

            # If content-type suggests PDF but content looks like HTML, also fail
            if not is_html_by_header and is_html_by_content and not is_pdf_by_content:
                logger.warning(f"Content-Type claims PDF but received HTML from {url} ({attempt_type})")
                return (False, Exception("Content-Type mismatch: HTML received instead of PDF"), "invalid_response")

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
