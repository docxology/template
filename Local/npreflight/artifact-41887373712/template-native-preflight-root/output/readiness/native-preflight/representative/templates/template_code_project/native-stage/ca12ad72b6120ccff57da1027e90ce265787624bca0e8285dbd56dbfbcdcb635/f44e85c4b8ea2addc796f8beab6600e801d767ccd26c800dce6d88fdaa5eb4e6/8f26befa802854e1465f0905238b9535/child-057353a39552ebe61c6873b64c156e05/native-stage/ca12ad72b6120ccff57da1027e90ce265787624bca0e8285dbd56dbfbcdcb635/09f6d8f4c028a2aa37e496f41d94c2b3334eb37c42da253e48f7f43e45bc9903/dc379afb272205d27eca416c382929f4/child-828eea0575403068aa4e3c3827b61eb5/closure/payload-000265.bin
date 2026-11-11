"""Public-repository fond scope helpers.

Runtime fond discovery intentionally includes local symlinked workspaces so
the orchestration CLI can operate on private fonds. Public CI and generated docs
must stay narrower: only the tracked exemplar fonds are part of the
public template repository.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from infrastructure.fonds.discovery import discover_fonds
from infrastructure.fonds.fonds_info import FondInfo

#: Canonical roster of git-tracked public exemplar fonds names.
#: Each entry is qualified as ``<program>/<name>`` (e.g. ``templates/template_bibliography``).
PUBLIC_FOND_NAMES: tuple[str, ...] = (
    "templates/template_bibliography",
    "templates/template_contacts",
    "templates/template_datasets",
)


def public_fond_infos(repo_root: Path | str) -> list[FondInfo]:
    """Return discovered fonds that are part of the public template repo."""
    root = Path(repo_root)
    allowed = set(PUBLIC_FOND_NAMES)
    return [fond for fond in discover_fonds(root) if fond.qualified_name in allowed]


def public_fond_names(repo_root: Path | str) -> list[str]:
    """Return public template fond names present in this checkout."""
    return sorted(fond.qualified_name for fond in public_fond_infos(repo_root))


def public_fond_data_paths(repo_root: Path | str) -> list[Path]:
    """Return ``data/`` paths for public fonds, for lint/type check scope.

    Paths are repo-relative.
    """
    root = Path(repo_root)
    paths: list[Path] = []
    for name in PUBLIC_FOND_NAMES:
        data_dir = root / "fonds" / name / "data"
        if data_dir.is_dir():
            paths.append(Path("fonds") / name / "data")
    return paths


def _format_paths(paths: Sequence[Path]) -> str:
    return " ".join(path.as_posix() for path in paths)


__all__ = [
    "PUBLIC_FOND_NAMES",
    "public_fond_data_paths",
    "public_fond_infos",
    "public_fond_names",
]
