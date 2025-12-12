"""arXiv API client for literature search.

Provides access to the arXiv preprint repository with:
- Title-based search with similarity matching
- General keyword search
- PDF URL extraction
- Rate limiting compliance with retry logic
"""
from __future__ import annotations

import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult, title_similarity

logger = get_logger(__name__)


class ArxivSource(LiteratureSource):
    """Client for arXiv API with standardized retry logic."""

    BASE_URL = "http://export.arxiv.org/api/query"
    TITLE_SIMILARITY_THRESHOLD = 0.7  # Minimum similarity for title match

    @staticmethod
    def normalize_arxiv_pdf_url(url: str) -> str:
        """Normalize arXiv PDF URL to ensure correct format.
        
        Ensures arXiv PDF URLs use the correct format (arxiv.org/pdf/ID.pdf)
        and removes version suffixes. Also handles abstract URLs by converting
        them to PDF URLs.
        
        Args:
            url: arXiv URL (can be abstract or PDF URL).
            
        Returns:
            Normalized arXiv PDF URL.
        """
        if not url:
            return url
        
        # Extract arXiv ID from various URL formats
        # Pattern matches: YYMM.NNNNN (new format) or category/YYMMNNN (old format)
        arxiv_match = re.search(r'arxiv\.org/(?:abs|pdf)/((?:\d{4}\.\d{4,5})|(?:\w+-\w+/\d{7}))(?:v\d+)?', url)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            # Return normalized PDF URL (remove version suffix)
            return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        return url

    @staticmethod
    def validate_arxiv_pdf_url(url: str) -> bool:
        """Validate that URL is a valid arXiv PDF URL.
        
        Args:
            url: URL to validate.
            
        Returns:
            True if URL is a valid arXiv PDF URL, False otherwise.
        """
        if not url:
            return False
        
        # Check if it's an arXiv PDF URL
        return bool(re.search(r'arxiv\.org/pdf/(?:\d{4}\.\d{4,5}|\w+-\w+/\d{7})(?:\.pdf)?', url))

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search arXiv with retry logic and rate limiting.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            LiteratureSearchError: If API request fails after all retries.
        """
        logger.info(f"Searching arXiv for: {query}")
        
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit
        }
        
        def _execute_search():
            # Use source-specific timeout if available
            timeout = self.config.source_configs.get("arxiv", {}).get("timeout", self.config.timeout)
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            return self._parse_response(response.text)
        
        # Use common retry logic from base class
        results = self._execute_with_retry(
            _execute_search,
            "search",
            "arxiv",
            handle_rate_limit=True
        )
        
        # Log detailed statistics
        pdfs_count = sum(1 for r in results if r.pdf_url)
        dois_count = sum(1 for r in results if r.doi)
        logger.debug(f"arXiv search completed: {len(results)} results, {pdfs_count} with PDFs, {dois_count} with DOIs")
        
        return results

    def search_by_title(self, title: str, limit: int = 5) -> Optional[SearchResult]:
        """Search arXiv for a paper by title with similarity matching.
        
        Searches arXiv using the title as a query, then finds the best
        matching result based on title similarity. Uses retry logic for reliability.
        
        Args:
            title: Paper title to search for.
            limit: Maximum number of results to check.
            
        Returns:
            Best matching SearchResult if similarity > threshold, else None.
        """
        logger.debug(f"Searching arXiv by title: {title[:50]}...")
        
        # Clean title for search query (remove special chars that might break query)
        clean_title = re.sub(r'[^\w\s]', ' ', title)
        clean_title = ' '.join(clean_title.split())
        
        def _execute_title_search():
            # Use source-specific timeout if available
            timeout = self.config.source_configs.get("arxiv", {}).get("timeout", self.config.timeout)
            
            # Use title-specific search
            params = {
                "search_query": f'ti:"{clean_title}"',
                "start": 0,
                "max_results": limit
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=timeout)
            response.raise_for_status()
            results = self._parse_response(response.text)
            
            if not results:
                # Try broader search without quotes
                params["search_query"] = f"ti:{clean_title}"
                response = requests.get(self.BASE_URL, params=params, timeout=timeout)
                response.raise_for_status()
                results = self._parse_response(response.text)
            
            return results
        
        try:
            # Use common retry logic
            results = self._execute_with_retry(
                _execute_title_search,
                "title_search",
                "arxiv",
                handle_rate_limit=True
            )
        except Exception as e:
            logger.warning(f"arXiv title search failed: {e}")
            return None
        
        if not results:
            logger.debug(f"No arXiv results found for title: {title[:50]}...")
            return None
        
        # Find best matching result by title similarity
        best_match = None
        best_similarity = 0.0
        
        for result in results:
            similarity = title_similarity(title, result.title)
            logger.debug(f"Title similarity: {similarity:.2f} for '{result.title[:50]}...'")
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = result
        
        if best_match and best_similarity >= self.TITLE_SIMILARITY_THRESHOLD:
            logger.info(f"Found arXiv match with similarity {best_similarity:.2f}: {best_match.title[:50]}...")
            return best_match
        else:
            logger.debug(f"Best arXiv match similarity {best_similarity:.2f} below threshold {self.TITLE_SIMILARITY_THRESHOLD}")
            return None

    def _parse_response(self, xml_data: str) -> List[SearchResult]:
        results = []
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            id_url = entry.find('atom:id', ns).text
            published = entry.find('atom:published', ns).text
            year = int(published.split('-')[0]) if published else None
            
            authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
            
            pdf_link = None
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    pdf_link = link.get('href')
                    break
            
            # If no PDF link found, try to generate from abstract URL
            if not pdf_link:
                # Extract arXiv ID from abstract URL and generate PDF URL
                arxiv_match = re.search(r'arxiv\.org/abs/((?:\d{4}\.\d{4,5})|(?:\w+-\w+/\d{7}))(?:v\d+)?', id_url)
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)
                    pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            # Normalize PDF URL to ensure correct format
            if pdf_link:
                pdf_link = self.normalize_arxiv_pdf_url(pdf_link)
                # Validate the normalized URL
                if not self.validate_arxiv_pdf_url(pdf_link):
                    logger.warning(f"Generated invalid arXiv PDF URL: {pdf_link}, using as-is")
            
            doi = None
            arxiv_doi = entry.find('arxiv:doi', ns)
            if arxiv_doi is not None:
                doi = arxiv_doi.text

            results.append(SearchResult(
                title=title,
                authors=authors,
                year=year,
                abstract=summary,
                url=id_url,
                doi=doi,
                source="arxiv",
                pdf_url=pdf_link,
                venue="arXiv"
            ))
            
        return results

