"""Base classes and utilities for literature sources.

This module provides:
- SearchResult: Normalized search result dataclass
- LiteratureSource: Abstract base class for all sources
- Utility functions for title normalization and similarity
- Common retry logic and error handling
"""
from __future__ import annotations

import abc
import re
import time
from typing import List, Optional, Callable, TypeVar, Any, Dict
from dataclasses import dataclass

import requests

from infrastructure.core.exceptions import APIRateLimitError, LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.core.config import LiteratureConfig

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class SearchResult:
    """Normalized search result."""
    title: str
    authors: List[str]
    year: Optional[int]
    abstract: str
    url: str
    doi: Optional[str] = None
    source: str = "unknown"
    pdf_url: Optional[str] = None
    venue: Optional[str] = None
    citation_count: Optional[int] = None


class LiteratureSource(abc.ABC):
    """Abstract base class for literature sources.
    
    Provides common functionality for all literature sources:
    - Standardized retry logic with exponential backoff
    - Rate limit handling
    - Error handling and logging
    - Health checks
    """

    def __init__(self, config: LiteratureConfig):
        self.config = config
        self._last_request_time: float = 0.0
        self._consecutive_failures: int = 0

    @abc.abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search for papers."""
        pass

    def _execute_with_retry(
        self,
        operation: Callable[[], T],
        operation_name: str,
        source_name: str,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        handle_rate_limit: bool = True
    ) -> T:
        """Execute an operation with retry logic and exponential backoff.
        
        Args:
            operation: Function to execute (should raise exceptions on failure).
            operation_name: Name of operation for logging (e.g., "search", "download").
            source_name: Name of source for error context.
            max_retries: Maximum retry attempts (default: config.retry_attempts).
            base_delay: Base delay for exponential backoff (default: config.retry_delay).
            handle_rate_limit: Whether to handle 429 rate limit errors specially.
            
        Returns:
            Result of the operation.
            
        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            LiteratureSearchError: If operation fails after all retries.
        """
        max_retries = max_retries or self.config.retry_attempts
        base_delay = base_delay or self.config.retry_delay
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Apply rate limiting delay
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.debug(f"{source_name} {operation_name} retry {attempt + 1}/{max_retries}, waiting {delay:.1f}s")
                    time.sleep(delay)
                else:
                    # First attempt - use source-specific delay if configured
                    source_delay = getattr(self.config, f"{source_name}_delay", None)
                    if source_delay:
                        elapsed = time.time() - self._last_request_time
                        if elapsed < source_delay:
                            time.sleep(source_delay - elapsed)
                    self._last_request_time = time.time()
                
                # Execute operation
                result = operation()
                
                # Reset failure counter on success
                self._consecutive_failures = 0
                return result
                
            except requests.exceptions.HTTPError as e:
                # Handle rate limit errors specially
                if handle_rate_limit and e.response and e.response.status_code == 429:
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = float(retry_after)
                            logger.warning(f"{source_name} rate limited, waiting {wait_time}s (Retry-After header)")
                            time.sleep(wait_time)
                            continue
                        except ValueError:
                            pass
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"{source_name} rate limited, retrying immediately...")
                        last_error = APIRateLimitError(
                            f"{source_name} rate limit exceeded",
                            context={"source": source_name, "attempt": attempt + 1}
                        )
                        continue
                    else:
                        raise APIRateLimitError(
                            f"{source_name} rate limit exceeded after {max_retries} attempts",
                            context={"source": source_name}
                        )
                
                # Other HTTP errors
                last_error = LiteratureSearchError(
                    f"{source_name} {operation_name} failed: HTTP {e.response.status_code if e.response else 'unknown'}",
                    context={"source": source_name, "attempt": attempt + 1, "status_code": e.response.status_code if e.response else None}
                )
                if attempt < max_retries - 1:
                    logger.warning(f"{source_name} {operation_name} failed, will retry: {e}")
                continue
                
            except requests.exceptions.RequestException as e:
                last_error = LiteratureSearchError(
                    f"{source_name} {operation_name} failed: {e}",
                    context={"source": source_name, "attempt": attempt + 1, "error_type": type(e).__name__}
                )
                if attempt < max_retries - 1:
                    logger.warning(f"{source_name} {operation_name} failed, will retry: {e}")
                continue
                
            except Exception as e:
                last_error = LiteratureSearchError(
                    f"{source_name} {operation_name} failed: {e}",
                    context={"source": source_name, "attempt": attempt + 1, "error_type": type(e).__name__}
                )
                if attempt < max_retries - 1:
                    logger.warning(f"{source_name} {operation_name} failed, will retry: {e}")
                continue
        
        # All retries exhausted
        self._consecutive_failures += 1
        if last_error:
            raise last_error
        raise LiteratureSearchError(
            f"{source_name} {operation_name} failed after {max_retries} attempts",
            context={"source": source_name}
        )

    def check_health(self) -> bool:
        """Check if the source is available and healthy.
        
        Performs a simple health check to verify the source API is accessible.
        Subclasses can override this for source-specific health checks.
        
        Returns:
            True if source is healthy, False otherwise.
        """
        try:
            # Simple health check - try a minimal search
            results = self.search("test", limit=1)
            self._consecutive_failures = 0  # Reset on success
            return True
        except Exception as e:
            logger.debug(f"Health check failed for {self.__class__.__name__}: {e}")
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
        """Get detailed health status for the source.
        
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


def normalize_title(title: str) -> str:
    """Normalize a title for comparison.
    
    Removes punctuation, extra whitespace, and converts to lowercase.
    
    Args:
        title: Title string to normalize.
        
    Returns:
        Normalized title string.
    """
    # Remove punctuation and extra whitespace, convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = ' '.join(normalized.split())
    return normalized


def title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles using word overlap.
    
    Uses Jaccard similarity on word sets after normalization.
    
    Args:
        title1: First title.
        title2: Second title.
        
    Returns:
        Similarity score between 0.0 and 1.0.
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    # Split into words
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    # Handle empty sets
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

