"""Backwards-compat shim: the module moved to ``infrastructure.publishing.release.release_workflow``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.release.release_workflow import (
    ReleaseRequest,
    prepare_release_bundle,
    resolve_combined_pdf,
    run_release_workflow,
    validate_release_tag,
)

__all__ = [
    "ReleaseRequest",
    "prepare_release_bundle",
    "resolve_combined_pdf",
    "run_release_workflow",
    "validate_release_tag",
]
