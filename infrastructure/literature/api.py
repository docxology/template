"""API clients for literature databases.

This module provides unified access to various literature databases:
- arXiv
- Semantic Scholar
- CrossRef
- PubMed
"""
from __future__ import annotations

import abc
import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from infrastructure.core.exceptions import APIRateLimitError, LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.config import LiteratureConfig

logger = get_logger(__name__)


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
    """Abstract base class for literature sources."""

    def __init__(self, config: LiteratureConfig):
        self.config = config

    @abc.abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search for papers."""
        pass


class ArxivSource(LiteratureSource):
    """Client for arXiv API."""

    BASE_URL = "http://export.arxiv.org/api/query"

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


class SemanticScholarSource(LiteratureSource):
    """Client for Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search Semantic Scholar."""
        logger.info(f"Searching Semantic Scholar for: {query}")
        
        headers = {}
        if self.config.semanticscholar_api_key:
            headers["x-api-key"] = self.config.semanticscholar_api_key

        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,abstract,url,externalIds,venue,citationCount,isOpenAccess,openAccessPdf"
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, headers=headers)
            
            if response.status_code == 429:
                raise APIRateLimitError("Semantic Scholar rate limit exceeded")
                
            response.raise_for_status()
            data = response.json()
            
            return self._parse_response(data)
            
        except requests.exceptions.RequestException as e:
            raise LiteratureSearchError(f"Semantic Scholar API request failed: {e}", context={"source": "semanticscholar"})

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

