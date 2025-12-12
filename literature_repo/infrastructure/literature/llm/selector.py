"""Paper selection and filtering functionality.

This module provides tools for selecting and filtering papers from the literature
library based on various criteria specified in a YAML configuration file.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import yaml

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.library.index import LibraryEntry

logger = get_logger(__name__)


@dataclass
class PaperSelectionConfig:
    """Configuration for paper selection criteria.

    Attributes:
        citation_keys: List of specific citation keys to select.
        years: Year range filter with min/max.
        sources: List of sources to include (arxiv, semanticscholar, etc.).
        has_pdf: Whether to require PDFs (True/False/None for any).
        has_summary: Whether to require summaries (True/False/None for any).
        keywords: List of keywords that must appear in title or abstract.
        limit: Maximum number of papers to select.
    """
    citation_keys: List[str] = field(default_factory=list)
    years: Dict[str, Optional[int]] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    has_pdf: Optional[bool] = None
    has_summary: Optional[bool] = None
    keywords: List[str] = field(default_factory=list)
    limit: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PaperSelectionConfig:
        """Create configuration from dictionary."""
        selection_data = data.get("selection", {})

        # Handle years field
        years_data = selection_data.get("years", {})
        years = {}
        if "min" in years_data:
            years["min"] = years_data["min"]
        if "max" in years_data:
            years["max"] = years_data["max"]

        return cls(
            citation_keys=selection_data.get("citation_keys", []),
            years=years,
            sources=selection_data.get("sources", []),
            has_pdf=selection_data.get("has_pdf"),
            has_summary=selection_data.get("has_summary"),
            keywords=selection_data.get("keywords", []),
            limit=selection_data.get("limit")
        )


class PaperSelector:
    """Handles selection and filtering of papers from the literature library.

    Provides flexible filtering based on various criteria including citation keys,
    years, sources, PDF availability, summary availability, and keyword matching.
    """

    def __init__(self, config: PaperSelectionConfig):
        """Initialize paper selector with configuration.

        Args:
            config: Selection criteria configuration.
        """
        self.config = config

    @classmethod
    def from_config(cls, config_path: Path) -> PaperSelector:
        """Create paper selector from YAML configuration file.

        Args:
            config_path: Path to YAML configuration file.

        Returns:
            Configured PaperSelector instance.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Paper selection config not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                # Handle empty file (yaml.safe_load returns None)
                data = data or {}
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in paper selection config: {e}")
            raise

        config = PaperSelectionConfig.from_dict(data)
        logger.info(f"Loaded paper selection config from {config_path}")
        return cls(config)

    def select_papers(self, library_entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """Select papers from library based on configured criteria.

        Applies all configured filters in sequence. Papers must pass ALL filters.

        Args:
            library_entries: List of all library entries to filter.

        Returns:
            Filtered list of library entries matching all criteria.
        """
        selected = library_entries.copy()
        logger.debug(f"Starting with {len(selected)} papers")

        # Apply citation key filter (if specified)
        if self.config.citation_keys:
            selected = self._filter_by_citation_keys(selected)
            logger.debug(f"After citation key filter: {len(selected)} papers")

        # Apply year range filter
        if self.config.years:
            selected = self._filter_by_years(selected)
            logger.debug(f"After year filter: {len(selected)} papers")

        # Apply source filter
        if self.config.sources:
            selected = self._filter_by_sources(selected)
            logger.debug(f"After source filter: {len(selected)} papers")

        # Apply PDF availability filter
        if self.config.has_pdf is not None:
            selected = self._filter_by_pdf_availability(selected)
            logger.debug(f"After PDF filter: {len(selected)} papers")

        # Apply summary availability filter
        if self.config.has_summary is not None:
            selected = self._filter_by_summary_availability(selected)
            logger.debug(f"After summary filter: {len(selected)} papers")

        # Apply keyword filter
        if self.config.keywords:
            selected = self._filter_by_keywords(selected)
            logger.debug(f"After keyword filter: {len(selected)} papers")

        # Apply limit
        if self.config.limit is not None and len(selected) > self.config.limit:
            selected = selected[:self.config.limit]
            logger.debug(f"After limit ({self.config.limit}): {len(selected)} papers")

        logger.info(f"Selected {len(selected)} papers from {len(library_entries)} total")
        return selected

    def _filter_by_citation_keys(self, entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """Filter by specific citation keys."""
        citation_key_set = set(self.config.citation_keys)
        return [entry for entry in entries if entry.citation_key in citation_key_set]

    def _filter_by_years(self, entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """Filter by year range."""
        min_year = self.config.years.get("min")
        max_year = self.config.years.get("max")

        filtered = []
        for entry in entries:
            if entry.year is None:
                continue  # Skip entries without year

            if min_year is not None and entry.year < min_year:
                continue
            if max_year is not None and entry.year > max_year:
                continue

            filtered.append(entry)

        return filtered

    def _filter_by_sources(self, entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """Filter by source (arxiv, semanticscholar, etc.)."""
        source_set = set(self.config.sources)
        return [entry for entry in entries if entry.source in source_set]

    def _filter_by_pdf_availability(self, entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """Filter by PDF availability."""
        def has_pdf(entry: LibraryEntry) -> bool:
            if not entry.pdf_path:
                return False
            pdf_path = Path(entry.pdf_path)
            if not pdf_path.is_absolute():
                pdf_path = Path("literature") / pdf_path
            return pdf_path.exists()

        if self.config.has_pdf:
            return [entry for entry in entries if has_pdf(entry)]
        else:
            return [entry for entry in entries if not has_pdf(entry)]

    def _filter_by_summary_availability(self, entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """Filter by summary availability."""
        def has_summary(entry: LibraryEntry) -> bool:
            summary_path = Path("data/summaries") / f"{entry.citation_key}_summary.md"
            return summary_path.exists()

        if self.config.has_summary:
            return [entry for entry in entries if has_summary(entry)]
        else:
            return [entry for entry in entries if not has_summary(entry)]

    def _filter_by_keywords(self, entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """Filter by keywords in title or abstract."""
        def matches_keywords(entry: LibraryEntry) -> bool:
            text_to_search = (entry.title or "").lower() + " " + (entry.abstract or "").lower()

            for keyword in self.config.keywords:
                # Use word boundary at start for matching (allows word continuation)
                pattern = r'\b' + re.escape(keyword.lower())
                if not re.search(pattern, text_to_search):
                    return False
            return True

        return [entry for entry in entries if matches_keywords(entry)]

    def get_selection_summary(self, selected: List[LibraryEntry], total: int) -> Dict[str, Any]:
        """Get summary statistics of the selection process.

        Args:
            selected: The selected papers.
            total: Total number of papers in the library.

        Returns:
            Dictionary with selection statistics.
        """
        return {
            "total_papers": total,
            "selected_papers": len(selected),
            "selection_rate": (len(selected) / total * 100) if total > 0 else 0,
            "filters_applied": {
                "citation_keys": len(self.config.citation_keys) > 0,
                "years": bool(self.config.years),
                "sources": len(self.config.sources) > 0,
                "has_pdf": self.config.has_pdf is not None,
                "has_summary": self.config.has_summary is not None,
                "keywords": len(self.config.keywords) > 0,
                "limit": self.config.limit is not None
            }
        }

