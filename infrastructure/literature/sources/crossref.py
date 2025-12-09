"""CrossRef API client for literature search.

Provides access to CrossRef database with:
- Works API for general search
- DOI-based metadata retrieval
- Comprehensive metadata (authors, venues, dates)
- Open access information
"""
from __future__ import annotations

import re
import requests
from typing import List, Dict, Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult

logger = get_logger(__name__)


class CrossRefSource(LiteratureSource):
    """Client for CrossRef Works API with retry logic."""

    BASE_URL = "https://api.crossref.org/works"

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search CrossRef with retry logic.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            LiteratureSearchError: If API request fails after all retries.
        """
        logger.info(f"Searching CrossRef for: {query}")
        
        params = {
            "query": query,
            "rows": limit,
            "sort": "relevance"
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
            "crossref",
            handle_rate_limit=True
        )
        
        # Log detailed statistics
        pdfs_count = sum(1 for r in results if r.pdf_url)
        dois_count = sum(1 for r in results if r.doi)
        logger.debug(f"CrossRef search completed: {len(results)} results, {pdfs_count} with PDFs, {dois_count} with DOIs")
        
        return results

    def _parse_response(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse CrossRef API response.
        
        Args:
            data: JSON response from CrossRef API.
            
        Returns:
            List of SearchResult objects.
        """
        results = []
        
        if 'message' not in data or 'items' not in data['message']:
            return results
        
        for item in data['message']['items']:
            # Title
            title = ""
            if 'title' in item and item['title']:
                title = item['title'][0] if isinstance(item['title'], list) else item['title']
            
            # Authors
            authors = []
            if 'author' in item:
                for author in item['author']:
                    name_parts = []
                    if 'given' in author:
                        name_parts.append(author['given'])
                    if 'family' in author:
                        name_parts.append(author['family'])
                    if name_parts:
                        authors.append(' '.join(name_parts))
            
            # Year
            year = None
            if 'published-print' in item and 'date-parts' in item['published-print']:
                date_parts = item['published-print']['date-parts'][0]
                if date_parts and len(date_parts) > 0:
                    try:
                        year = int(date_parts[0])
                    except (ValueError, TypeError):
                        pass
            elif 'published-online' in item and 'date-parts' in item['published-online']:
                date_parts = item['published-online']['date-parts'][0]
                if date_parts and len(date_parts) > 0:
                    try:
                        year = int(date_parts[0])
                    except (ValueError, TypeError):
                        pass
            
            # DOI
            doi = item.get('DOI', '')
            
            # Abstract
            abstract = ""
            if 'abstract' in item:
                abstract_text = item['abstract']
                # Remove XML/HTML tags if present
                if isinstance(abstract_text, str):
                    import re
                    abstract = re.sub(r'<[^>]+>', '', abstract_text)
            
            # URL
            url = f"https://doi.org/{doi}" if doi else ""
            
            # PDF URL (from link or resource)
            pdf_url = None
            if 'link' in item:
                for link in item['link']:
                    if link.get('content-type') == 'application/pdf':
                        pdf_url = link.get('URL')
                        if pdf_url:
                            break
            
            # Venue
            venue = None
            if 'container-title' in item and item['container-title']:
                venue = item['container-title'][0] if isinstance(item['container-title'], list) else item['container-title']
            
            results.append(SearchResult(
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                url=url,
                doi=doi,
                source="crossref",
                pdf_url=pdf_url,
                venue=venue
            ))
        
        return results

