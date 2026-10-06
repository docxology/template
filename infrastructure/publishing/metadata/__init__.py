"""Metadata pipeline family (stage, export, CLI, config-driven metadata).

Subpackaged out of the flat ``infrastructure.publishing`` namespace by
RENDERING-LAYERING-1 phase 2b; import pipeline modules from this package.
The shared ``infrastructure.metadata`` leaf package
(repository-URL normalization and ebook metadata generation) is a different,
rendering-safe surface and must not be confused with this pipeline family.

The package exports metadata extraction and reporting functions directly
from their implementation modules.
"""

from infrastructure.publishing._metadata_extraction import (
    extract_publication_metadata,
    validate_doi,
)
from infrastructure.publishing._metadata_reporting import (
    calculate_metadata_complexity_score,
    create_academic_profile_data,
    create_repository_metadata,
    generate_publication_metrics,
    generate_publication_summary,
)

__all__ = [
    "calculate_metadata_complexity_score",
    "create_academic_profile_data",
    "create_repository_metadata",
    "extract_publication_metadata",
    "generate_publication_metrics",
    "generate_publication_summary",
    "validate_doi",
]
