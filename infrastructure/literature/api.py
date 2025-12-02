"""API clients for literature databases.

This module provides unified access to various literature databases:
- arXiv
- Semantic Scholar
- CrossRef
- PubMed
- Unpaywall (for open access PDF resolution)
"""
from __future__ import annotations

import abc
import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

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


def _normalize_title(title: str) -> str:
    """Normalize a title for comparison.
    
    Removes punctuation, extra whitespace, and converts to lowercase.
    
    Args:
        title: Title string to normalize.
        
    Returns:
        Normalized title string.
    """
    import re
    # Remove punctuation and extra whitespace, convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = ' '.join(normalized.split())
    return normalized


def _title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles using word overlap.
    
    Uses Jaccard similarity on word sets after normalization.
    
    Args:
        title1: First title.
        title2: Second title.
        
    Returns:
        Similarity score between 0.0 and 1.0.
    """
    norm1 = _normalize_title(title1)
    norm2 = _normalize_title(title2)
    
    # Split into words
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    # Handle empty sets
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


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
        import re
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
                similarity = _title_similarity(title, result.title)
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
    """Client for Semantic Scholar API with retry logic."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search Semantic Scholar with retry on rate limit.
        
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
        
        last_error = None
        for attempt in range(self.config.retry_attempts):
            try:
                # Rate limiting delay before request
                delay = self.config.semanticscholar_delay * (2 ** attempt)  # Exponential backoff
                if attempt > 0:
                    logger.debug(f"Retry attempt {attempt + 1}, waiting {delay:.1f}s")
                time.sleep(delay)
                
                response = requests.get(
                    self.BASE_URL, 
                    params=params, 
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 429:
                    # Remove exponential backoff delay - allow immediate retry
                    logger.warning(f"Rate limited, retrying immediately...")
                    last_error = APIRateLimitError("Semantic Scholar rate limit exceeded")
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                results = self._parse_response(data)
                logger.debug(f"Semantic Scholar returned {len(results)} results")
                return results
                
            except requests.exceptions.RequestException as e:
                last_error = LiteratureSearchError(
                    f"Semantic Scholar API request failed: {e}", 
                    context={"source": "semanticscholar", "attempt": attempt + 1}
                )
                if attempt < self.config.retry_attempts - 1:
                    logger.warning(f"Request failed, will retry: {e}")
                continue
        
        # All retries exhausted
        if last_error:
            raise last_error
        raise LiteratureSearchError("Semantic Scholar search failed after all retries")

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


@dataclass
class UnpaywallResult:
    """Result from Unpaywall API lookup."""
    doi: str
    is_oa: bool
    pdf_url: Optional[str] = None
    oa_status: Optional[str] = None  # "gold", "hybrid", "bronze", "green", "closed"
    host_type: Optional[str] = None  # "publisher", "repository"
    version: Optional[str] = None  # "publishedVersion", "acceptedVersion", etc.
    license: Optional[str] = None


class UnpaywallSource:
    """Client for Unpaywall API to find open access PDFs.

    Unpaywall provides a database of legal, open access versions of papers.
    It requires an email address for API access (no key needed).

    API Documentation: https://unpaywall.org/products/api

    Rate Limits:
    - 100,000 requests per day for registered emails
    - 50 requests per day for non-registered emails
    - Includes retry logic with exponential backoff
    """

    BASE_URL = "https://api.unpaywall.org/v2"
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 2.0

    def __init__(self, config: LiteratureConfig):
        """Initialize Unpaywall source.

        Args:
            config: Literature configuration with unpaywall_email.
        """
        self.config = config
        self._last_request_time = 0
        self._min_delay = 0.1  # Minimum delay between requests (10 requests/second max)

        if not config.unpaywall_email:
            logger.warning("Unpaywall email not configured - API calls will fail")
        elif not self._validate_email(config.unpaywall_email):
            logger.warning(f"Unpaywall email format appears invalid: {config.unpaywall_email}")
        else:
            logger.debug(f"Unpaywall initialized with email: {config.unpaywall_email}")

    def _validate_email(self, email: str) -> bool:
        """Basic email validation.

        Args:
            email: Email address to validate.

        Returns:
            True if email format is valid.
        """
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    def _rate_limit_delay(self):
        """Enforce rate limiting between requests."""
        import time
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            delay = self._min_delay - elapsed
            logger.debug(f"Unpaywall rate limiting: waiting {delay:.2f}s")
            time.sleep(delay)
        self._last_request_time = time.time()

    def get_pdf_url(self, doi: str) -> Optional[str]:
        """Get open access PDF URL for a DOI.
        
        Args:
            doi: The DOI to look up (e.g., "10.1038/nature12373").
            
        Returns:
            URL to open access PDF, or None if not available.
        """
        result = self.lookup(doi)
        return result.pdf_url if result else None

    def lookup(self, doi: str) -> Optional[UnpaywallResult]:
        """Look up a DOI in Unpaywall with retry logic and rate limiting.

        Args:
            doi: The DOI to look up.

        Returns:
            UnpaywallResult with OA information, or None on failure.
        """
        if not self.config.unpaywall_email:
            logger.warning("Cannot query Unpaywall: email not configured")
            return None

        if not self._validate_email(self.config.unpaywall_email):
            logger.warning(f"Skipping Unpaywall lookup: invalid email format: {self.config.unpaywall_email}")
            return None

        # Clean DOI (remove URL prefix if present)
        clean_doi = doi
        if doi.startswith("https://doi.org/"):
            clean_doi = doi[16:]
        elif doi.startswith("http://doi.org/"):
            clean_doi = doi[15:]
        elif doi.startswith("doi:"):
            clean_doi = doi[4:]

        url = f"{self.BASE_URL}/{clean_doi}"
        params = {"email": self.config.unpaywall_email}

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                # Rate limiting
                self._rate_limit_delay()

                # Exponential backoff for retries
                if attempt > 0:
                    delay = self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
                    logger.debug(f"Unpaywall retry attempt {attempt + 1}, waiting {delay:.1f}s")
                    time.sleep(delay)

                logger.debug(f"Querying Unpaywall for DOI: {clean_doi} (attempt {attempt + 1})")
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.config.timeout,
                    headers={"User-Agent": self.config.user_agent}
                )

                if response.status_code == 404:
                    logger.debug(f"DOI not found in Unpaywall: {clean_doi}")
                    return None

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    wait_time = float(retry_after) if retry_after else self.BASE_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Unpaywall rate limited, waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    last_error = APIRateLimitError("Unpaywall rate limit exceeded")
                    continue

                response.raise_for_status()
                data = response.json()

                result = self._parse_response(data)
                logger.debug(f"Unpaywall found OA version for {clean_doi}: {result.is_oa}")
                return result

            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Unpaywall timeout for {clean_doi} (attempt {attempt + 1}): {e}")
                if attempt == self.MAX_RETRIES - 1:
                    break
                continue

            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Unpaywall request failed for {clean_doi} (attempt {attempt + 1}): {e}")
                if attempt == self.MAX_RETRIES - 1:
                    break
                continue

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected Unpaywall error for {clean_doi}: {e}")
                break

        logger.warning(f"Unpaywall lookup failed for {clean_doi} after {self.MAX_RETRIES} attempts: {last_error}")
        return None

    def _parse_response(self, data: Dict[str, Any]) -> UnpaywallResult:
        """Parse Unpaywall API response.
        
        Args:
            data: JSON response from Unpaywall API.
            
        Returns:
            UnpaywallResult with extracted information.
        """
        is_oa = data.get("is_oa", False)
        pdf_url = None
        oa_status = data.get("oa_status")
        host_type = None
        version = None
        license_info = None
        
        # Get best OA location (prioritize published version)
        best_oa = data.get("best_oa_location")
        if best_oa:
            pdf_url = best_oa.get("url_for_pdf")
            host_type = best_oa.get("host_type")
            version = best_oa.get("version")
            license_info = best_oa.get("license")
        
        # If no PDF URL from best location, check other locations
        if not pdf_url and is_oa:
            oa_locations = data.get("oa_locations", [])
            for loc in oa_locations:
                url = loc.get("url_for_pdf")
                if url:
                    pdf_url = url
                    host_type = loc.get("host_type")
                    version = loc.get("version")
                    license_info = loc.get("license")
                    break
        
        return UnpaywallResult(
            doi=data.get("doi", ""),
            is_oa=is_oa,
            pdf_url=pdf_url,
            oa_status=oa_status,
            host_type=host_type,
            version=version,
            license=license_info
        )


