"""Backwards-compat shim: the module moved to ``infrastructure.publishing.release.release_pairing``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.release.release_pairing import (
    format_pairing_checklist,
    format_pairing_checklist_compact,
    validate_release_pairing,
)

__all__ = [
    "format_pairing_checklist",
    "format_pairing_checklist_compact",
    "validate_release_pairing",
]
