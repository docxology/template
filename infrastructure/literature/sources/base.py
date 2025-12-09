"""Base classes and utilities for literature sources.

This module provides:
- SearchResult: Normalized search result dataclass
- LiteratureSource: Abstract base class for all sources
- Utility functions for title normalization and similarity
"""
from __future__ import annotations

import abc
import re
from typing import List, Optional
from dataclasses import dataclass

from infrastructure.literature.config import LiteratureConfig


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


def normalize_title(title: str) -> str:
    """Normalize a title for comparison.
    
    Removes punctuation, extra whitespace, and converts to lowercase.
    
    Args:
        title: Title string to normalize.
        
    Returns:
        Normalized title string.
    """
    # Remove punctuation and extra whitespace, convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = ' '.join(normalized.split())
    return normalized


def title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles using word overlap.
    
    Uses Jaccard similarity on word sets after normalization.
    
    Args:
        title1: First title.
        title2: Second title.
        
    Returns:
        Similarity score between 0.0 and 1.0.
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
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

