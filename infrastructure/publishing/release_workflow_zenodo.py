"""Backwards-compat shim: the module moved to ``infrastructure.publishing.release.release_workflow_zenodo``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.release.release_workflow_zenodo import (
    _reserve_doi_dry_run,
    reserve_zenodo_doi_pair,
    write_reserved_dois_to_config,
)

__all__ = [
    "_reserve_doi_dry_run",
    "reserve_zenodo_doi_pair",
    "write_reserved_dois_to_config",
]
