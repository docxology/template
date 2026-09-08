"""Backwards-compat shim: the module moved to ``infrastructure.publishing.metadata.metadata_stage``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.metadata.metadata_stage import (
    run_metadata_package,
)

__all__ = [
    "run_metadata_package",
]
