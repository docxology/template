"""Private path-identity and confinement helpers for Methods plans."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.project.linking import LIFECYCLE_SUBDIRS

_ExternalBoundary = tuple[Path, Path]


def _is_within(path: Path, boundary: Path) -> bool:
    try:
        path.relative_to(boundary)
    except ValueError:
        return False
    return True


def _lexical_project_root(
    root: Path,
    project_name: str,
    resolved_project_root: Path,
    *,
    projects_dir: str,
) -> Path:
    """Return the non-resolved project alias selected by project resolution."""
    projects_root = (root / projects_dir).absolute()
    direct = projects_root.joinpath(*project_name.split("/"))
    resolved = resolved_project_root.resolve(strict=False)
    if (direct.exists() or direct.is_symlink()) and direct.resolve(strict=False) == resolved:
        return direct
    if projects_dir == "projects" and "/" not in project_name:
        for prefix in ("active", "working", "templates"):
            candidate = projects_root / prefix / project_name
            if (candidate.exists() or candidate.is_symlink()) and candidate.resolve(strict=False) == resolved:
                return candidate
    if _is_within(resolved, root):
        return resolved
    return direct


def _portable_project_path(
    path: Path,
    *,
    repo_root: Path,
    project_root: Path,
    project_display_root: Path,
) -> Path:
    """Map a resolved project-local path back through its lexical alias."""
    resolved = path.resolve(strict=False)
    if _is_within(resolved, repo_root.resolve()):
        return resolved.relative_to(repo_root.resolve())
    if _is_within(resolved, project_root.resolve()):
        return project_display_root / resolved.relative_to(project_root.resolve())
    return path


def _lexical_plan_path(root: Path, path: Path) -> Path:
    """Return an absolute plan path without resolving an intentional leaf link."""
    return path.absolute() if path.is_absolute() else (root / path).absolute()


def _nearest_git_worktree(project_root: Path) -> Path:
    """Return the real nearest Git worktree containing an external project."""
    try:
        completed = subprocess.run(  # noqa: S603,S607 - fixed Git metadata argv; no shell.
            ["git", "-c", "core.fsmonitor=false", "rev-parse", "--show-toplevel"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"external lifecycle project has no readable Git worktree: {exc}") from exc
    lines = completed.stdout.splitlines()
    if completed.returncode != 0 or len(lines) != 1 or not lines[0].strip():
        raise ValueError("external lifecycle project has no readable Git worktree")
    try:
        git_root = Path(lines[0]).resolve(strict=True)
        resolved_project = project_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"external lifecycle Git worktree root is unreadable: {exc}") from exc
    if not (git_root / ".git").exists() or not _is_within(resolved_project, git_root):
        raise ValueError("external lifecycle project is outside its nearest Git worktree")
    return git_root


def _external_lifecycle_git_boundary(
    repo_root: Path,
    lexical_project_root: Path,
    resolved_project_root: Path,
) -> _ExternalBoundary | None:
    """Authorize one external project only through a managed lifecycle leaf link."""
    root = repo_root.resolve()
    resolved_project = resolved_project_root.resolve(strict=False)
    if _is_within(resolved_project, root):
        return None

    projects_root = (root / "projects").absolute()
    lexical = lexical_project_root.absolute()
    try:
        relative = lexical.relative_to(projects_root)
    except ValueError as exc:
        raise ValueError("external project is not represented by a managed lifecycle leaf") from exc
    parts = relative.parts
    is_direct_leaf = len(parts) == 2
    is_category_leaf = len(parts) == 3 and parts[1].startswith("_")
    if not parts or parts[0] not in LIFECYCLE_SUBDIRS or not (is_direct_leaf or is_category_leaf):
        raise ValueError("external project is not represented by a managed lifecycle leaf")
    if not lexical.is_symlink():
        raise ValueError("external lifecycle project must be represented by a leaf symlink")
    parents = (
        (lexical.parent, projects_root) if is_direct_leaf else (lexical.parent, lexical.parent.parent, projects_root)
    )
    if any(parent.is_symlink() for parent in parents):
        raise ValueError("external lifecycle project has an intermediate symlink")
    try:
        linked_target = lexical.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"external lifecycle project link is unreadable: {exc}") from exc
    if linked_target != resolved_project:
        raise ValueError("external lifecycle project link does not match the resolved project")
    return lexical, _nearest_git_worktree(resolved_project)


def _path_is_authorized(
    root: Path,
    path: Path,
    external_boundary: _ExternalBoundary | None,
) -> bool:
    """Return whether a plan path stays within an authorized repository boundary."""
    candidate = _lexical_plan_path(root, path)
    resolved = candidate.resolve(strict=False)
    if _is_within(resolved, root.resolve()):
        return True
    if external_boundary is None:
        return False
    lexical_project_root, git_boundary = external_boundary
    return _is_within(candidate, lexical_project_root) and _is_within(resolved, git_boundary.resolve())
