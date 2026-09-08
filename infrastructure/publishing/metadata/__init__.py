"""Metadata pipeline family (stage, export, CLI, config-driven metadata).

Subpackaged out of the flat ``infrastructure.publishing`` namespace by
RENDERING-LAYERING-1 phase 2b; the flat module paths remain as silent
backwards-compat shims. The shared ``infrastructure.metadata`` leaf package
(repository-URL normalization and ebook metadata generation) is a different,
rendering-safe surface and must not be confused with this pipeline family.

The aggregate re-exports below keep the historical
``from infrastructure.publishing.metadata import <symbol>`` module path
resolving (the flat ``metadata.py`` aggregator became this package).
"""

from .metadata_aggregate import (
    calculate_metadata_complexity_score,
    create_academic_profile_data,
    create_repository_metadata,
    extract_publication_metadata,
    generate_publication_metrics,
    generate_publication_summary,
    validate_doi,
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