class BiorxivSource:
    """Client for bioRxiv/medRxiv API to find preprint PDFs.
    
    bioRxiv and medRxiv are preprint servers for biology and medicine.
    Many papers are first posted here before journal publication.
    
    API Documentation: https://api.biorxiv.org/
    
    Features:
    - Search by DOI to find preprint versions
    - Search by title with similarity matching
    - Get PDF URLs for open access preprints
    """
    
    BASE_URL = "https://api.biorxiv.org"
    TITLE_SIMILARITY_THRESHOLD = 0.7
    
    def __init__(self, config: LiteratureConfig):
        """Initialize bioRxiv source.
        
        Args:
            config: Literature configuration.
        """
        self.config = config
        self._last_request_time = 0
        self._min_delay = 1.0  # Be polite to the API
    
    def _rate_limit_delay(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            delay = self._min_delay - elapsed
            logger.debug(f"bioRxiv rate limiting: waiting {delay:.2f}s")
            time.sleep(delay)
        self._last_request_time = time.time()
    
    def search_by_doi(self, doi: str) -> Optional[SearchResult]:
        """Search for a paper by DOI in bioRxiv/medRxiv.
        
        Uses the bioRxiv API to find papers that were posted as preprints
        and later published with a DOI.
        
        Args:
            doi: DOI to search for.
            
        Returns:
            SearchResult with PDF URL if found, else None.
        """
        # Clean DOI
        clean_doi = doi
        if doi.startswith("https://doi.org/"):
            clean_doi = doi[16:]
        elif doi.startswith("http://doi.org/"):
            clean_doi = doi[15:]
        elif doi.startswith("doi:"):
            clean_doi = doi[4:]
        
        logger.debug(f"Searching bioRxiv/medRxiv for DOI: {clean_doi}")
        
        # Try bioRxiv first, then medRxiv
        for server in ["biorxiv", "medrxiv"]:
            result = self._search_server_by_doi(server, clean_doi)
            if result:
                return result
        
        return None
    
    def _search_server_by_doi(self, server: str, doi: str) -> Optional[SearchResult]:
        """Search a specific server (bioRxiv or medRxiv) by DOI.
        
        Args:
            server: "biorxiv" or "medrxiv".
            doi: Clean DOI string.
            
        Returns:
            SearchResult if found, else None.
        """
        # Use the pub endpoint to search for published DOI -> preprint mapping
        url = f"{self.BASE_URL}/pub/{server}/{doi}"
        
        try:
            self._rate_limit_delay()
            
            response = requests.get(
                url,
                timeout=self.config.timeout,
                headers={"User-Agent": self.config.user_agent}
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Check if we got a result
            collection = data.get("collection", [])
            if not collection:
                return None
            
            # Take the first (most recent) result
            paper = collection[0]
            
            # Build PDF URL
            biorxiv_doi = paper.get("biorxiv_doi", "")
            pdf_url = None
            if biorxiv_doi:
                # Format: https://www.biorxiv.org/content/10.1101/2020.01.01.123456v1.full.pdf
                pdf_url = f"https://www.{server}.org/content/{biorxiv_doi}.full.pdf"
            
            # Parse authors
            authors_str = paper.get("authors", "")
            authors = [a.strip() for a in authors_str.split(";")] if authors_str else []
            
            # Parse date for year
            date_str = paper.get("date", "")
            year = None
            if date_str and len(date_str) >= 4:
                try:
                    year = int(date_str[:4])
                except ValueError:
                    pass
            
            return SearchResult(
                title=paper.get("title", ""),
                authors=authors,
                year=year,
                abstract=paper.get("abstract", ""),
                url=f"https://www.{server}.org/content/{biorxiv_doi}",
                doi=biorxiv_doi,
                source=server,
                pdf_url=pdf_url,
                venue=f"{server} preprint"
            )
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"{server} DOI search failed: {e}")
            return None
        except Exception as e:
            logger.debug(f"{server} DOI search error: {e}")
            return None
    
    def search_by_title(self, title: str, limit: int = 5) -> Optional[SearchResult]:
        """Search bioRxiv/medRxiv for a paper by title.
        
        Uses the details endpoint with title-based filtering.
        
        Args:
            title: Paper title to search for.
            limit: Maximum number of results to check.
            
        Returns:
            Best matching SearchResult if similarity > threshold, else None.
        """
        logger.debug(f"Searching bioRxiv/medRxiv by title: {title[:50]}...")
        
        # Try both servers
        for server in ["biorxiv", "medrxiv"]:
            result = self._search_server_by_title(server, title, limit)
            if result:
                return result
        
        return None
    
    def _search_server_by_title(self, server: str, title: str, limit: int) -> Optional[SearchResult]:
        """Search a specific server by title using recent papers.
        
        Note: bioRxiv API doesn't have direct title search, so we use
        the details endpoint and filter by date range then match titles.
        
        Args:
            server: "biorxiv" or "medrxiv".
            title: Paper title to search for.
            limit: Max results to check.
            
        Returns:
            Best matching SearchResult if found.
        """
        # Get recent papers (last 30 days) and search through them
        # This is a limitation of the bioRxiv API
        from datetime import datetime, timedelta
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Use the details endpoint
        url = f"{self.BASE_URL}/details/{server}/{start_date}/{end_date}/0"
        
        try:
            self._rate_limit_delay()
            
            response = requests.get(
                url,
                timeout=self.config.timeout,
                headers={"User-Agent": self.config.user_agent}
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            collection = data.get("collection", [])
            
            if not collection:
                return None
            
            # Find best title match
            best_match = None
            best_similarity = 0.0
            
            for paper in collection[:limit * 10]:  # Check more papers for title matching
                paper_title = paper.get("title", "")
                similarity = _title_similarity(title, paper_title)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = paper
            
            if best_match and best_similarity >= self.TITLE_SIMILARITY_THRESHOLD:
                # Build result
                biorxiv_doi = best_match.get("doi", "")
                pdf_url = f"https://www.{server}.org/content/{biorxiv_doi}.full.pdf" if biorxiv_doi else None
                
                authors_str = best_match.get("authors", "")
                authors = [a.strip() for a in authors_str.split(";")] if authors_str else []
                
                date_str = best_match.get("date", "")
                year = int(date_str[:4]) if date_str and len(date_str) >= 4 else None
                
                logger.info(f"Found {server} match with similarity {best_similarity:.2f}")
                
                return SearchResult(
                    title=best_match.get("title", ""),
                    authors=authors,
                    year=year,
                    abstract=best_match.get("abstract", ""),
                    url=f"https://www.{server}.org/content/{biorxiv_doi}",
                    doi=biorxiv_doi,
                    source=server,
                    pdf_url=pdf_url,
                    venue=f"{server} preprint"
                )
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"{server} title search failed: {e}")
            return None
        except Exception as e:
            logger.debug(f"{server} title search error: {e}")
            return None
    
    def get_pdf_url(self, doi: str) -> Optional[str]:
        """Get PDF URL for a DOI if available in bioRxiv/medRxiv.
        
        Args:
            doi: DOI to look up.
            
        Returns:
            PDF URL if found, else None.
        """
        result = self.search_by_doi(doi)
        return result.pdf_url if result else None

