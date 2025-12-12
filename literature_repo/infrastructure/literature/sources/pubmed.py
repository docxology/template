"""PubMed/NCBI E-utilities API client for literature search.

Provides access to PubMed database with:
- Keyword search via E-utilities API
- Abstract extraction
- DOI and PMC ID extraction
- PDF links from PMC (PubMed Central)
- Rate limiting compliance (3 requests/second)
"""
from __future__ import annotations

import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult

logger = get_logger(__name__)


class PubMedSource(LiteratureSource):
    """Client for PubMed/NCBI E-utilities API with standardized retry logic."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    EUTILS_DELAY = 0.34  # ~3 requests/second max (NCBI requirement)

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search PubMed with retry logic and rate limiting.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            LiteratureSearchError: If API request fails after all retries.
        """
        logger.info(f"Searching PubMed for: {query}")
        
        def _execute_search():
            # Step 1: Search for IDs
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": limit,
                "retmode": "xml",
                "usehistory": "y"
            }
            
            search_url = f"{self.BASE_URL}/esearch.fcgi"
            search_response = requests.get(
                search_url,
                params=search_params,
                timeout=self.config.timeout,
                headers={"User-Agent": self.config.user_agent}
            )
            search_response.raise_for_status()
            
            # Parse search results to get IDs
            search_root = ET.fromstring(search_response.text)
            id_list = search_root.find(".//IdList")
            if id_list is None or len(id_list) == 0:
                return []
            
            pmids = [id_elem.text for id_elem in id_list.findall("Id")]
            if not pmids:
                return []
            
            # Step 2: Fetch details for IDs
            time.sleep(self.EUTILS_DELAY)  # Rate limiting between requests
            
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract"
            }
            
            fetch_url = f"{self.BASE_URL}/efetch.fcgi"
            fetch_response = requests.get(
                fetch_url,
                params=fetch_params,
                timeout=self.config.timeout,
                headers={"User-Agent": self.config.user_agent}
            )
            fetch_response.raise_for_status()
            
            return self._parse_response(fetch_response.text)
        
        # Use common retry logic from base class
        results = self._execute_with_retry(
            _execute_search,
            "search",
            "pubmed",
            handle_rate_limit=True
        )
        
        # Log detailed statistics
        pdfs_count = sum(1 for r in results if r.pdf_url)
        dois_count = sum(1 for r in results if r.doi)
        logger.debug(f"PubMed search completed: {len(results)} results, {pdfs_count} with PDFs, {dois_count} with DOIs")
        
        return results

    def _parse_response(self, xml_data: str) -> List[SearchResult]:
        """Parse PubMed XML response.
        
        Args:
            xml_data: XML response from efetch.
            
        Returns:
            List of SearchResult objects.
        """
        results = []
        root = ET.fromstring(xml_data)
        
        # PubMed XML namespace
        ns = {'': 'http://www.ncbi.nlm.nih.gov'}
        
        for article in root.findall('.//PubmedArticle'):
            # Title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else ""
            
            # Authors
            authors = []
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author in author_list.findall('Author'):
                    last_name = author.find('LastName')
                    first_name = author.find('ForeName')
                    if last_name is not None:
                        name = last_name.text
                        if first_name is not None:
                            name = f"{first_name.text} {name}"
                        authors.append(name)
            
            # Abstract
            abstract = ""
            abstract_elem = article.find('.//Abstract/AbstractText')
            if abstract_elem is not None:
                abstract = abstract_elem.text or ""
            else:
                # Try multiple abstract text elements
                abstract_parts = []
                for abs_text in article.findall('.//Abstract/AbstractText'):
                    if abs_text.text:
                        abstract_parts.append(abs_text.text)
                abstract = " ".join(abstract_parts)
            
            # Year
            year = None
            pub_date = article.find('.//PubDate/Year')
            if pub_date is not None and pub_date.text:
                try:
                    year = int(pub_date.text)
                except ValueError:
                    pass
            
            # DOI
            doi = None
            article_id_list = article.find('.//ArticleIdList')
            if article_id_list is not None:
                for article_id in article_id_list.findall('ArticleId'):
                    if article_id.get('IdType') == 'doi':
                        doi = article_id.text
                        break
            
            # PMC ID (for PDF URL)
            pmc_id = None
            if article_id_list is not None:
                for article_id in article_id_list.findall('ArticleId'):
                    if article_id.get('IdType') == 'pmc':
                        pmc_id = article_id.text
                        break
            
            # URL
            pmid_elem = article.find('.//MedlineCitation/PMID')
            pmid = pmid_elem.text if pmid_elem is not None else ""
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}" if pmid else ""
            
            # PDF URL from PMC
            pdf_url = None
            if pmc_id:
                # Remove "PMC" prefix if present
                pmc_num = pmc_id.replace("PMC", "").replace("pmc", "")
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_num}/pdf/"
            
            # Venue (Journal)
            venue = None
            journal_elem = article.find('.//Journal/Title')
            if journal_elem is not None:
                venue = journal_elem.text
            
            results.append(SearchResult(
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                url=url,
                doi=doi,
                source="pubmed",
                pdf_url=pdf_url,
                venue=venue
            ))
        
        return results

