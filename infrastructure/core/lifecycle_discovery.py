"""Traverse lifecycle trees without owning the resource types they contain."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from logging import Logger
from pathlib import Path
from typing import Literal

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.project_paths import NON_RENDERED_SUBDIRS

_project_logger = get_logger("infrastructure.project.validation")

EntryKind = Literal["standalone", "program"]
POOL_NON_RENDERED_SUBDIRS = frozenset({"working", "archive"})
POOL_RENDERED_SUBDIRS = frozenset({"templates"})


@dataclass(frozen=True)
class LifecycleDiscoveryConfig:
    """Data container for LifecycleDiscoveryConfig."""

    non_rendered_subdirs: frozenset[str] = field(default_factory=lambda: NON_RENDERED_SUBDIRS)
    skip_dot_prefixed: bool = True


@dataclass(frozen=True)
class ProgramEntry:
    """Data container for ProgramEntry."""

    name: str
    path: Path
    kind: EntryKind


def _visible_directories(
    root: Path,
    excluded: frozenset[str] = frozenset(),
    *,
    skip_dot_prefixed: bool = True,
) -> Iterator[Path]:
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in excluded:
            continue
        if skip_dot_prefixed and child.name.startswith("."):
            continue
        yield child


def discover_lifecycle_items[Item](
    root: Path,
    validate: Callable[[Path], tuple[bool, str]],
    build: Callable[[Path, str], Item],
    *,
    excluded: frozenset[str],
    kind: str,
    logger: Logger,
) -> list[Item]:
    """Discover valid leaves in sorted order, including one category level per program.

    A validated directory is a leaf even when its name begins with an underscore.
    Each domain supplies its own eligibility predicate and result constructor.
    """
    if not root.exists():
        logger.warning("%ss directory not found: %s", kind.capitalize(), root)
        return []

    def program_items(program_dir: Path, program: str, *, allow_category: bool = True) -> Iterator[Item]:
        for child in _visible_directories(program_dir):
            valid, _ = validate(child)
            if valid:
                item = build(child, program)
                logger.debug("Discovered nested %s: %s/%s at %s", kind, program, child.name, child)
                yield item
            elif allow_category and child.name.startswith("_"):
                yield from program_items(child, f"{program}/{child.name}", allow_category=False)

    items: list[Item] = []
    for child in _visible_directories(root):
        if child.name in excluded:
            logger.debug("Skipping non-rendered lifecycle subfolder: %s", child.name)
            continue
        valid, reason = validate(child)
        if valid:
            items.append(build(child, ""))
            logger.debug("Discovered standalone %s: %s at %s", kind, child.name, child)
            continue
        nested = list(program_items(child, child.name))
        if nested:
            items.extend(nested)
            logger.debug("Discovered program directory: %s with %s %ss", child.name, len(nested), kind)
        else:
            logger.debug("Skipping %s: %s", child.name, reason)
    return items


def resolve_pool_root(pool: Path, name: str, qualified_heads: frozenset[str]) -> Path:
    """Resolve resource pools with the shared qualified or templates-first lookup."""
    direct = pool / name
    if name.replace("\\", "/").split("/", 1)[0] in qualified_heads:
        return direct.resolve() if direct.is_dir() else direct
    for candidate in (pool / "templates" / name, direct):
        if candidate.is_dir():
            return candidate.resolve()
    return direct


def discover_program_entries(
    projects_dir: Path,
    config: LifecycleDiscoveryConfig | None = None,
) -> list[ProgramEntry]:
    """Process discover program entries."""
    cfg = config or LifecycleDiscoveryConfig()
    if not projects_dir.is_dir():
        return []
    entries: list[ProgramEntry] = []
    for child in _visible_directories(projects_dir, cfg.non_rendered_subdirs, skip_dot_prefixed=cfg.skip_dot_prefixed):
        is_valid, _ = validate_project_structure(child)
        kind: EntryKind = "standalone" if is_valid else "program"
        entries.append(ProgramEntry(name=child.name, path=child, kind=kind))
    return entries


def validate_project_structure(project_dir: Path) -> tuple[bool, str]:
    """Validate that project has required directory structure.

    Required directories:
    - src/ - Source code
    - tests/ - Test suite

    Optional but recommended:
    - scripts/ - Analysis scripts
    - manuscript/ - Research manuscript
    - output/ - Generated outputs (created automatically)

    Args:
        project_dir: Path to project directory

    Returns:
        Tuple of (is_valid, message)

    Examples:
        >>> validate_project_structure(Path("projects/project"))
        (True, "Valid project structure")

        >>> validate_project_structure(Path("projects/invalid"))
        (False, "Missing required directory: src")
    """
    if not project_dir.exists():
        return False, f"Project directory does not exist: {project_dir}"

    if not project_dir.is_dir():
        return False, f"Not a directory: {project_dir}"

    # Check required directories
    src_dir = project_dir / "src"
    if not src_dir.exists():
        return False, "Missing required directory: src"

    tests_dir = project_dir / "tests"
    if not tests_dir.exists():
        return False, "Missing required directory: tests"

    # Check that src/ contains Python files
    python_files = list(src_dir.glob("**/*.py"))
    if not python_files:
        return False, "src/ directory contains no Python files"

    # Check optional but recommended directories
    scripts_dir = project_dir / "scripts"
    manuscript_dir = project_dir / "manuscript"

    if not scripts_dir.exists():
        _project_logger.debug(f"{project_dir.name}: Optional scripts/ directory not found")

    if not manuscript_dir.exists():
        _project_logger.debug(f"{project_dir.name}: Optional manuscript/ directory not found")

    return True, "Valid project structure"


__all__ = [
    "EntryKind",
    "LifecycleDiscoveryConfig",
    "POOL_NON_RENDERED_SUBDIRS",
    "POOL_RENDERED_SUBDIRS",
    "ProgramEntry",
    "discover_lifecycle_items",
    "discover_program_entries",
    "resolve_pool_root",
    "validate_project_structure",
]
