"""Data models for academic publishing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PublicationMetadata:
    """Container for publication metadata."""

    title: str
    authors: List[str]
    abstract: str
    keywords: List[str]
    doi: Optional[str] = None
    journal: Optional[str] = None
    conference: Optional[str] = None
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    license: str = "CC-BY-4.0"
    repository_url: Optional[str] = None
    citation_count: int = 0
    download_count: int = 0


@dataclass
class CitationStyle:
    """Container for citation style configuration."""

    name: str
    format_string: str
    example: str




