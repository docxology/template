"""Backwards-compat shim: the module moved to ``infrastructure.publishing.metadata.metadata_from_config``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.metadata.metadata_from_config import (
    publication_metadata_from_config,
    publication_metadata_from_config_dict,
    load_publication_release_context,
)

__all__ = [
    "publication_metadata_from_config",
    "publication_metadata_from_config_dict",
    "load_publication_release_context",
]
