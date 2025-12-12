"""bioRxiv/medRxiv API client for preprint search.

Provides access to bioRxiv and medRxiv preprint servers with:
- DOI-based search
- Title-based search with similarity matching
- PDF URL extraction
- Biology and medicine preprints
"""
from __future__ import annotations

import requests
from typing import Optional, List
from datetime import datetime, timedelta

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.sources.base import LiteratureSource, SearchResult, title_similarity

logger = get_logger(__name__)


class BiorxivSource(LiteratureSource):
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
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search bioRxiv/medRxiv for papers matching a query.
        
        Note: bioRxiv API doesn't have direct keyword search, so we use
        the details endpoint to get recent papers and filter by keywords
        in title and abstract.
        
        Args:
            query: Search query string (keywords).
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects matching the query.
        """
        logger.info(f"Searching bioRxiv/medRxiv for: {query}")
        
        def _execute_search():
            all_results = []
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            # Search both servers
            for server in ["biorxiv", "medrxiv"]:
                try:
                    server_results = self._search_server_by_keywords(server, query_words, limit)
                    all_results.extend(server_results)
                    logger.debug(f"Found {len(server_results)} results from {server}")
                except Exception as e:
                    logger.warning(f"Search failed for {server}: {e}")
                    continue
            
            # Limit total results
            if len(all_results) > limit:
                all_results = all_results[:limit]
            
            return all_results
        
        # Use common retry logic from base class
        results = self._execute_with_retry(
            _execute_search,
            "search",
            "biorxiv",
            handle_rate_limit=True
        )
        
        logger.info(f"Found {len(results)} total results from bioRxiv/medRxiv")
        
        # Log detailed statistics
        pdfs_count = sum(1 for r in results if r.pdf_url)
        dois_count = sum(1 for r in results if r.doi)
        logger.debug(f"bioRxiv/medRxiv search completed: {len(results)} results, {pdfs_count} with PDFs, {dois_count} with DOIs")
        
        return results
    
    def _search_server_by_keywords(self, server: str, query_words: set, limit: int) -> List[SearchResult]:
        """Search a specific server by keywords in recent papers.
        
        Args:
            server: "biorxiv" or "medrxiv".
            query_words: Set of query words to match.
            limit: Maximum results to return.
            
        Returns:
            List of SearchResult objects.
        """
        # Get recent papers (last year) and filter by keywords
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        url = f"{self.BASE_URL}/details/{server}/{start_date}/{end_date}/0"
        results = []
        
        try:
            response = requests.get(
                url,
                timeout=self.config.timeout,
                headers={"User-Agent": self.config.user_agent}
            )
            
            if response.status_code != 200:
                return results
            
            data = response.json()
            collection = data.get("collection", [])
            
            if not collection:
                return results
            
            # Filter papers by keyword matching in title/abstract
            for paper in collection:
                if len(results) >= limit:
                    break
                
                title = paper.get("title", "").lower()
                abstract = paper.get("abstract", "").lower()
                text = f"{title} {abstract}"
                
                # Check if any query words appear in title/abstract
                text_words = set(text.split())
                matches = query_words & text_words
                
                if matches:
                    # Build result
                    biorxiv_doi = paper.get("doi", "")
                    pdf_url = f"https://www.{server}.org/content/{biorxiv_doi}.full.pdf" if biorxiv_doi else None
                    
                    authors_str = paper.get("authors", "")
                    authors = [a.strip() for a in authors_str.split(";")] if authors_str else []
                    
                    date_str = paper.get("date", "")
                    year = int(date_str[:4]) if date_str and len(date_str) >= 4 else None
                    
                    results.append(SearchResult(
                        title=paper.get("title", ""),
                        authors=authors,
                        year=year,
                        abstract=paper.get("abstract", ""),
                        url=f"https://www.{server}.org/content/{biorxiv_doi}" if biorxiv_doi else "",
                        doi=biorxiv_doi,
                        source=server,
                        pdf_url=pdf_url,
                        venue=f"{server} preprint"
                    ))
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"{server} keyword search failed: {e}")
            return []
        except Exception as e:
            logger.debug(f"{server} keyword search error: {e}")
            return []
    
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
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Use the details endpoint
        url = f"{self.BASE_URL}/details/{server}/{start_date}/{end_date}/0"
        
        try:
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
                similarity = title_similarity(title, paper_title)
                
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

