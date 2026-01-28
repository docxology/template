"""Publishing module - Academic publishing & dissemination tools.

This module contains utilities for academic publishing workflows, DOI management,
citation generation, and publishing to academic platforms.

Modules:
    core: Publishing workflow assistance and metadata management
    api: API clients for Zenodo, arXiv, GitHub
"""

from .api import ZenodoClient, ZenodoConfig
from .core import (CitationStyle, PublicationMetadata,
                   calculate_complexity_score, calculate_file_hash,
                   create_academic_profile_data, create_github_release,
                   create_publication_announcement, create_publication_package,
                   create_repository_metadata, create_submission_checklist,
                   extract_citations_from_markdown,
                   extract_publication_metadata, generate_citation_apa,
                   generate_citation_bibtex, generate_citation_mla,
                   generate_citations_markdown, generate_doi_badge,
                   generate_publication_metrics, generate_publication_summary,
                   prepare_arxiv_submission, publish_to_zenodo, validate_doi,
                   validate_publication_readiness)

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
