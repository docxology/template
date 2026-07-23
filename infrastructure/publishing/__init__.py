"""Publishing module - Academic publishing & dissemination tools.

This module contains utilities for academic publishing workflows, DOI management,
citation generation, and publishing to academic platforms.

Modules:
    citations: Citation format generation (APA, MLA, BibTeX)
    metadata: Publication metadata extraction and management
    models: Data models (PublicationMetadata, CitationStyle)
    package: Publication package creation, checklists, and readiness validation
    zenodo: Zenodo REST API client and publish workflow
    github: GitHub Releases API
    arxiv: arXiv submission tarball preparation
    pypi: PyPI / TestPyPI package distribution
    static_site: GitHub Pages, Cloudflare Pages, Netlify deployment
    archival: IPFS, Software Heritage, and multi-provider archival
    platforms: Backwards-compatible platform re-exports
    registry: Central platform adapter registry
    api: Backwards-compatible Zenodo re-exports
"""

from .api import ZenodoClient, ZenodoConfig
from .citations import (
    extract_citations_from_markdown,
    generate_citation_apa,
    generate_citation_bibtex,
    generate_citation_mla,
    generate_citations_markdown,
)
from .metadata import (
    calculate_metadata_complexity_score,
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
    PyPIAdapter,
    build_dist,
    upload_dist,
    check_dist,
    GitHubPagesAdapter,
    CloudflarePagesAdapter,
    NetlifyAdapter,
    get_static_site_adapter,
    SiteDeployConfig,
    SiteDeployResult,
    SiteHosting,
    archive_publication,
    load_credentials,
    ArchivalProvider,
    ArchivalReceipt,
    ArchivalRun,
)
from .registry import (
    PLATFORM_REGISTRY,
    PlatformInfo,
    PublishingTier,
    list_platforms,
    get_platform,
    first_class_platforms,
    documented_platforms,
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
    "calculate_metadata_complexity_score",
    # Dissemination — core
    "publish_to_zenodo",
    "prepare_arxiv_submission",
    "create_github_release",
    # PyPI
    "PyPIAdapter",
    "build_dist",
    "upload_dist",
    "check_dist",
    # Static site
    "GitHubPagesAdapter",
    "CloudflarePagesAdapter",
    "NetlifyAdapter",
    "get_static_site_adapter",
    "SiteDeployConfig",
    "SiteDeployResult",
    "SiteHosting",
    # Archival
    "archive_publication",
    "load_credentials",
    "ArchivalProvider",
    "ArchivalReceipt",
    "ArchivalRun",
    # Registry
    "PLATFORM_REGISTRY",
    "PlatformInfo",
    "PublishingTier",
    "list_platforms",
    "get_platform",
    "first_class_platforms",
    "documented_platforms",
]
