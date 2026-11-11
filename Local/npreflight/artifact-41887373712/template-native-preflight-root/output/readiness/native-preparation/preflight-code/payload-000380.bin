"""Shared publication-metadata leaves consumed by publishing, rendering,
documentation, and project layers.

Renderers may import this package; the rendering->publishing inversion
guard (``tests/infra_tests/rendering/test_layering.py``) treats it as
rendering-safe.
"""

from infrastructure.metadata.metadata_package import (
    EbookPublicationMetadata,
    ebook_metadata_from_config,
    generate_epub_opf,
    generate_metadata_json,
    generate_metadata_package,
    generate_onix_xml,
)
from infrastructure.metadata.repository_metadata import normalized_repository_url

__all__ = [
    "EbookPublicationMetadata",
    "ebook_metadata_from_config",
    "generate_epub_opf",
    "generate_metadata_json",
    "generate_metadata_package",
    "generate_onix_xml",
    "normalized_repository_url",
    "repository_metadata",
]
