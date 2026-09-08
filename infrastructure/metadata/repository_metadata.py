"""Canonical repository metadata normalization for publication generators."""

from __future__ import annotations

from collections.abc import Mapping


def normalized_repository_url(publication: Mapping[str, object] | None) -> str | None:
    """Return the explicit repository URL or derive one from ``owner/repo``.

    ``publication.repository_url`` is authoritative when present.  Otherwise
    ``publication.github_repository`` is interpreted as a GitHub ``owner/repo``
    slug. Empty and non-string values produce ``None``.
    """
    if publication is None:
        return None
    explicit = publication.get("repository_url")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    github_repository = publication.get("github_repository")
    if isinstance(github_repository, str) and github_repository.strip():
        return f"https://github.com/{github_repository.strip()}"
    return None


__all__ = ["normalized_repository_url"]
