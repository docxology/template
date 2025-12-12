"""Europe PMC API client for literature search.

Provides access to Europe PMC (European PubMed Central) with:
- REST API keyword search
- Open access PDF links
- Citation counts
- Comprehensive metadata
"""
from __future__ import annotations

import requests
from typing import List, Dict, Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult

logger = get_logger(__name__)


class EuropePMCSource(LiteratureSource):
    """Client for Europe PMC REST API with retry logic."""

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search Europe PMC with retry logic.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            LiteratureSearchError: If API request fails after all retries.
        """
        logger.info(f"Searching Europe PMC for: {query}")
        
        params = {
            "query": query,
            "pageSize": limit,
            "format": "json",
            "resultType": "core"
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
            "europepmc",
            handle_rate_limit=True
        )
        
        # Log detailed statistics
        citations_total = sum(r.citation_count or 0 for r in results)
        pdfs_count = sum(1 for r in results if r.pdf_url)
        dois_count = sum(1 for r in results if r.doi)
        logger.debug(f"Europe PMC search completed: {len(results)} results, "
                    f"{citations_total} total citations, {pdfs_count} with PDFs, {dois_count} with DOIs")
        
        return results

    def _parse_response(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse Europe PMC API response.
        
        Args:
            data: JSON response from Europe PMC API.
            
        Returns:
            List of SearchResult objects.
        """
        results = []
        
        if 'resultList' not in data or 'result' not in data['resultList']:
            return results
        
        for paper in data['resultList']['result']:
            # Authors
            authors = []
            if 'authorList' in paper and 'author' in paper['authorList']:
                for author in paper['authorList']['author']:
                    if isinstance(author, dict):
                        name_parts = []
                        if 'firstName' in author:
                            name_parts.append(author['firstName'])
                        if 'lastName' in author:
                            name_parts.append(author['lastName'])
                        if name_parts:
                            authors.append(' '.join(name_parts))
            
            # Year
            year = None
            if 'pubYear' in paper and paper['pubYear']:
                try:
                    year = int(paper['pubYear'])
                except (ValueError, TypeError):
                    pass
            
            # DOI
            doi = None
            if 'doi' in paper and paper['doi']:
                doi = paper['doi']
            
            # PDF URL (open access)
            pdf_url = None
            if 'fullTextUrlList' in paper and 'fullTextUrl' in paper['fullTextUrlList']:
                for url_info in paper['fullTextUrlList']['fullTextUrl']:
                    if isinstance(url_info, dict) and url_info.get('documentStyle') == 'pdf':
                        pdf_url = url_info.get('url')
                        if pdf_url:
                            break
            
            # Citation count
            citation_count = None
            if 'citedByCount' in paper and paper['citedByCount']:
                try:
                    citation_count = int(paper['citedByCount'])
                except (ValueError, TypeError):
                    pass
            
            # URL
            url = ""
            if 'id' in paper:
                pmc_id = paper.get('pmcid') or paper.get('id')
                if pmc_id:
                    url = f"https://europepmc.org/article/MED/{pmc_id}"
            
            results.append(SearchResult(
                title=paper.get('title', ''),
                authors=authors,
                year=year,
                abstract=paper.get('abstractText', ''),
                url=url,
                doi=doi,
                source="europepmc",
                pdf_url=pdf_url,
                venue=paper.get('journalTitle'),
                citation_count=citation_count
            ))
        
        return results

