"""Unpaywall API client for open access PDF resolution.

Provides access to Unpaywall's database of legal open access papers with:
- DOI-based lookup
- OA status information
- PDF URL resolution
- Retry logic with rate limiting
"""
from __future__ import annotations

import time
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass

from infrastructure.core.exceptions import APIRateLimitError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.core.config import LiteratureConfig

logger = get_logger(__name__)


@dataclass
class UnpaywallResult:
    """Result from Unpaywall API lookup."""
    doi: str
    is_oa: bool
    pdf_url: Optional[str] = None
    oa_status: Optional[str] = None  # "gold", "hybrid", "bronze", "green", "closed"
    host_type: Optional[str] = None  # "publisher", "repository"
    version: Optional[str] = None  # "publishedVersion", "acceptedVersion", etc.
    license: Optional[str] = None


class UnpaywallSource:
    """Client for Unpaywall API to find open access PDFs.

    Unpaywall provides a database of legal, open access versions of papers.
    It requires an email address for API access (no key needed).

    This is a lookup-only source (no search method). It provides:
    - DOI-based lookup for open access PDFs
    - Health status monitoring via check_health() and get_health_status()
    - Automatic failure tracking for health monitoring

    API Documentation: https://unpaywall.org/products/api

    Rate Limits:
    - 100,000 requests per day for registered emails
    - 50 requests per day for non-registered emails
    - Includes retry logic with exponential backoff

    Health Checks:
    - check_health(): Performs a test lookup to verify API availability
    - is_healthy: Property indicating health based on recent failures
    - get_health_status(): Returns detailed health status information
    """

    BASE_URL = "https://api.unpaywall.org/v2"
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 2.0

    def __init__(self, config: LiteratureConfig):
        """Initialize Unpaywall source.

        Args:
            config: Literature configuration with unpaywall_email.
        """
        self.config = config
        self._last_request_time = 0.0
        self._min_delay = 0.1  # Minimum delay between requests (10 requests/second max)
        self._consecutive_failures = 0  # Track consecutive failures for health monitoring

        if not config.unpaywall_email:
            logger.warning("Unpaywall email not configured - API calls will fail")
        elif not self._validate_email(config.unpaywall_email):
            logger.warning(f"Unpaywall email format appears invalid: {config.unpaywall_email}")
        else:
            logger.debug(f"Unpaywall initialized with email: {config.unpaywall_email}")

    def _validate_email(self, email: str) -> bool:
        """Basic email validation.

        Args:
            email: Email address to validate.

        Returns:
            True if email format is valid.
        """
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    def _rate_limit_delay(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            delay = self._min_delay - elapsed
            logger.debug(f"Unpaywall rate limiting: waiting {delay:.2f}s")
            time.sleep(delay)
        self._last_request_time = time.time()

    def get_pdf_url(self, doi: str) -> Optional[str]:
        """Get open access PDF URL for a DOI.
        
        Args:
            doi: The DOI to look up (e.g., "10.1038/nature12373").
            
        Returns:
            URL to open access PDF, or None if not available.
        """
        result = self.lookup(doi)
        return result.pdf_url if result else None

    def lookup(self, doi: str) -> Optional[UnpaywallResult]:
        """Look up a DOI in Unpaywall with retry logic and rate limiting.

        Args:
            doi: The DOI to look up.

        Returns:
            UnpaywallResult with OA information, or None on failure.
        """
        if not self.config.unpaywall_email:
            logger.warning("Cannot query Unpaywall: email not configured")
            return None

        if not self._validate_email(self.config.unpaywall_email):
            logger.warning(f"Skipping Unpaywall lookup: invalid email format: {self.config.unpaywall_email}")
            return None

        # Clean DOI (remove URL prefix if present)
        clean_doi = doi
        if doi.startswith("https://doi.org/"):
            clean_doi = doi[16:]
        elif doi.startswith("http://doi.org/"):
            clean_doi = doi[15:]
        elif doi.startswith("doi:"):
            clean_doi = doi[4:]

        url = f"{self.BASE_URL}/{clean_doi}"
        params = {"email": self.config.unpaywall_email}

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                # Rate limiting
                self._rate_limit_delay()

                # Exponential backoff for retries
                if attempt > 0:
                    delay = self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
                    logger.debug(f"Unpaywall retry attempt {attempt + 1}, waiting {delay:.1f}s")
                    time.sleep(delay)

                logger.debug(f"Querying Unpaywall for DOI: {clean_doi} (attempt {attempt + 1})")
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.config.timeout,
                    headers={"User-Agent": self.config.user_agent}
                )

                if response.status_code == 404:
                    logger.debug(f"DOI not found in Unpaywall: {clean_doi}")
                    return None

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    wait_time = float(retry_after) if retry_after else self.BASE_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Unpaywall rate limited, waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    last_error = APIRateLimitError("Unpaywall rate limit exceeded")
                    continue

                response.raise_for_status()
                data = response.json()

                result = self._parse_response(data)
                logger.debug(f"Unpaywall found OA version for {clean_doi}: {result.is_oa}")
                # Reset failure counter on success
                self._consecutive_failures = 0
                return result

            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Unpaywall timeout for {clean_doi} (attempt {attempt + 1}): {e}")
                if attempt == self.MAX_RETRIES - 1:
                    self._consecutive_failures += 1
                    break
                continue

            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Unpaywall request failed for {clean_doi} (attempt {attempt + 1}): {e}")
                if attempt == self.MAX_RETRIES - 1:
                    self._consecutive_failures += 1
                    break
                continue

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected Unpaywall error for {clean_doi}: {e}")
                self._consecutive_failures += 1
                break

        logger.warning(f"Unpaywall lookup failed for {clean_doi} after {self.MAX_RETRIES} attempts: {last_error}")
        if last_error:
            self._consecutive_failures += 1
        return None

    def _parse_response(self, data: Dict[str, Any]) -> UnpaywallResult:
        """Parse Unpaywall API response.
        
        Args:
            data: JSON response from Unpaywall API.
            
        Returns:
            UnpaywallResult with extracted information.
        """
        is_oa = data.get("is_oa", False)
        pdf_url = None
        oa_status = data.get("oa_status")
        host_type = None
        version = None
        license_info = None
        
        # Get best OA location (prioritize published version)
        best_oa = data.get("best_oa_location")
        if best_oa:
            pdf_url = best_oa.get("url_for_pdf")
            host_type = best_oa.get("host_type")
            version = best_oa.get("version")
            license_info = best_oa.get("license")
        
        # If no PDF URL from best location, check other locations
        if not pdf_url and is_oa:
            oa_locations = data.get("oa_locations", [])
            for loc in oa_locations:
                url = loc.get("url_for_pdf")
                if url:
                    pdf_url = url
                    host_type = loc.get("host_type")
                    version = loc.get("version")
                    license_info = loc.get("license")
                    break
        
        return UnpaywallResult(
            doi=data.get("doi", ""),
            is_oa=is_oa,
            pdf_url=pdf_url,
            oa_status=oa_status,
            host_type=host_type,
            version=version,
            license=license_info
        )

    def check_health(self) -> bool:
        """Check if the Unpaywall API is available and healthy.
        
        Performs a simple health check by attempting a lookup with a known DOI.
        Returns True if the API responds (even if DOI not found), False on network/API errors.
        
        Returns:
            True if source is healthy, False otherwise.
        """
        # Use a well-known DOI for health check (Nature paper)
        test_doi = "10.1038/nature12373"
        
        try:
            # Try a lookup - if we get a response (even None for not found), API is healthy
            result = self.lookup(test_doi)
            # Reset failure counter on successful health check
            self._consecutive_failures = 0
            # Return True if we got any response (even None means API is responding)
            return True
        except Exception as e:
            logger.debug(f"Unpaywall health check failed: {e}")
            self._consecutive_failures += 1
            return False

    @property
    def is_healthy(self) -> bool:
        """Check if source is currently healthy (cached check).
        
        Returns:
            True if source appears healthy based on recent failures.
        """
        return self._consecutive_failures < 3

    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status for the Unpaywall source.
        
        Returns:
            Dictionary with health status information:
            - healthy: bool
            - consecutive_failures: int
            - last_request_time: float (timestamp)
            - source_name: str
        """
        return {
            "healthy": self.is_healthy,
            "consecutive_failures": self._consecutive_failures,
            "last_request_time": self._last_request_time,
            "source_name": self.__class__.__name__
        }

