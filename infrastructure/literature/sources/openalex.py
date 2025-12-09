"""OpenAlex API client for literature search.

Provides access to OpenAlex open access academic database with:
- Free REST API (no key required)
- Comprehensive metadata and PDF links
- Citation counts
- Open access information
"""
from __future__ import annotations

import requests
from typing import List, Dict, Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult

logger = get_logger(__name__)


class OpenAlexSource(LiteratureSource):
    """Client for OpenAlex API with retry logic."""

    BASE_URL = "https://api.openalex.org/works"

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search OpenAlex with retry logic.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            LiteratureSearchError: If API request fails after all retries.
        """
        logger.info(f"Searching OpenAlex for: {query}")
        
        params = {
            "search": query,
            "per_page": limit,
            "sort": "relevance_score:desc"
        }
        
        def _execute_search():
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.config.timeout,
                headers={
                    "User-Agent": self.config.user_agent,
                    "Accept": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        
        # Use common retry logic from base class
        results = self._execute_with_retry(
            _execute_search,
            "search",
            "openalex",
            handle_rate_limit=True
        )
        
        # Log detailed statistics
        citations_total = sum(r.citation_count or 0 for r in results)
        pdfs_count = sum(1 for r in results if r.pdf_url)
        dois_count = sum(1 for r in results if r.doi)
        logger.debug(f"OpenAlex search completed: {len(results)} results, "
                    f"{citations_total} total citations, {pdfs_count} with PDFs, {dois_count} with DOIs")
        
        return results

    def _parse_response(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse OpenAlex API response.
        
        Args:
            data: JSON response from OpenAlex API.
            
        Returns:
            List of SearchResult objects.
        """
        results = []
        
        if 'results' not in data:
            return results
        
        for work in data['results']:
            # Title
            title = work.get('title', '')
            
            # Authors
            authors = []
            if 'authorships' in work:
                for authorship in work['authorships']:
                    author = authorship.get('author', {})
                    if author:
                        display_name = author.get('display_name', '')
                        if display_name:
                            authors.append(display_name)
            
            # Year
            year = None
            publication_date = work.get('publication_date')
            if publication_date:
                try:
                    year = int(publication_date.split('-')[0])
                except (ValueError, IndexError):
                    pass
            
            # DOI
            doi = None
            doi_url = work.get('doi')
            if doi_url:
                # Extract DOI from URL (e.g., "https://doi.org/10.1234/example" -> "10.1234/example")
                if doi_url.startswith('https://doi.org/'):
                    doi = doi_url[16:]
                elif doi_url.startswith('http://doi.org/'):
                    doi = doi_url[15:]
                else:
                    doi = doi_url
            
            # Abstract
            abstract = ""
            if 'abstract_inverted_index' in work and work['abstract_inverted_index']:
                # Reconstruct abstract from inverted index
                abstract_dict = work['abstract_inverted_index']
                words = {}
                for word, positions in abstract_dict.items():
                    for pos in positions:
                        words[pos] = word
                if words:
                    max_pos = max(words.keys())
                    abstract = ' '.join([words.get(i, '') for i in range(max_pos + 1)])
            elif 'abstract' in work:
                abstract = work['abstract']
            
            # URL
            url = work.get('id', '')  # OpenAlex ID is a URL
            
            # PDF URL (open access)
            pdf_url = None
            if 'open_access' in work and work['open_access'].get('is_oa'):
                oa_url = work['open_access'].get('oa_url')
                if oa_url:
                    pdf_url = oa_url
            elif 'primary_location' in work:
                location = work['primary_location']
                if location and location.get('pdf_url'):
                    pdf_url = location['pdf_url']
            
            # Citation count
            citation_count = work.get('cited_by_count')
            
            # Venue
            venue = None
            if 'primary_location' in work:
                location = work['primary_location']
                if location and 'source' in location:
                    venue = location['source'].get('display_name')
            
            results.append(SearchResult(
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                url=url,
                doi=doi,
                source="openalex",
                pdf_url=pdf_url,
                venue=venue,
                citation_count=citation_count
            ))
        
        return results

