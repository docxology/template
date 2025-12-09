"""arXiv API client for literature search.

Provides access to the arXiv preprint repository with:
- Title-based search with similarity matching
- General keyword search
- PDF URL extraction
- Rate limiting compliance
"""
from __future__ import annotations

import time
import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Optional

from infrastructure.core.exceptions import LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult, title_similarity

logger = get_logger(__name__)


class ArxivSource(LiteratureSource):
    """Client for arXiv API."""

    BASE_URL = "http://export.arxiv.org/api/query"
    TITLE_SIMILARITY_THRESHOLD = 0.7  # Minimum similarity for title match

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search arXiv."""
        logger.info(f"Searching arXiv for: {query}")
        
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit
        }
        
        try:
            # Rate limiting
            time.sleep(self.config.arxiv_delay)
            
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            return self._parse_response(response.text)
            
        except requests.exceptions.RequestException as e:
            raise LiteratureSearchError(f"arXiv API request failed: {e}", context={"source": "arxiv"})

    def search_by_title(self, title: str, limit: int = 5) -> Optional[SearchResult]:
        """Search arXiv for a paper by title with similarity matching.
        
        Searches arXiv using the title as a query, then finds the best
        matching result based on title similarity.
        
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
        
        # Use title-specific search
        params = {
            "search_query": f'ti:"{clean_title}"',
            "start": 0,
            "max_results": limit
        }
        
        try:
            # Rate limiting
            time.sleep(self.config.arxiv_delay)
            
            response = requests.get(self.BASE_URL, params=params, timeout=self.config.timeout)
            response.raise_for_status()
            
            results = self._parse_response(response.text)
            
            if not results:
                # Try broader search without quotes
                params["search_query"] = f"ti:{clean_title}"
                time.sleep(self.config.arxiv_delay)
                response = requests.get(self.BASE_URL, params=params, timeout=self.config.timeout)
                response.raise_for_status()
                results = self._parse_response(response.text)
            
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
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"arXiv title search failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"arXiv title search error: {e}")
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
                    # Clean up arXiv PDF URLs by removing version suffixes
                    if pdf_link and 'arxiv.org/pdf/' in pdf_link:
                        # Remove version suffix (e.g., 2311.18356v2 -> 2311.18356)
                        pdf_link = re.sub(r'(\d{4}\.\d{4,5})v\d+', r'\1', pdf_link)
            
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

