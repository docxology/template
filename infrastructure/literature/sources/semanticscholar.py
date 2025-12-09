"""Semantic Scholar API client for literature search.

Provides access to Semantic Scholar's comprehensive academic database with:
- Keyword search with filtering
- Citation counts and venue information
- Open access PDF links
- Retry logic with exponential backoff
"""
from __future__ import annotations

import time
import requests
from typing import List, Dict, Any

from infrastructure.core.exceptions import APIRateLimitError, LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult

logger = get_logger(__name__)


class SemanticScholarSource(LiteratureSource):
    """Client for Semantic Scholar API with retry logic."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search Semantic Scholar with retry on rate limit.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            LiteratureSearchError: If API request fails.
        """
        logger.info(f"Searching Semantic Scholar for: {query}")
        
        headers = {"User-Agent": self.config.user_agent}
        if self.config.semanticscholar_api_key:
            headers["x-api-key"] = self.config.semanticscholar_api_key

        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,abstract,url,externalIds,venue,citationCount,isOpenAccess,openAccessPdf"
        }
        
        last_error = None
        for attempt in range(self.config.retry_attempts):
            try:
                # Rate limiting delay before request
                delay = self.config.semanticscholar_delay * (2 ** attempt)  # Exponential backoff
                if attempt > 0:
                    logger.debug(f"Retry attempt {attempt + 1}, waiting {delay:.1f}s")
                time.sleep(delay)
                
                response = requests.get(
                    self.BASE_URL, 
                    params=params, 
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 429:
                    # Remove exponential backoff delay - allow immediate retry
                    logger.warning(f"Rate limited, retrying immediately...")
                    last_error = APIRateLimitError("Semantic Scholar rate limit exceeded")
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                results = self._parse_response(data)
                logger.debug(f"Semantic Scholar returned {len(results)} results")
                return results
                
            except requests.exceptions.RequestException as e:
                last_error = LiteratureSearchError(
                    f"Semantic Scholar API request failed: {e}", 
                    context={"source": "semanticscholar", "attempt": attempt + 1}
                )
                if attempt < self.config.retry_attempts - 1:
                    logger.warning(f"Request failed, will retry: {e}")
                continue
        
        # All retries exhausted
        if last_error:
            raise last_error
        raise LiteratureSearchError("Semantic Scholar search failed after all retries")

    def _parse_response(self, data: Dict[str, Any]) -> List[SearchResult]:
        results = []
        if 'data' not in data:
            return results

        for paper in data['data']:
            authors = [a['name'] for a in paper.get('authors', [])]
            external_ids = paper.get('externalIds', {})
            doi = external_ids.get('DOI')
            
            pdf_url = None
            if paper.get('isOpenAccess') and paper.get('openAccessPdf'):
                pdf_url = paper['openAccessPdf'].get('url')

            results.append(SearchResult(
                title=paper.get('title', ''),
                authors=authors,
                year=paper.get('year'),
                abstract=paper.get('abstract') or "",
                url=paper.get('url', ''),
                doi=doi,
                source="semanticscholar",
                pdf_url=pdf_url,
                venue=paper.get('venue'),
                citation_count=paper.get('citationCount')
            ))
            
        return results

