"""DBLP API client for computer science literature search.

Provides access to DBLP (Digital Bibliography & Library Project) with:
- XML/JSON API for computer science papers
- Author and venue information
- Comprehensive metadata
"""
from __future__ import annotations

import requests
from typing import List, Dict, Any, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult

logger = get_logger(__name__)


class DBLPSource(LiteratureSource):
    """Client for DBLP API with retry logic."""

    BASE_URL = "https://dblp.org/search/publ/api"

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search DBLP with retry logic.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            LiteratureSearchError: If API request fails after all retries.
        """
        logger.info(f"Searching DBLP for: {query}")
        
        params = {
            "q": query,
            "h": limit,
            "format": "json"
        }
        
        def _execute_search():
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.config.timeout,
                headers={"User-Agent": self.config.user_agent}
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        
        # Use common retry logic from base class
        results = self._execute_with_retry(
            _execute_search,
            "search",
            "dblp",
            handle_rate_limit=True
        )
        
        # Log detailed statistics
        pdfs_count = sum(1 for r in results if r.pdf_url)
        dois_count = sum(1 for r in results if r.doi)
        logger.debug(f"DBLP search completed: {len(results)} results, {pdfs_count} with PDFs, {dois_count} with DOIs")
        
        return results

    def _parse_response(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse DBLP API response.
        
        Args:
            data: JSON response from DBLP API.
            
        Returns:
            List of SearchResult objects.
        """
        results = []
        
        if 'result' not in data or 'hits' not in data['result'] or 'hit' not in data['result']['hits']:
            return results
        
        hits = data['result']['hits']['hit']
        # Handle single result (not a list)
        if not isinstance(hits, list):
            hits = [hits]
        
        for hit in hits:
            info = hit.get('info', {})
            
            # Title
            title = info.get('title', '')
            
            # Authors
            authors = []
            if 'authors' in info and 'author' in info['authors']:
                author_list = info['authors']['author']
                # Handle single author (not a list)
                if not isinstance(author_list, list):
                    author_list = [author_list]
                authors = [str(a) for a in author_list]
            
            # Year
            year = None
            if 'year' in info and info['year']:
                try:
                    year = int(info['year'])
                except (ValueError, TypeError):
                    pass
            
            # DOI
            doi = None
            if 'doi' in info and info['doi']:
                doi = info['doi']
                # Ensure DOI format
                if not doi.startswith('10.'):
                    doi = None
            
            # Abstract (DBLP doesn't provide abstracts)
            abstract = ""
            
            # URL
            url = info.get('ee', '')
            if not url and 'url' in info:
                url = info['url']
            
            # PDF URL (from ee field if it's a PDF)
            pdf_url = None
            if 'ee' in info:
                ee_url = info['ee']
                if isinstance(ee_url, list):
                    # Find PDF URL
                    for url_item in ee_url:
                        if isinstance(url_item, str) and url_item.endswith('.pdf'):
                            pdf_url = url_item
                            break
                    # If no PDF found, use first URL
                    if not pdf_url and ee_url:
                        pdf_url = ee_url[0]
                elif isinstance(ee_url, str):
                    if ee_url.endswith('.pdf'):
                        pdf_url = ee_url
                    else:
                        # Try to construct PDF URL (some venues provide PDFs at same path)
                        pdf_url = ee_url
            
            # Venue
            venue = None
            if 'venue' in info:
                venue = info['venue']
            elif 'journal' in info:
                venue = info['journal']
            elif 'booktitle' in info:
                venue = info['booktitle']
            
            results.append(SearchResult(
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                url=url,
                doi=doi,
                source="dblp",
                pdf_url=pdf_url,
                venue=venue
            ))
        
        return results

