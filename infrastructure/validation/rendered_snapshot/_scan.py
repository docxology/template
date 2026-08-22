"""Repository-boundary scan and Git-cache machinery for rendered snapshots.

Split from :mod:`infrastructure.validation.rendered_snapshot` to keep module
sizes inside the line-count gate; the parent module re-imports every moved
name under its original spelling, so all existing import paths remain valid.
This is a private companion module — the public API surface stays in
``rendered_snapshot``.
"""

from __future__ import annotations

import hashlib  # noqa: F401  (re-exported companion namespace)
import subprocess
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.project_paths import validate_project_name
from infrastructure.project.linking import LIFECYCLE_SUBDIRS


class RenderedSnapshotError(ValueError):
    """Raised when current rendered evidence is incomplete or inconsistent."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_CACHE_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "htmlcov",
    }
)

#: Path components skipped when walking project trees for snapshots.
CACHE_PARTS = _CACHE_PARTS
PROJECT_EXCLUDED_PARTS = _CACHE_PARTS | {"output", "tests"}

_PROJECT_CACHE_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "htmlcov",
    }
)


@dataclass(frozen=True)
class Fingerprint:
    """Hash and cardinality for a deterministic set of named files."""

    sha256: str
    file_count: int


@dataclass(frozen=True)
class FileRecord:
    key: str
    path: Path


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def relative_to_permitted(path: Path, permitted: list[Path]) -> str | None:
    """Return *path* relative to the first permitted root that contains it."""
    for allowed in permitted:
        try:
            return path.relative_to(allowed).as_posix()
        except ValueError:
            continue
    return None


def iter_tree_files(
    root: Path,
    *,
    repo_root: Path,
    excluded_parts: frozenset[str] = PROJECT_EXCLUDED_PARTS,
    extra_root: Path | None = None,
) -> Iterator[FileRecord]:
    """Walk files while following only confined, acyclic symlinks.

    Confinement means the repository, plus ``extra_root`` when one is given.

    ``extra_root`` exists for projects that are symlinked into the repository
    rather than stored inside it. A private sidecar checkout linked in at
    ``projects/working/<name>`` resolves outside ``repo_root``, and refusing it
    made the entire tree unreadable even though that tree is precisely what the
    snapshot was asked to describe. Callers pass the project root they are
    already walking, so the guard still rejects a symlink escaping BOTH the
    repository and the declared project, which is the case it exists for.

    The boundary is never widened by default: a caller that declares no extra
    root gets the repository-only behavior unchanged.

    Args:
        root: Directory to walk.
        repo_root: Repository the snapshot claims to describe.
        excluded_parts: Path components to skip.
        extra_root: An additional permitted containment root, or None.
    """
    root = root.absolute()
    repository = repo_root.resolve()
    permitted = [repository]
    if extra_root is not None:
        permitted.append(extra_root.resolve())
    if not root.exists():
        return

    def visit(display_dir: Path, actual_dir: Path, ancestors: frozenset[Path]) -> Iterator[FileRecord]:
        resolved_dir = actual_dir.resolve(strict=True)
        if not any(is_relative_to(resolved_dir, allowed) for allowed in permitted):
            raise RenderedSnapshotError("SOURCE_SYMLINK_ESCAPE", f"source directory escapes repository: {display_dir}")
        if resolved_dir in ancestors:
            raise RenderedSnapshotError("SOURCE_SYMLINK_CYCLE", f"source symlink cycle: {display_dir}")
        try:
            children = sorted(actual_dir.iterdir(), key=lambda child: child.name)
        except OSError as exc:
            raise RenderedSnapshotError("SOURCE_UNREADABLE", f"cannot read {display_dir}: {exc}") from exc
        next_ancestors = ancestors | {resolved_dir}
        for child in children:
            display = display_dir / child.name
            if child.name in excluded_parts:
                continue
            try:
                if child.is_symlink():
                    target = child.resolve(strict=True)
                    target_key = relative_to_permitted(target, permitted)
                    if target_key is None:
                        raise RenderedSnapshotError(
                            "SOURCE_SYMLINK_ESCAPE",
                            f"source symlink escapes repository: {display}",
                        )
                    if target.is_dir():
                        try:
                            display_key = display.absolute().relative_to(repo_root.absolute()).as_posix()
                        except ValueError as exc:
                            raise RenderedSnapshotError(
                                "SOURCE_SYMLINK_ESCAPE",
                                f"source symlink display path escapes repository: {display}",
                            ) from exc
                        for nested in visit(display, target, next_ancestors):
                            yield FileRecord(
                                f"{nested.key} @symlink={display_key}->{target_key}",
                                nested.path,
                            )
                    elif target.is_file():
                        yield FileRecord(f"{display.as_posix()} -> {target_key}", target)
                    else:
                        raise RenderedSnapshotError(
                            "SOURCE_SYMLINK_INVALID",
                            f"source symlink is not a file or directory: {display}",
                        )
                elif child.is_dir():
                    yield from visit(display, child, next_ancestors)
                elif child.is_file():
                    yield FileRecord(display.as_posix(), child)
            except OSError as exc:
                raise RenderedSnapshotError("SOURCE_UNREADABLE", f"cannot inspect {display}: {exc}") from exc

    yield from visit(root, root, frozenset())


def relative_record(record: FileRecord, root: Path) -> FileRecord:
    prefix = root.absolute().as_posix().rstrip("/") + "/"
    return FileRecord(record.key.removeprefix(prefix), record.path)


def repository_root_for(path: Path, fallback: Path) -> Path:
    """Find the nearest Git worktree for *path*, including nested checkouts."""
    candidate = path.resolve()
    for directory in (candidate, *candidate.parents):
        if (directory / ".git").exists():
            return directory
        if directory == fallback.resolve():
            break
    return fallback


def lexical_project_root_for_selection(
    repo_root: Path,
    project: str,
    resolved_project_root: Path,
) -> Path:
    """Recover the selected lexical alias without resolving its leaf link."""
    project = validate_project_name(project)
    projects_root = (repo_root / "projects").absolute()
    parts = project.split("/")
    if parts[0] in {*LIFECYCLE_SUBDIRS, "templates"}:
        return projects_root.joinpath(*parts)

    resolved = resolved_project_root.resolve(strict=False)
    candidates = (
        projects_root / "active" / project,
        projects_root / "working" / project,
        projects_root / project,
        projects_root / "templates" / project,
    )
    for candidate in candidates:
        if (candidate.exists() or candidate.is_symlink()) and candidate.resolve(strict=False) == resolved:
            return candidate
    return candidates[0]


def source_repository_boundary(
    repo_root: Path,
    lexical_project_root: Path,
    resolved_project_root: Path,
) -> Path:
    """Authorize project source through its real repository and lexical alias."""
    repository = repo_root.resolve()
    projects_root = (repository / "projects").absolute()
    lexical = lexical_project_root.absolute()
    try:
        relative = lexical.relative_to(projects_root)
    except ValueError as exc:
        raise RenderedSnapshotError(
            "PROJECT_LINK_INVALID",
            "project source is not represented below the template projects directory",
        ) from exc

    current = lexical.parent
    while True:
        if current.is_symlink():
            raise RenderedSnapshotError(
                "PROJECT_LINK_INVALID",
                f"project source has an intermediate symlink: {current}",
            )
        if current == projects_root:
            break
        if current == current.parent:
            raise RenderedSnapshotError(
                "PROJECT_LINK_INVALID",
                "project source alias does not have the expected projects-directory ancestry",
            )
        current = current.parent

    parts = relative.parts
    if parts and parts[0] == "templates" and lexical.is_symlink():
        raise RenderedSnapshotError(
            "PROJECT_LINK_INVALID",
            "public template projects cannot be represented by a symlink",
        )

    resolved_project = resolved_project_root.resolve()
    if is_relative_to(resolved_project, repository):
        return repository

    is_direct_leaf = len(parts) == 2
    is_category_leaf = len(parts) == 3 and parts[1].startswith("_")
    if (
        not parts
        or parts[0] not in LIFECYCLE_SUBDIRS
        or not (is_direct_leaf or is_category_leaf)
        or not lexical.is_symlink()
    ):
        raise RenderedSnapshotError(
            "PROJECT_LINK_INVALID",
            "external project source requires a managed lifecycle leaf symlink",
        )
    try:
        linked_target = lexical.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RenderedSnapshotError(
            "PROJECT_LINK_INVALID",
            f"external lifecycle project link is unreadable: {exc}",
        ) from exc
    if linked_target != resolved_project:
        raise RenderedSnapshotError(
            "PROJECT_LINK_INVALID",
            "external lifecycle project link does not match the selected project",
        )

    project_repository = repository_root_for(resolved_project, repository).resolve()
    if project_repository == repository or not (project_repository / ".git").exists():
        raise RenderedSnapshotError(
            "PROJECT_REPOSITORY_MISSING",
            "external project requires a containing Git worktree boundary",
        )
    if not is_relative_to(resolved_project, project_repository):
        raise RenderedSnapshotError(
            "PROJECT_REPOSITORY_INVALID",
            "external project escapes its nearest Git worktree boundary",
        )
    if cached_paths(project_repository) is None:
        raise RenderedSnapshotError(
            "PROJECT_REPOSITORY_INVALID",
            "external project Git worktree is unavailable",
        )
    return project_repository


def cached_paths(repo_root: Path) -> set[Path] | None:
    """Return cached paths for one worktree, independent of global Git helpers."""
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [
                "git",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedcache=false",
                "-C",
                str(repo_root),
                "ls-files",
                "--cached",
                "-z",
            ],
            check=False,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return {(repo_root / raw.decode("utf-8")).absolute() for raw in completed.stdout.split(b"\0") if raw}


def cached_records(
    records: Iterable[FileRecord],
    repo_root: Path,
    *,
    require_worktrees: bool = False,
) -> list[FileRecord]:
    """Keep files cached by their nearest Git worktree, including nested repos."""
    candidates = list(records)
    by_root: dict[Path, list[FileRecord]] = {}
    for record in candidates:
        root = repository_root_for(record.path, repo_root)
        by_root.setdefault(root, []).append(record)
    cached_by_root = {root: cached_paths(root) for root in by_root}
    if any(paths is None for paths in cached_by_root.values()):
        if require_worktrees:
            unavailable = sorted(str(root) for root, paths in cached_by_root.items() if paths is None)
            raise RenderedSnapshotError(
                "PROJECT_REPOSITORY_INVALID",
                "project source Git worktree is unavailable: " + ", ".join(unavailable),
            )
        return candidates
    return [
        record
        for root, grouped in by_root.items()
        for record in grouped
        if record.path.resolve() in (cached_by_root[root] or set())
    ]
