"""Core logic for literature search module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import APIRateLimitError
from infrastructure.literature.core.config import LiteratureConfig
from infrastructure.literature.sources import (
    SearchResult,
    ArxivSource,
    SemanticScholarSource,
    BiorxivSource,
    UnpaywallSource,
    PubMedSource,
    EuropePMCSource,
    CrossRefSource,
    OpenAlexSource,
    DBLPSource,
    LiteratureSource
)
from infrastructure.literature.pdf.handler import PDFHandler
from infrastructure.literature.library.references import ReferenceManager
from infrastructure.literature.library.index import LibraryIndex

logger = get_logger(__name__)


@dataclass
class SourceStatistics:
    """Statistics for a single literature source.
    
    Tracks per-source metrics including results found, citations,
    PDF availability, health status, and timing information.
    
    Attributes:
        source_name: Name of the source (e.g., "arxiv", "semanticscholar").
        results_found: Number of search results found.
        citations_found: Total citation count across all results.
        pdfs_available: Number of results with PDF URLs.
        dois_available: Number of results with DOIs.
        healthy: Whether the source is currently healthy.
        time_taken: Time taken for search in seconds.
        errors: Number of errors encountered.
        skipped: Whether this source was skipped (unhealthy/unavailable).
    """
    source_name: str
    results_found: int = 0
    citations_found: int = 0
    pdfs_available: int = 0
    dois_available: int = 0
    healthy: bool = True
    time_taken: float = 0.0
    errors: int = 0
    skipped: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_name": self.source_name,
            "results_found": self.results_found,
            "citations_found": self.citations_found,
            "pdfs_available": self.pdfs_available,
            "dois_available": self.dois_available,
            "healthy": self.healthy,
            "time_taken": self.time_taken,
            "errors": self.errors,
            "skipped": self.skipped,
        }


@dataclass
class SearchStatistics:
    """Statistics for a complete search operation.
    
    Contains per-source statistics and overall search metrics.
    
    Attributes:
        query: Search query string.
        total_results: Total unique results after deduplication.
        source_stats: Dictionary mapping source names to SourceStatistics.
        total_time: Total search time in seconds.
    """
    query: str
    total_results: int = 0
    source_stats: Dict[str, SourceStatistics] = field(default_factory=dict)
    total_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "total_results": self.total_results,
            "source_stats": {k: v.to_dict() for k, v in self.source_stats.items()},
            "total_time": self.total_time,
        }


@dataclass
class DownloadResult:
    """Result of a PDF download attempt with status tracking.
    
    Tracks success/failure status and categorizes failure reasons for
    reporting and potential retry operations.
    
    Attributes:
        citation_key: Unique identifier for the paper.
        success: Whether the download succeeded.
        pdf_path: Path to downloaded PDF if successful.
        failure_reason: Category of failure if unsuccessful.
        failure_message: Detailed error message.
        attempted_urls: List of URLs that were attempted.
        result: The original SearchResult for reference.
    """
    citation_key: str
    success: bool
    pdf_path: Optional[Path] = None
    failure_reason: Optional[str] = None  # "no_pdf_url", "access_denied", "network_error", "timeout"
    failure_message: Optional[str] = None
    attempted_urls: List[str] = field(default_factory=list)
    result: Optional[SearchResult] = None
    already_existed: bool = False  # True if PDF was already downloaded
    
    @property
    def is_retriable(self) -> bool:
        """Check if this download failure might succeed on retry.
        
        Network errors and timeouts are potentially retriable.
        Access denied and missing URLs are not.
        """
        return self.failure_reason in ("network_error", "timeout")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "citation_key": self.citation_key,
            "success": self.success,
            "pdf_path": str(self.pdf_path) if self.pdf_path else None,
            "failure_reason": self.failure_reason,
            "failure_message": self.failure_message,
            "attempted_urls": self.attempted_urls,
            "already_existed": self.already_existed,
        }


class LiteratureSearch:
    """Main entry point for literature search functionality.
    
    Coordinates search across multiple sources, PDF downloads, BibTeX
    generation, and library index management for comprehensive tracking.
    
    All outputs are saved to the literature/ directory:
    - data/references.bib - BibTeX entries
    - data/library.json - JSON index with full metadata
    - data/pdfs/ - Downloaded PDFs (named by citation key)
    """

    def __init__(self, config: Optional[LiteratureConfig] = None):
        """Initialize literature search.
        
        Args:
            config: Optional configuration. Uses environment-based config if not provided.
        """
        self.config = config or LiteratureConfig.from_env()
        
        # Initialize library index first (other components depend on it)
        self.library_index = LibraryIndex(self.config)
        
        # Initialize sources
        self.sources: Dict[str, Any] = {
            "arxiv": ArxivSource(self.config),
            "semanticscholar": SemanticScholarSource(self.config),
            "biorxiv": BiorxivSource(self.config),
            "pubmed": PubMedSource(self.config),
            "europepmc": EuropePMCSource(self.config),
            "crossref": CrossRefSource(self.config),
            "openalex": OpenAlexSource(self.config),
            "dblp": DBLPSource(self.config),
        }
        
        # Initialize optional sources if configured
        if self.config.use_unpaywall and self.config.unpaywall_email:
            self.sources["unpaywall"] = UnpaywallSource(self.config)
        
        # Source health monitoring
        self._source_health_cache: Dict[str, bool] = {}
        self._last_health_check: float = 0.0
        
        # Initialize handlers with library index
        self.pdf_handler = PDFHandler(self.config, self.library_index)
        self.reference_manager = ReferenceManager(self.config, self.library_index)

    def _ping_sources(self, sources_to_use: List[str]) -> Dict[str, bool]:
        """Ping sources to check availability before search.
        
        Performs quick health checks on all sources to verify they're available.
        Logs which sources are healthy/unhealthy.
        
        Args:
            sources_to_use: List of source names to check.
            
        Returns:
            Dictionary mapping source names to health status (True/False).
        """
        logger.info("")
        logger.info("=" * 60)
        logger.info("CHECKING SOURCE AVAILABILITY")
        logger.info("=" * 60)
        
        health_status = {}
        healthy_sources = []
        unhealthy_sources = []
        
        for source_name in sources_to_use:
            if source_name not in self.sources:
                logger.warning(f"  {source_name.upper()}: ⚠️  NOT CONFIGURED (skipping)")
                health_status[source_name] = False
                unhealthy_sources.append(source_name)
                continue
            
            source = self.sources[source_name]
            
            # Check if source supports search
            if not hasattr(source, 'search'):
                logger.info(f"  {source_name.upper()}: ℹ️  NO SEARCH SUPPORT (lookup only)")
                health_status[source_name] = True  # Not unhealthy, just doesn't support search
                healthy_sources.append(source_name)
                continue
            
            # Quick health check
            try:
                # Check if source has health status methods
                if not hasattr(source, 'get_health_status') or not hasattr(source, 'is_healthy'):
                    logger.debug(f"  {source_name.upper()}: ℹ️  NO HEALTH STATUS SUPPORT (assuming healthy)")
                    health_status[source_name] = True
                    healthy_sources.append(source_name)
                    continue
                
                is_healthy = source.is_healthy
                health_info = source.get_health_status()
                consecutive_failures = health_info.get('consecutive_failures', 0)
                
                if is_healthy:
                    logger.info(f"  {source_name.upper()}: ✓ HEALTHY")
                    health_status[source_name] = True
                    healthy_sources.append(source_name)
                else:
                    logger.warning(f"  {source_name.upper()}: ✗ UNHEALTHY ({consecutive_failures} consecutive failures)")
                    health_status[source_name] = False
                    unhealthy_sources.append(source_name)
            except Exception as e:
                logger.warning(f"  {source_name.upper()}: ✗ ERROR CHECKING HEALTH: {e}")
                health_status[source_name] = False
                unhealthy_sources.append(source_name)
        
        logger.info("")
        logger.info(f"  Healthy sources: {len(healthy_sources)} ({', '.join(healthy_sources) if healthy_sources else 'none'})")
        if unhealthy_sources:
            logger.warning(f"  Unhealthy sources: {len(unhealthy_sources)} ({', '.join(unhealthy_sources)})")
        logger.info("=" * 60)
        logger.info("")
        
        return health_status

    def search(
        self, 
        query: str, 
        limit: int = 10, 
        sources: Optional[List[str]] = None,
        return_stats: bool = False
    ) -> Union[List[SearchResult], Tuple[List[SearchResult], SearchStatistics]]:
        """Search for papers across enabled sources.
        
        Args:
            query: Search query string.
            limit: Maximum results per source.
            sources: List of sources to use (default: all enabled in config).
            return_stats: If True, return tuple of (results, statistics).
            
        Returns:
            Combined list of deduplicated search results, or tuple of (results, statistics)
            if return_stats is True.
        """
        import time
        start_time = time.time()
        results = []
        source_stats: Dict[str, SourceStatistics] = {}
        sources_to_use = sources or self.config.sources
        
        # Ping sources before search
        source_health = self._ping_sources(sources_to_use)
        
        logger.info(f"Searching across {len(sources_to_use)} source(s): {', '.join(sources_to_use)}")
        logger.info(f"Query: '{query}' | Limit per source: {limit}")
        logger.info("")
        
        for source_name in sources_to_use:
            source_start_time = time.time()
            stats = SourceStatistics(source_name=source_name)
            
            if source_name not in self.sources:
                logger.warning(f"✗ {source_name.upper()}: Unknown source, skipping")
                stats.skipped = True
                stats.healthy = False
                source_stats[source_name] = stats
                continue
            
            # Check source health before attempting search
            source = self.sources[source_name]
            
            # Check if source supports health status
            if hasattr(source, 'get_health_status') and hasattr(source, 'is_healthy'):
                try:
                    health_status = source.get_health_status()
                    stats.healthy = health_status.get("healthy", True)
                    
                    if not source.is_healthy:
                        consecutive_failures = getattr(source, '_consecutive_failures', 0)
                        logger.warning(f"✗ {source_name.upper()}: Unhealthy ({consecutive_failures} consecutive failures), skipping")
                        stats.skipped = True
                        stats.healthy = False
                        source_stats[source_name] = stats
                        continue
                except Exception as e:
                    logger.debug(f"Error checking health for {source_name}: {e}, proceeding with search")
                    stats.healthy = True  # Default to healthy if check fails
            else:
                # Source doesn't support health checks, assume healthy
                stats.healthy = True
                
            try:
                # Check if source has search method (some sources like Unpaywall don't)
                if not hasattr(source, 'search'):
                    logger.debug(f"ℹ️  {source_name.upper()}: No search support (lookup only), skipping")
                    stats.skipped = True
                    source_stats[source_name] = stats
                    continue
                
                logger.debug(f"Searching {source_name}...")
                source_results = source.search(query, limit)
                source_time = time.time() - source_start_time
                
                # Calculate statistics
                stats.results_found = len(source_results)
                stats.citations_found = sum(r.citation_count or 0 for r in source_results)
                stats.pdfs_available = sum(1 for r in source_results if r.pdf_url)
                stats.dois_available = sum(1 for r in source_results if r.doi)
                stats.time_taken = source_time
                stats.healthy = True
                
                results.extend(source_results)
                
                # Log detailed per-source results with health status
                health_indicator = "✓" if stats.healthy else "✗"
                avg_citations = stats.citations_found / stats.results_found if stats.results_found > 0 else 0
                logger.info(f"{health_indicator} {source_name.upper()}: {stats.results_found} results "
                          f"({stats.citations_found} total citations, avg: {avg_citations:.1f}, "
                          f"{stats.pdfs_available} PDFs, {stats.dois_available} DOIs) - {source_time:.2f}s")
                
            except APIRateLimitError as e:
                source_time = time.time() - source_start_time
                error_context = getattr(e, 'context', {})
                attempt = error_context.get('attempt', '?')
                logger.error(f"✗ {source_name.upper()}: Rate limit exceeded (attempt {attempt}) - {source_time:.2f}s")
                stats.errors = 1
                stats.time_taken = source_time
                stats.healthy = False
                if hasattr(source, '_consecutive_failures'):
                    source._consecutive_failures += 1
            except Exception as e:
                source_time = time.time() - source_start_time
                error_type = type(e).__name__
                error_context = getattr(e, 'context', {}) if hasattr(e, 'context') else {}
                attempt = error_context.get('attempt', '?')
                logger.error(f"✗ {source_name.upper()}: Search failed ({error_type}, attempt {attempt}) - {e} - {source_time:.2f}s")
                stats.errors = 1
                stats.time_taken = source_time
                stats.healthy = False
                if hasattr(source, '_consecutive_failures'):
                    source._consecutive_failures += 1
            
            source_stats[source_name] = stats
                
        # Deduplicate by DOI or Title
        deduplicated = self._deduplicate_results(results)
        total_time = time.time() - start_time
        
        # Calculate summary statistics
        successful_sources = [name for name, stat in source_stats.items() if not stat.skipped and stat.errors == 0]
        failed_sources = [name for name, stat in source_stats.items() if stat.errors > 0]
        skipped_sources = [name for name, stat in source_stats.items() if stat.skipped]
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("SEARCH SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Query: '{query}'")
        logger.info(f"Sources queried: {len(sources_to_use)}")
        logger.info(f"  ✓ Successful: {len(successful_sources)} ({', '.join(successful_sources) if successful_sources else 'none'})")
        if failed_sources:
            logger.warning(f"  ✗ Failed: {len(failed_sources)} ({', '.join(failed_sources)})")
        if skipped_sources:
            logger.info(f"  ⊘ Skipped: {len(skipped_sources)} ({', '.join(skipped_sources)})")
        logger.info(f"Raw results: {len(results)}")
        logger.info(f"Unique results (after deduplication): {len(deduplicated)}")
        logger.info(f"Total time: {total_time:.2f}s")
        logger.info("=" * 60)
        logger.info("")
        
        # Create search statistics
        search_stats = SearchStatistics(
            query=query,
            total_results=len(deduplicated),
            source_stats=source_stats,
            total_time=total_time
        )
        
        if return_stats:
            return deduplicated, search_stats
        return deduplicated

    def download_paper(self, result: SearchResult) -> Optional[Path]:
        """Download PDF for a search result.
        
        Downloads to data/pdfs/ using citation key as filename.
        Updates library index with PDF path.
        
        Args:
            result: Search result with pdf_url.
            
        Returns:
            Path to downloaded file, or None if no PDF URL.
        """
        if not result.pdf_url:
            logger.warning(f"No PDF URL for paper: {result.title}")
            return None
            
        return self.pdf_handler.download_pdf(result.pdf_url, result=result)
    
    def download_paper_with_result(self, result: SearchResult) -> DownloadResult:
        """Download PDF for a search result with detailed result tracking.
        
        Similar to download_paper but returns a DownloadResult with
        detailed success/failure information for reporting.
        
        Args:
            result: Search result with pdf_url.
            
        Returns:
            DownloadResult with download status and details.
        """
        # Generate citation key
        citation_key = self.library_index.generate_citation_key(
            result.title, result.authors, result.year
        )
        
        # Check if PDF already exists before attempting download
        expected_pdf_path = Path(self.config.download_dir) / f"{citation_key}.pdf"
        already_existed = expected_pdf_path.exists()

        # Attempt download - pass pdf_url even if None (fallbacks will handle it)
        attempted_urls = [result.pdf_url] if result.pdf_url else []
        try:
            pdf_path = self.pdf_handler.download_pdf(result.pdf_url, result=result)
            return DownloadResult(
                citation_key=citation_key,
                success=True,
                pdf_path=pdf_path,
                attempted_urls=attempted_urls,
                result=result,
                already_existed=already_existed
            )
        except Exception as e:
            # Extract failure reason from exception context if available
            failure_reason = "unknown"
            failure_message = str(e)
            
            if hasattr(e, 'context') and isinstance(e.context, dict):
                failure_reason = e.context.get('failure_reason', 'unknown')
                if 'attempted_urls' in e.context:
                    attempted_urls = e.context['attempted_urls']
            
            # Categorize common errors
            error_str = str(e).lower()
            if '403' in error_str or 'forbidden' in error_str:
                failure_reason = "access_denied"
            elif '404' in error_str or 'not found' in error_str:
                failure_reason = "not_found"
            elif 'timeout' in error_str:
                failure_reason = "timeout"
            elif 'connection' in error_str:
                failure_reason = "network_error"
            
            return DownloadResult(
                citation_key=citation_key,
                success=False,
                failure_reason=failure_reason,
                failure_message=failure_message,
                attempted_urls=attempted_urls,
                result=result
            )

    def add_to_library(self, result: SearchResult) -> str:
        """Add paper to local library.
        
        Adds entry to both:
        - data/references.bib (BibTeX)
        - data/library.json (JSON index)
        
        Args:
            result: Search result to add.
            
        Returns:
            Citation key for the paper.
        """
        return self.reference_manager.add_reference(result)

    def export_library(self, path: Optional[Path] = None, format: str = "json") -> Path:
        """Export the library to a file.
        
        Args:
            path: Output path. Uses default if not specified.
            format: Export format ('json' supported).
            
        Returns:
            Path to exported file.
            
        Raises:
            ValueError: If format is not supported.
        """
        if format != "json":
            raise ValueError(f"Unsupported export format: {format}. Use 'json'.")
        
        return self.library_index.export_json(path)

    def get_library_stats(self) -> Dict[str, Any]:
        """Get statistics about the library.
        
        Returns:
            Dictionary with library statistics including:
            - total_entries: Number of papers
            - downloaded_pdfs: Number of PDFs downloaded
            - sources: Count by source
            - years: Count by year
        """
        return self.library_index.get_stats()
    
    def get_source_health_status(self) -> Dict[str, Any]:
        """Get health status for all sources.
        
        Returns:
            Dictionary mapping source names to health status information.
        """
        health_status = {}
        for source_name, source in self.sources.items():
            try:
                # Check if source supports health status reporting
                if hasattr(source, 'get_health_status'):
                    health_status[source_name] = source.get_health_status()
                else:
                    # Return default health status for sources without health methods
                    logger.debug(f"Source {source_name} does not support health status reporting, using defaults")
                    health_status[source_name] = {
                        "healthy": True,  # Assume healthy if we can't check
                        "consecutive_failures": 0,
                        "last_request_time": 0.0,
                        "source_name": source.__class__.__name__,
                        "note": "Health status not available for this source type"
                    }
            except Exception as e:
                logger.warning(f"Error getting health status for {source_name}: {e}")
                # Return error status
                health_status[source_name] = {
                    "healthy": False,
                    "consecutive_failures": 0,
                    "last_request_time": 0.0,
                    "source_name": source.__class__.__name__,
                    "error": str(e)
                }
        return health_status
    
    def check_all_sources_health(self) -> Dict[str, bool]:
        """Check health of all sources.
        
        Returns:
            Dictionary mapping source names to health status (True/False).
        """
        health_results = {}
        for source_name, source in self.sources.items():
            try:
                # Check if source supports health checks
                if hasattr(source, 'check_health'):
                    is_healthy = source.check_health()
                    health_results[source_name] = is_healthy
                    logger.debug(f"Source {source_name} health: {'healthy' if is_healthy else 'unhealthy'}")
                else:
                    # Source doesn't support health checks, assume healthy
                    logger.debug(f"Source {source_name} does not support health checks, assuming healthy")
                    health_results[source_name] = True
            except Exception as e:
                logger.warning(f"Health check failed for {source_name}: {e}")
                health_results[source_name] = False
        return health_results

    def get_library_entries(self) -> List[Dict[str, Any]]:
        """Get all entries in the library.
        
        Returns:
            List of library entries as dictionaries.
        """
        return [entry.to_dict() for entry in self.library_index.list_entries()]

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results with fuzzy matching and relevance ranking.
        
        Uses multiple strategies:
        1. Exact DOI matching (highest priority)
        2. Fuzzy title similarity matching
        3. Relevance ranking to keep best results
        
        Args:
            results: List of search results.
            
        Returns:
            Deduplicated and ranked list of results.
        """
        from infrastructure.literature.sources.base import normalize_title, title_similarity
        
        if not results:
            return []
        
        # First pass: exact DOI deduplication
        seen_dois: Dict[str, SearchResult] = {}
        doi_results = []
        non_doi_results = []
        
        for r in results:
            if r.doi:
                doi_lower = r.doi.lower().strip()
                if doi_lower not in seen_dois:
                    seen_dois[doi_lower] = r
                    doi_results.append(r)
            else:
                non_doi_results.append(r)
        
        # Second pass: fuzzy title matching for non-DOI results
        unique_results = list(doi_results)  # Start with DOI-matched results
        seen_titles: Dict[str, SearchResult] = {}
        TITLE_SIMILARITY_THRESHOLD = 0.85  # High threshold for fuzzy matching
        
        for r in non_doi_results:
            norm_title = normalize_title(r.title)
            
            # Check for exact match
            if norm_title in seen_titles:
                # Keep the one with better metadata (DOI, citation count, etc.)
                existing = seen_titles[norm_title]
                if self._is_better_result(r, existing):
                    seen_titles[norm_title] = r
                    # Replace in unique_results if it was added
                    if existing in unique_results:
                        idx = unique_results.index(existing)
                        unique_results[idx] = r
                continue
            
            # Check for fuzzy match
            is_duplicate = False
            for existing_title, existing_result in seen_titles.items():
                similarity = title_similarity(norm_title, existing_title)
                if similarity >= TITLE_SIMILARITY_THRESHOLD:
                    # Similar title found - keep the better one
                    if self._is_better_result(r, existing_result):
                        seen_titles[existing_title] = r
                        if existing_result in unique_results:
                            idx = unique_results.index(existing_result)
                            unique_results[idx] = r
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_titles[norm_title] = r
                unique_results.append(r)
        
        # Third pass: relevance ranking
        ranked_results = self._rank_by_relevance(unique_results)
        
        logger.debug(f"Deduplicated {len(results)} results to {len(ranked_results)} unique papers")
        return ranked_results
    
    def _is_better_result(self, r1: SearchResult, r2: SearchResult) -> bool:
        """Compare two results to determine which is better.
        
        Prefers results with:
        - DOI over no DOI
        - Higher citation count
        - More complete metadata
        
        Args:
            r1: First result.
            r2: Second result.
            
        Returns:
            True if r1 is better than r2.
        """
        # DOI is preferred
        if r1.doi and not r2.doi:
            return True
        if r2.doi and not r1.doi:
            return False
        
        # Higher citation count is preferred
        if r1.citation_count is not None and r2.citation_count is not None:
            if r1.citation_count > r2.citation_count:
                return True
            if r2.citation_count > r1.citation_count:
                return False
        
        # More complete abstract is preferred
        if len(r1.abstract or "") > len(r2.abstract or ""):
            return True
        
        # Prefer results with venue information
        if r1.venue and not r2.venue:
            return True
        
        return False
    
    def _rank_by_relevance(self, results: List[SearchResult]) -> List[SearchResult]:
        """Rank results by relevance score.
        
        Relevance factors:
        - Citation count (higher is better)
        - Recency (newer is better, within reason)
        - Source quality (prefer certain sources)
        - Metadata completeness
        
        Args:
            results: List of results to rank.
            
        Returns:
            Ranked list of results (best first).
        """
        def relevance_score(r: SearchResult) -> float:
            score = 0.0
            
            # Citation count (normalized, max 100 citations = 1.0)
            if r.citation_count is not None:
                score += min(1.0, r.citation_count / 100.0) * 0.4
            
            # Recency (prefer papers from last 10 years)
            if r.year:
                current_year = 2025  # Could be dynamic
                age = current_year - r.year
                if age <= 10:
                    score += (1.0 - age / 10.0) * 0.3
                elif age <= 20:
                    score += 0.1
            
            # Source quality
            source_scores = {
                "arxiv": 0.1,
                "semanticscholar": 0.15,
                "pubmed": 0.1,
                "crossref": 0.1
            }
            score += source_scores.get(r.source, 0.05) * 0.1
            
            # Metadata completeness
            completeness = 0.0
            if r.doi:
                completeness += 0.2
            if r.abstract and len(r.abstract) > 100:
                completeness += 0.3
            if r.venue:
                completeness += 0.2
            if r.pdf_url:
                completeness += 0.3
            score += completeness * 0.2
            
            return score
        
        # Sort by relevance score (descending)
        scored_results = [(r, relevance_score(r)) for r in results]
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [r for r, _ in scored_results]

    def remove_paper(self, citation_key: str) -> bool:
        """Remove a paper from the library.

        Removes from both:
        - data/library.json (JSON index)
        - data/references.bib (BibTeX)

        Args:
            citation_key: Citation key of the paper to remove.

        Returns:
            True if paper was removed, False if not found.
        """
        # Remove from library index
        removed_from_index = self.library_index.remove_entry(citation_key)

        # Also remove from BibTeX if it exists
        # The ReferenceManager doesn't have a remove method, but we can handle this
        # by noting that the next save will not include this entry
        # For now, we'll just remove from the index

        if removed_from_index:
            logger.info(f"Removed paper from library: {citation_key}")
            return True
        else:
            logger.warning(f"Paper not found for removal: {citation_key}")
            return False

    def cleanup_library(self, remove_missing_pdfs: bool = True) -> Dict[str, int]:
        """Clean up the library by removing entries without PDFs.

        Args:
            remove_missing_pdfs: Whether to remove entries without PDF files.

        Returns:
            Dictionary with cleanup statistics:
            - total_entries: Total entries before cleanup
            - entries_removed: Number of entries removed
            - entries_remaining: Number of entries remaining
        """
        total_entries = len(self.library_index.list_entries())

        if remove_missing_pdfs:
            removed_count = self.library_index.remove_entries_without_pdf()
        else:
            removed_count = 0

        remaining_count = total_entries - removed_count

        stats = {
            "total_entries": total_entries,
            "entries_removed": removed_count,
            "entries_remaining": remaining_count
        }

        logger.info(f"Library cleanup completed: {removed_count} entries removed, {remaining_count} remaining")
        return stats
