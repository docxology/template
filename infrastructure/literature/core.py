"""Core logic for literature search module."""
from __future__ import annotations

from typing import List, Optional, Dict
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

logger = get_logger(__name__)


class LiteratureSearch:
    """Main entry point for literature search functionality."""

    def __init__(self, config: Optional[LiteratureConfig] = None):
        self.config = config or LiteratureConfig.from_env()
        self.sources: Dict[str, LiteratureSource] = {
            "arxiv": ArxivSource(self.config),
            "semanticscholar": SemanticScholarSource(self.config)
        }
        self.pdf_handler = PDFHandler(self.config)
        self.reference_manager = ReferenceManager(self.config)

    def search(self, query: str, limit: int = 10, sources: Optional[List[str]] = None) -> List[SearchResult]:
        """Search for papers across enabled sources.
        
        Args:
            query: Search query
            limit: Maximum results per source
            sources: List of sources to use (default: all enabled)
            
        Returns:
            Combined list of search results
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
            except Exception as e:
                logger.error(f"Search failed for source {source_name}: {e}")
                
        # Deduplicate by DOI or Title
        return self._deduplicate_results(results)

    def download_paper(self, result: SearchResult) -> Optional[Path]:
        """Download PDF for a search result."""
        if not result.pdf_url:
            logger.warning(f"No PDF URL for paper: {result.title}")
            return None
            
        return self.pdf_handler.download_pdf(result.pdf_url)

    def add_to_library(self, result: SearchResult) -> str:
        """Add paper to local library (BibTeX)."""
        return self.reference_manager.add_reference(result)

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on DOI or normalized title."""
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

