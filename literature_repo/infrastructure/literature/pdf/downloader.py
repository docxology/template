"""PDF download logic with retry mechanisms and error handling."""
from __future__ import annotations

import os
import random
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import requests

from infrastructure.core.exceptions import FileOperationError, LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.core.config import LiteratureConfig, BROWSER_USER_AGENTS
from infrastructure.literature.sources import SearchResult
from infrastructure.literature.pdf.fallbacks import transform_pdf_url, doi_to_pdf_urls, PDFFallbackStrategies

logger = get_logger(__name__)


def is_pdf_content(content: bytes) -> bool:
    """Check if content is a PDF by examining magic bytes.

    Args:
        content: Raw response content bytes.

    Returns:
        True if content starts with PDF magic bytes.
    """
    return content.startswith(b'%PDF')


def is_html_content(content: bytes) -> bool:
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


class PDFDownloader:
    """Handles PDF downloading with retry logic and error recovery."""
    
    def __init__(self, config: LiteratureConfig):
        """Initialize PDF downloader.
        
        Args:
            config: Literature configuration.
        """
        self.config = config
        self._ensure_download_dir()
    
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
    
    def categorize_error(self, error: Exception, status_code: Optional[int] = None, url: Optional[str] = None) -> Tuple[str, str]:
        """Categorize an error into failure reason and message.

        Args:
            error: The exception that occurred.
            status_code: HTTP status code if available.
            url: Optional URL for context in error messages.

        Returns:
            Tuple of (failure_reason, failure_message).
        """
        error_str = str(error)
        url_context = f" from {url}" if url else ""

        # Check for specific error messages first
        if "Received HTML instead of PDF" in error_str:
            msg = f"HTML received instead of PDF{url_context}: {error_str}"
            if url and "arxiv.org" in url:
                msg += " (Note: arXiv PDFs should always be available - check URL format)"
            return ("html_response", msg)
        elif "no working PDF URLs found in content" in error_str:
            return ("html_no_pdf_link", f"HTML page contains no PDF links{url_context}: {error_str}")
        elif "Content-Type mismatch" in error_str:
            return ("content_mismatch", f"Content-Type header doesn't match actual content{url_context}: {error_str}")

        # Check HTTP status codes
        if status_code == 403:
            msg = f"403 Forbidden{url_context}: {error_str}"
            if url and "arxiv.org" in url:
                msg += " (Unexpected: arXiv PDFs are open access - check URL or network)"
            return ("access_denied", msg)
        elif status_code == 404:
            msg = f"404 Not Found{url_context}: {error_str}"
            if url and "arxiv.org" in url:
                msg += " (Check arXiv ID format - may need version removal)"
            return ("not_found", msg)
        elif status_code == 429:
            return ("rate_limited", f"429 Too Many Requests{url_context}: {error_str}")
        elif status_code == 502:
            return ("server_error", f"502 Bad Gateway{url_context}: {error_str}")
        elif status_code == 503:
            return ("server_error", f"503 Service Unavailable{url_context}: {error_str}")
        elif status_code and status_code >= 500:
            return ("server_error", f"Server error {status_code}{url_context}: {error_str}")

        # Check exception types and messages
        elif "timeout" in error_str.lower() or isinstance(error, requests.exceptions.Timeout):
            msg = f"Request timed out{url_context}: {error_str}"
            if url and "arxiv.org" in url:
                msg += " (Consider increasing timeout for large PDFs)"
            return ("timeout", msg)
        elif isinstance(error, requests.exceptions.ConnectionError):
            return ("network_error", f"Connection error{url_context}: {error_str}")
        elif isinstance(error, requests.exceptions.RequestException):
            return ("network_error", f"Request failed{url_context}: {error_str}")
        elif "redirect" in error_str.lower() and "loop" in error_str.lower():
            return ("redirect_loop", f"Redirect loop detected{url_context}: {error_str}")
        else:
            return ("unknown", f"{error_str}{url_context}")
    
    def download_with_enhanced_retry(
        self,
        url: str,
        output_path: Path,
        parse_html_callback: Optional[Callable[[bytes, str], List[str]]] = None,
        timeout: Optional[float] = None
    ) -> Tuple[bool, Optional[Exception], Optional[str], List[str]]:
        """Attempt to download from URL with enhanced retry logic and 403 error recovery.

        Includes multiple fallback strategies for 403 Forbidden errors:
        - Different User-Agents
        - Minimal headers
        - HEAD request first
        - Referer header spoofing
        - Academic referer spoofing

        Args:
            url: URL to download from.
            output_path: Where to save the file.
            parse_html_callback: Optional callback to parse HTML for PDF URLs.
            timeout: Optional timeout in seconds. If None, uses config timeout.

        Returns:
            Tuple of (success, error, failure_reason, attempted_urls).
        """
        # Determine timeout to use
        if timeout is None:
            timeout = getattr(self.config, 'pdf_download_timeout', self.config.timeout)
        
        logger.debug(f"Downloading from {url} with timeout {timeout}s")
        
        last_error: Optional[Exception] = None
        last_failure_reason: Optional[str] = None
        attempted_urls: List[str] = []

        # Try standard download first
        result = self._download_single_attempt(
            url, output_path, attempt_type="standard", 
            parse_html_callback=parse_html_callback, timeout=timeout
        )
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
                transformed_urls = transform_pdf_url(url)
                for i, transformed_url in enumerate(transformed_urls[:3]):  # Try up to 3 transformed URLs
                    logger.debug(f"Trying transformed URL {i+1}: {transformed_url}")
                    result = self._download_single_attempt(
                        transformed_url, output_path, attempt_type=f"transformed_{i+1}", 
                        parse_html_callback=parse_html_callback, timeout=timeout
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
                    custom_headers={"User-Agent": user_agent},
                    parse_html_callback=parse_html_callback, timeout=timeout
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
                },
                parse_html_callback=parse_html_callback, timeout=timeout
            )
            attempted_urls.append(f"{url} (minimal)")

            if result[0]:
                return (True, None, None, attempted_urls)

            # Strategy 3: Try HEAD request first to check if URL is accessible
            try:
                logger.debug(f"Trying HEAD request")
                head_response = requests.head(
                    url,
                    timeout=timeout,
                    headers={"User-Agent": random.choice(BROWSER_USER_AGENTS)},
                    allow_redirects=True
                )
                if head_response.status_code == 200:
                    # HEAD succeeded, try GET again with same User-Agent
                    result = self._download_single_attempt(
                        url, output_path, attempt_type="head_ok",
                        custom_headers={"User-Agent": head_response.request.headers.get("User-Agent", "")},
                        parse_html_callback=parse_html_callback, timeout=timeout
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
                },
                parse_html_callback=parse_html_callback, timeout=timeout
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
                    },
                    parse_html_callback=parse_html_callback, timeout=timeout
                )
                attempted_urls.append(f"{url} (academic_referer: {referer.split('//')[1].split('/')[0]})")

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
                            custom_headers={"User-Agent": custom_agent},
                            parse_html_callback=parse_html_callback, timeout=timeout
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

                result = self._download_single_attempt(
                    url, output_path, attempt_type=f"retry_{attempt}", 
                    parse_html_callback=parse_html_callback, timeout=timeout
                )
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
        custom_headers: Optional[Dict[str, str]] = None,
        parse_html_callback: Optional[Callable[[bytes, str], List[str]]] = None,
        recursion_depth: int = 0,
        timeout: Optional[float] = None
    ) -> Tuple[bool, Optional[Exception], Optional[str]]:
        """Single download attempt with specific configuration.

        Args:
            url: URL to download from.
            output_path: Where to save the file.
            attempt_type: Description of this attempt type for logging.
            custom_headers: Custom headers to use instead of defaults.
            parse_html_callback: Optional callback to parse HTML for PDF URLs.
            recursion_depth: Current recursion depth for HTML parsing.
            timeout: Optional timeout in seconds. If None, uses config timeout.

        Returns:
            Tuple of (success, error, failure_reason).
        """
        try:
            # Determine timeout to use
            if timeout is None:
                timeout = getattr(self.config, 'pdf_download_timeout', self.config.timeout)
            
            logger.debug(f"Download attempt ({attempt_type}) from {url} (timeout: {timeout}s)")

            # Use custom headers if provided, otherwise default
            headers = custom_headers or {
                "User-Agent": self._get_user_agent(),
                "Accept": "application/pdf,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }

            response = requests.get(
                url,
                stream=True,
                timeout=timeout,
                headers=headers,
                allow_redirects=True
            )

            # Check for errors
            if response.status_code >= 400:
                failure_reason, error_msg = self.categorize_error(
                    Exception(f"HTTP {response.status_code}"),
                    response.status_code,
                    url=url
                )
                return (False, Exception(error_msg), failure_reason)

            # Verify we got a PDF (or at least something substantial)
            content_type = response.headers.get("Content-Type", "")
            content_length = response.headers.get("Content-Length")

            # Read first chunk to check for PDF magic bytes and HTML content
            content_sample = response.content[:2048] if hasattr(response, 'content') else b''

            # Enhanced validation: check both content-type header and actual content
            is_html_by_header = "text/html" in content_type.lower()
            is_html_by_content = is_html_content(content_sample)
            is_pdf_by_content = is_pdf_content(content_sample)

            # If we got HTML instead of PDF, try to extract PDF URLs from the HTML
            if (is_html_by_header or is_html_by_content) and not is_pdf_by_content:
                # Prevent excessive recursion
                MAX_RECURSION_DEPTH = 2
                if recursion_depth >= MAX_RECURSION_DEPTH:
                    logger.debug(f"Max recursion depth ({MAX_RECURSION_DEPTH}) reached, skipping HTML parsing")
                    return (False, Exception("HTML received instead of PDF"), "html_response")
                
                logger.debug(f"HTML response from {url}, extracting PDF URLs (depth={recursion_depth})")

                # Try to extract PDF URLs from the HTML content if callback provided
                if parse_html_callback and recursion_depth < MAX_RECURSION_DEPTH:
                    html_pdf_urls = parse_html_callback(response.content, url)

                    if html_pdf_urls:
                        # Limit attempts to avoid excessive retries
                        max_html_urls = 2 if recursion_depth > 0 else 3
                        urls_to_try = html_pdf_urls[:max_html_urls]
                        logger.debug(f"Found {len(html_pdf_urls)} PDF URLs in HTML, trying {len(urls_to_try)}")

                        # Try each extracted URL
                        for i, pdf_url in enumerate(urls_to_try):
                            logger.debug(f"Trying HTML PDF URL {i+1}/{len(urls_to_try)}: {pdf_url[:60]}...")
                            try:
                                # Recursively try the extracted URL (but avoid infinite recursion)
                                if pdf_url != url:  # Don't retry the same URL
                                    recursive_result = self._download_single_attempt(
                                        pdf_url, output_path, attempt_type=f"html_{i+1}", 
                                        parse_html_callback=parse_html_callback,
                                        recursion_depth=recursion_depth + 1,
                                        timeout=timeout
                                    )
                                    if recursive_result[0]:  # Success
                                        logger.info(f"Downloaded PDF from HTML URL")
                                        return recursive_result
                                    else:
                                        logger.debug(f"HTML URL {i+1} failed: {recursive_result[2]}")
                            except Exception as e:
                                logger.debug(f"HTML URL {i+1} error: {e}")
                                continue

                        # If we got here, all extracted URLs failed
                        # Only log warning at top level (recursion_depth == 0)
                        if recursion_depth == 0:
                            logger.debug(f"HTML page contains no working PDF URLs ({len(urls_to_try)} URLs tried)")
                        return (False, Exception("HTML page contains no working PDF URLs"), "html_no_pdf_link")
                    else:
                        # Only log warning at top level
                        if recursion_depth == 0:
                            logger.debug(f"HTML received instead of PDF (no PDF URLs found in HTML)")
                        return (False, Exception("HTML received instead of PDF"), "html_response")
                else:
                    # Only log warning at top level
                    if recursion_depth == 0:
                        logger.debug(f"HTML received instead of PDF (parser not available or max depth reached)")
                    return (False, Exception("HTML received instead of PDF"), "html_response")

            # If content-type suggests PDF but content looks like HTML, also fail
            if not is_html_by_header and is_html_by_content and not is_pdf_by_content:
                # Only log warning at top level
                if recursion_depth == 0:
                    logger.debug(f"Content-Type mismatch: HTML received instead of PDF")
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
                if not is_pdf_content(file_header):
                    file_size = output_path.stat().st_size if output_path.exists() else 0
                    logger.warning(
                        f"Downloaded file is not a PDF (missing %PDF magic bytes): {output_path} "
                        f"(size: {file_size} bytes, URL: {url})"
                    )
                    output_path.unlink()
                    return (False, Exception(f"File is not a valid PDF (size: {file_size} bytes)"), "invalid_response")
            except Exception as e:
                logger.warning(f"Failed to validate downloaded file: {e} (URL: {url})")
                if output_path.exists():
                    output_path.unlink()
                return (False, e, "validation_error")

            return (True, None, None)

        except requests.exceptions.HTTPError as e:
            failure_reason, error_msg = self.categorize_error(
                e, e.response.status_code if e.response else None, url=url
            )
            return (False, Exception(error_msg), failure_reason)
        except requests.exceptions.Timeout as e:
            failure_reason, error_msg = self.categorize_error(e, url=url)
            return (False, Exception(error_msg), failure_reason)
        except requests.exceptions.RequestException as e:
            failure_reason, error_msg = self.categorize_error(e, url=url)
            return (False, Exception(error_msg), failure_reason)
        except OSError as e:
            error = FileOperationError(
                f"Failed to write PDF file: {e}",
                context={"path": str(output_path)}
            )
            return (False, error, "file_error")

