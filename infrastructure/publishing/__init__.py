"""Publishing module - Academic publishing & dissemination tools.

This module contains utilities for academic publishing workflows, DOI management,
citation generation, and publishing to academic platforms.

Modules:
    citations: Citation format generation (APA, MLA, BibTeX)
    metadata: Publication metadata extraction and management
    models: Data models (PublicationMetadata, CitationStyle)
    package: Publication package creation, checklists, and readiness validation
    platforms: Academic platform integrations (Zenodo, arXiv, GitHub)
    api: API clients for Zenodo, arXiv, GitHub
"""

from __future__ import annotations

from .api import ZenodoClient, ZenodoConfig
from .citations import (
    extract_citations_from_markdown,
    generate_citation_apa,
    generate_citation_bibtex,
    generate_citation_mla,
    generate_citations_markdown,
)
from .metadata import (
    calculate_complexity_score,
    create_academic_profile_data,
    create_repository_metadata,
    extract_publication_metadata,
    generate_publication_metrics,
    generate_publication_summary,
    validate_doi,
)
from .models import CitationStyle, PublicationMetadata
from .package import (
    create_publication_announcement,
    create_publication_package,
    create_submission_checklist,
    generate_doi_badge,
    validate_publication_readiness,
)
from .platforms import (
    create_github_release,
    prepare_arxiv_submission,
    publish_to_zenodo,
)

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
    "calculate_complexity_score",
    # Dissemination
    "publish_to_zenodo",
    "prepare_arxiv_submission",
    "create_github_release",
]
