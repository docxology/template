"""Data models for academic publishing."""

from dataclasses import dataclass, field


@dataclass
class AuthorRecord:
    """Structured author metadata for deposit APIs."""

    name: str
    orcid: str | None = None
    affiliation: str | None = None
    email: str | None = None


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
    author_records: list[AuthorRecord] = field(default_factory=list)
    deposit_description: str | None = None
    pdf_sha256: str | None = None
    release_tag: str | None = None
    paper_version: str | None = None
    github_release_url: str | None = None
    zenodo_description_override: str | None = None


@dataclass
class CitationStyle:
    """Container for citation style configuration."""

    name: str
    format_string: str
    example: str
