"""Fond discovery for multi-fond support.

Scans the fonds/ directory for valid fonds (passive resource pools) and returns
FondInfo objects. Follows the same architecture as infrastructure/project/discovery.py
but for passive data stores instead of executable projects.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.fonds.fonds_info import FondInfo, build_fond_info
from infrastructure.fonds.validation import validate_fond_structure

logger = get_logger(__name__)

#: Non-rendered lifecycle subdirectories under ``fonds/``.
#: Only ``templates/`` is ever discovered and rendered (for public exemplars).
#: Working/ holds private sidecar mirrors; archive/ holds retired fonds.
NON_RENDERED_FOND_SUBDIRS: frozenset[str] = frozenset({"working", "archive"})

#: Rendered subdirectories under ``fonds/``.
RENDERED_FOND_SUBDIRS: frozenset[str] = frozenset({"templates"})

#: Public API of this module.
__all__ = [
    "NON_RENDERED_FOND_SUBDIRS",
    "RENDERED_FOND_SUBDIRS",
    "discover_fonds",
    "resolve_fond_root",
]


def discover_fonds(
    repo_root: Path | str,
) -> list[FondInfo]:
    """Discover all valid fonds in the fonds/ directory.

    Args:
        repo_root: Repository root directory.

    Returns:
        List of FondInfo objects for valid fonds.

    The lifecycle subfolders in :data:`NON_RENDERED_FOND_SUBDIRS`
    (``working``/``archive``) are deliberately excluded from discovery.
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)
    fonds_dir_path = repo_root / "fonds"

    if not fonds_dir_path.exists():
        logger.warning(f"Fonds directory not found: {fonds_dir_path}")
        return []

    fonds: list[FondInfo] = []

    for child_dir in sorted(fonds_dir_path.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        # Non-rendered lifecycle mirrors are never discovered
        if child_dir.name in NON_RENDERED_FOND_SUBDIRS:
            logger.debug(f"Skipping non-rendered lifecycle subfolder: {child_dir.name}")
            continue

        # First, check if this is a valid standalone fond
        is_valid, _ = validate_fond_structure(child_dir)

        if is_valid:
            fond_info = build_fond_info(child_dir)
            fonds.append(fond_info)
            logger.debug(f"Discovered standalone fond: {fond_info.name} at {fond_info.path}")
        else:
            # Not a valid fond — check if it's a program directory containing fonds
            nested = _discover_nested_fonds(child_dir, program_name=child_dir.name)
            if nested:
                fonds.extend(nested)
                logger.debug(f"Discovered program directory: {child_dir.name} with {len(nested)} fonds")
            else:
                logger.debug(f"Skipping {child_dir.name}: not a valid fond or program directory")

    return fonds


def _discover_nested_fonds(
    program_dir: Path,
    program_name: str,
    *,
    _allow_category: bool = True,
) -> list[FondInfo]:
    """Discover fonds nested within a program directory.

    A program directory is a folder that contains multiple related fonds,
    but is not a fond itself. A child directory whose name starts with
    ``_`` is a category grouping — its own direct children are the actual
    fonds, discovered with the compound qualified name ``<program>/_<category>/<name>``.
    Category nesting is exactly one level deep.
    """
    nested = []
    for child_dir in sorted(program_dir.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        is_valid, _ = validate_fond_structure(child_dir)

        if is_valid:
            fond_info = build_fond_info(child_dir, program=program_name)
            nested.append(fond_info)
            logger.debug(f"Discovered nested fond: {fond_info.qualified_name} at {fond_info.path}")
        elif _allow_category and child_dir.name.startswith("_"):
            nested.extend(
                _discover_nested_fonds(
                    child_dir,
                    program_name=f"{program_name}/{child_dir.name}",
                    _allow_category=False,
                )
            )

    return nested


def resolve_fond_root(repo_root: Path | str, fond_name: str) -> Path:
    """Resolve a fond directory by qualified name.

    A qualified ``<subfolder>/<name>`` path (head in ``templates/``, ``working/``)
    resolves directly under ``fonds/<subfolder>/<name>``. A bare name prefers
    ``fonds/templates/<name>``, then a flat standalone ``fonds/<name>``.

    Args:
        repo_root: Repository root directory.
        fond_name: Fond name or qualified path.

    Returns:
        Absolute resolved path to the fond directory.
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)

    valid_heads = NON_RENDERED_FOND_SUBDIRS | RENDERED_FOND_SUBDIRS

    head = fond_name.replace("\\", "/").split("/", 1)[0]
    if head in valid_heads:
        qualified = repo_root / "fonds" / fond_name
        if qualified.is_dir():
            return qualified.resolve()
        return qualified

    # Try templates first, then flat
    for candidate in [
        repo_root / "fonds" / "templates" / fond_name,
        repo_root / "fonds" / fond_name,
    ]:
        if candidate.is_dir():
            return candidate.resolve()

    return repo_root / "fonds" / fond_name
