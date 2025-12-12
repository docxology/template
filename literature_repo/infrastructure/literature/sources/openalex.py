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
            try:
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
                
                # Validate response structure
                if not isinstance(data, dict):
                    raise ValueError(f"Expected dict response, got {type(data).__name__}")
                
                return self._parse_response(data)
            except requests.exceptions.Timeout as e:
                logger.warning(f"OpenAlex API timeout: {e}")
                raise
            except requests.exceptions.RequestException as e:
                logger.warning(f"OpenAlex API request failed: {e}")
                raise
            except (ValueError, KeyError) as e:
                logger.warning(f"OpenAlex API response parsing error: {e}")
                raise
        
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
            logger.debug("OpenAlex response missing 'results' key")
            return results
        
        for work in data['results']:
            try:
                # Title
                title = work.get('title', '')
                if not title:
                    logger.debug("Skipping work with missing title")
                    continue
                
                # Authors
                authors = []
                if 'authorships' in work and work['authorships']:
                    for authorship in work['authorships']:
                        if not authorship:
                            continue
                        author = authorship.get('author', {})
                        if author and isinstance(author, dict):
                            display_name = author.get('display_name', '')
                            if display_name:
                                authors.append(display_name)
                
                # Year
                year = None
                publication_date = work.get('publication_date')
                if publication_date:
                    try:
                        year = int(publication_date.split('-')[0])
                    except (ValueError, IndexError, AttributeError):
                        logger.debug(f"Could not parse publication date: {publication_date}")
                        pass
                
                # DOI
                doi = None
                doi_url = work.get('doi')
                if doi_url:
                    # Extract DOI from URL (e.g., "https://doi.org/10.1234/example" -> "10.1234/example")
                    if isinstance(doi_url, str):
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
                    try:
                        abstract_dict = work['abstract_inverted_index']
                        if isinstance(abstract_dict, dict):
                            words = {}
                            for word, positions in abstract_dict.items():
                                if isinstance(positions, list):
                                    for pos in positions:
                                        if isinstance(pos, int):
                                            words[pos] = word
                            if words:
                                max_pos = max(words.keys())
                                abstract = ' '.join([words.get(i, '') for i in range(max_pos + 1)])
                    except (TypeError, ValueError, KeyError) as e:
                        logger.debug(f"Error reconstructing abstract from inverted index: {e}")
                elif 'abstract' in work and work['abstract']:
                    abstract = work['abstract'] if isinstance(work['abstract'], str) else ""
                
                # URL
                url = work.get('id', '')  # OpenAlex ID is a URL
                
                # PDF URL (open access) - Fixed NoneType error
                pdf_url = None
                if 'open_access' in work:
                    open_access = work['open_access']
                    # Check if open_access is not None before accessing its properties
                    if open_access is not None and isinstance(open_access, dict) and open_access.get('is_oa'):
                        oa_url = open_access.get('oa_url')
                        if oa_url:
                            pdf_url = oa_url
                
                # Fallback to primary_location if open_access didn't provide PDF
                if not pdf_url and 'primary_location' in work:
                    location = work['primary_location']
                    if location and isinstance(location, dict):
                        pdf_url_from_location = location.get('pdf_url')
                        if pdf_url_from_location:
                            pdf_url = pdf_url_from_location
                
                # Citation count
                citation_count = work.get('cited_by_count')
                if citation_count is not None:
                    try:
                        citation_count = int(citation_count)
                    except (ValueError, TypeError):
                        citation_count = None
                
                # Venue - Fixed NoneType error
                venue = None
                if 'primary_location' in work:
                    location = work['primary_location']
                    # Check if location and source are not None before accessing nested properties
                    if location and isinstance(location, dict) and 'source' in location:
                        source = location['source']
                        if source is not None and isinstance(source, dict):
                            venue = source.get('display_name')
                
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
            except Exception as e:
                # Log error but continue processing other results
                work_id = work.get('id', 'unknown')
                logger.warning(f"Error parsing OpenAlex work {work_id}: {e}. Skipping this result.")
                logger.debug(f"Work data: {work}", exc_info=True)
                continue
        
        return results

