"""Core logic for literature search module."""
from __future__ import annotations

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
