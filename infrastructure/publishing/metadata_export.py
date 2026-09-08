"""Backwards-compat shim: the module moved to ``infrastructure.publishing.metadata.metadata_export``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.metadata.metadata_export import (
    build_citation_cff,
    build_codemeta,
    build_zenodo,
    write_metadata_files,
)

__all__ = [
    "build_citation_cff",
    "build_codemeta",
    "build_zenodo",
    "write_metadata_files",
]
