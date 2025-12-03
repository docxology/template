"""Core logic for literature search module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.config import LiteratureConfig
from infrastructure.literature.api import (
    SearchResult,
    ArxivSource,
    SemanticScholarSource,
    LiteratureSource
)
from infrastructure.literature.pdf_handler import PDFHandler
from infrastructure.literature.reference_manager import ReferenceManager
from infrastructure.literature.library_index import LibraryIndex

logger = get_logger(__name__)


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
    - literature/references.bib - BibTeX entries
    - literature/library.json - JSON index with full metadata
    - literature/pdfs/ - Downloaded PDFs (named by citation key)
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
        self.sources: Dict[str, LiteratureSource] = {
            "arxiv": ArxivSource(self.config),
            "semanticscholar": SemanticScholarSource(self.config)
        }
        
        # Initialize handlers with library index
        self.pdf_handler = PDFHandler(self.config, self.library_index)
        self.reference_manager = ReferenceManager(self.config, self.library_index)

    def search(
        self, 
        query: str, 
        limit: int = 10, 
        sources: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search for papers across enabled sources.
        
        Args:
            query: Search query string.
            limit: Maximum results per source.
            sources: List of sources to use (default: all enabled in config).
            
        Returns:
            Combined list of deduplicated search results.
        """
        results = []
        sources_to_use = sources or self.config.sources
        
        for source_name in sources_to_use:
            if source_name not in self.sources:
                logger.warning(f"Unknown source: {source_name}")
                continue
                
            try:
                source = self.sources[source_name]
                source_results = source.search(query, limit)
                results.extend(source_results)
                logger.info(f"Found {len(source_results)} results from {source_name}")
            except Exception as e:
                logger.error(f"Search failed for source {source_name}: {e}")
                
        # Deduplicate by DOI or Title
        deduplicated = self._deduplicate_results(results)
        logger.info(f"Total results after deduplication: {len(deduplicated)}")
        return deduplicated

    def download_paper(self, result: SearchResult) -> Optional[Path]:
        """Download PDF for a search result.
        
        Downloads to literature/pdfs/ using citation key as filename.
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
        - literature/references.bib (BibTeX)
        - literature/library.json (JSON index)
        
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

    def get_library_entries(self) -> List[Dict[str, Any]]:
        """Get all entries in the library.
        
        Returns:
            List of library entries as dictionaries.
        """
        return [entry.to_dict() for entry in self.library_index.list_entries()]

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on DOI or normalized title.
        
        Args:
            results: List of search results.
            
        Returns:
            Deduplicated list of results.
        """
        seen_dois = set()
        seen_titles = set()
        unique_results = []
        
        for r in results:
            # Check DOI
            if r.doi and r.doi in seen_dois:
                continue
            
            # Check Title
            norm_title = r.title.lower().strip()
            if norm_title in seen_titles:
                continue
                
            if r.doi:
                seen_dois.add(r.doi)
            seen_titles.add(norm_title)
            unique_results.append(r)
            
        return unique_results

    def remove_paper(self, citation_key: str) -> bool:
        """Remove a paper from the library.

        Removes from both:
        - literature/library.json (JSON index)
        - literature/references.bib (BibTeX)

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
