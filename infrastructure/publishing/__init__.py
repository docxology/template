"""Publishing module - Academic publishing & dissemination tools.

This module contains utilities for academic publishing workflows, DOI management,
citation generation, and publishing to academic platforms.

Modules:
    core: Publishing workflow assistance and metadata management
    api: API clients for Zenodo, arXiv, GitHub
"""

from .core import (
    PublicationMetadata,
    CitationStyle,
    extract_publication_metadata,
    validate_doi,
    generate_citation_bibtex,
    generate_citation_apa,
    generate_citation_mla,
    generate_citations_markdown,
    create_publication_package,
    create_submission_checklist,
    extract_citations_from_markdown,
    generate_publication_summary,
    create_academic_profile_data,
    generate_doi_badge,
    create_publication_announcement,
    validate_publication_readiness,
    generate_publication_metrics,
    create_repository_metadata,
    publish_to_zenodo,
    prepare_arxiv_submission,
    create_github_release,
    calculate_file_hash,
    calculate_complexity_score,
)
from .api import ZenodoClient, ZenodoConfig

__all__ = [
    # Classes
    "PublicationMetadata",
    "CitationStyle",
    "ZenodoClient",
    "ZenodoConfig",
    # Core functions
    "extract_publication_metadata",
    "validate_doi",
    "generate_citation_bibtex",
    "generate_citation_apa",
    "generate_citation_mla",
    "generate_citations_markdown",
    "create_publication_package",
    "create_submission_checklist",
    "extract_citations_from_markdown",
    "generate_publication_summary",
    "create_academic_profile_data",
    "generate_doi_badge",
    "create_publication_announcement",
    "validate_publication_readiness",
    "generate_publication_metrics",
    "create_repository_metadata",
    "calculate_file_hash",
    "calculate_complexity_score",
    # Dissemination
    "publish_to_zenodo",
    "prepare_arxiv_submission",
    "create_github_release",
]

