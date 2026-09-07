"""Shared bibliography discovery and Pandoc argument construction.

Publication renderers must consume the same bibliography set. Pandoc accepts one
``--bibliography`` argument per database, so the render boundary can preserve
the manuscript's source files while still presenting their deterministic union
to citeproc.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path


class BibliographyConflictError(ValueError):
    """Raised when two bibliography entries declare conflicting citation keys."""


_BIB_ENTRY_RE = re.compile(
    r"^\s*@(?!(?:comment|string|preamble)\b)[A-Za-z][A-Za-z0-9_-]*\s*[({]\s*([^,\s})]+)",
    flags=re.IGNORECASE | re.MULTILINE,
)


def _unique_existing_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    """Return paths in input order, deduplicated by resolved file identity."""

    unique: list[Path] = []
    seen: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"Bibliography not found: {path}")
        identity = path.resolve(strict=True)
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(path)
    return tuple(unique)


def _validate_unique_citation_keys(paths: tuple[Path, ...]) -> None:
    """Reject case-insensitive duplicate keys before citation tools diverge."""

    owner_by_key: dict[str, tuple[str, Path]] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for key in _BIB_ENTRY_RE.findall(text):
            key_identity = key.casefold()
            previous = owner_by_key.get(key_identity)
            if previous is not None:
                previous_key, previous_path = previous
                raise BibliographyConflictError(
                    "Case-insensitive duplicate citation keys "
                    f"{previous_key!r} in {previous_path.resolve(strict=True)} and "
                    f"{key!r} in {path.resolve(strict=True)}; citation keys must be "
                    "unique case-insensitively across manuscript/*.bib"
                )
            owner_by_key[key_identity] = (key, path)


def resolve_bibliography(manuscript_dir: Path) -> tuple[Path, ...]:
    """Return the deterministic union of top-level manuscript bibliographies.

    Files are ordered by path name, repeated or symlinked paths are included once, and
    duplicate citation keys (including case-only variants) fail closed so
    BibTeX and citeproc cannot choose different definitions silently.  A
    missing directory or a directory with no ``*.bib`` files resolves to an
    empty tuple.
    """

    candidates = sorted(
        (path for path in manuscript_dir.glob("*.bib") if path.is_file()),
        key=lambda path: path.name,
    )
    paths = _unique_existing_paths(candidates)
    _validate_unique_citation_keys(paths)
    return paths


def pandoc_bibliography_args(paths: Iterable[Path]) -> list[str]:
    """Return one stable ``--bibliography`` argument per unique input file.

    Callers add ``--citeproc`` at the correct point in their filter ordering.
    Missing inputs raise instead of silently dropping citations.
    """

    return [f"--bibliography={path}" for path in _unique_existing_paths(paths)]


__all__ = [
    "BibliographyConflictError",
    "pandoc_bibliography_args",
    "resolve_bibliography",
]
