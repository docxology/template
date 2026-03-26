"""Metadata extraction and management functions for academic publishing.

This module re-exports from focused sub-modules for backwards compatibility.
"""

from __future__ import annotations

from infrastructure.publishing._metadata_extraction import (
    extract_publication_metadata as extract_publication_metadata,
    validate_doi as validate_doi,
)
from infrastructure.publishing._metadata_reporting import (
    calculate_complexity_score as calculate_complexity_score,
    calculate_metadata_complexity_score as calculate_metadata_complexity_score,
    create_academic_profile_data as create_academic_profile_data,
    create_repository_metadata as create_repository_metadata,
    generate_publication_metrics as generate_publication_metrics,
    generate_publication_summary as generate_publication_summary,
)

__all__ = [
    "calculate_complexity_score",
    "calculate_metadata_complexity_score",
    "create_academic_profile_data",
    "create_repository_metadata",
    "extract_publication_metadata",
    "generate_publication_metrics",
    "generate_publication_summary",
    "validate_doi",
]
