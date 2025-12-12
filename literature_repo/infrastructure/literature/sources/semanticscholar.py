"""Semantic Scholar API client for literature search.

Provides access to Semantic Scholar's comprehensive academic database with:
- Keyword search with filtering
- Citation counts and venue information
- Open access PDF links
- Standardized retry logic with exponential backoff
"""
from __future__ import annotations

import requests
from typing import List, Dict, Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult

logger = get_logger(__name__)


class SemanticScholarSource(LiteratureSource):
    """Client for Semantic Scholar API with retry logic."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search Semantic Scholar with retry on rate limit.
        
        Uses the standardized retry logic from the base class for consistent
        error handling and rate limit management.
        
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
        
        def _execute_search():
            response = requests.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            results = self._parse_response(data)
            return results
        
        # Use common retry logic from base class
        results = self._execute_with_retry(
            _execute_search,
            "search",
            "semanticscholar",
            handle_rate_limit=True
        )
        
        # Log detailed statistics
        citations_total = sum(r.citation_count or 0 for r in results)
        pdfs_count = sum(1 for r in results if r.pdf_url)
        dois_count = sum(1 for r in results if r.doi)
        logger.debug(f"Semantic Scholar search completed: {len(results)} results, "
                    f"{citations_total} total citations, {pdfs_count} with PDFs, {dois_count} with DOIs")
        
        return results

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

