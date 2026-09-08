"""Backwards-compat shim: the module moved to ``infrastructure.publishing.release.release_cli``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.release.release_cli import (
    build_release_parser,
    resolve_github_token,
    resolve_zenodo_token,
)

__all__ = [
    "build_release_parser",
    "resolve_github_token",
    "resolve_zenodo_token",
]
