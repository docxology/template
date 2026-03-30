"""Data models for academic publishing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PublicationMetadata:
    """Container for publication metadata."""

    title: str
    authors: list[str]
    abstract: str
    keywords: list[str]
    doi: str | None = None
    journal: str | None = None
    conference: str | None = None
    publication_date: str | None = None
    publisher: str | None = None
    license: str = "CC-BY-4.0"
    repository_url: str | None = None
    citation_count: int = 0
    download_count: int = 0


@dataclass
class CitationStyle:
    """Container for citation style configuration."""

    name: str
    format_string: str
    example: str
