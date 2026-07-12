"""Path normalization helpers for markdown link validation."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROJECT_BUCKETS: frozenset[str] = frozenset(
    {"templates", "active", "working", "ongoing", "published", "archive", "other"}
)
_SCOPED_RESOURCE_ROOTS: frozenset[str] = frozenset({"projects", "fonds", "rules", "tools"})


@lru_cache(maxsize=32)
def _get_actual_project_names_cached(repo_root_key: str) -> tuple[str, ...]:
    from infrastructure.project.discovery import discover_projects

    names: list[str] = []
    seen: set[str] = set()
    for project in discover_projects(Path(repo_root_key)):
        for candidate in (project.qualified_name, project.name):
            if candidate and candidate not in seen:
                names.append(candidate)
                seen.add(candidate)
    return tuple(names)


def _get_actual_project_names(repo_root: Path) -> list[str]:
    """Return discoverable project path segments for template substitution."""
    repo_root_key = str(repo_root if repo_root.is_absolute() else repo_root.resolve())
    return list(_get_actual_project_names_cached(repo_root_key))


@lru_cache(maxsize=4096)
def _nearest_scoped_root_cached(source_file_key: str, repo_root_key: str) -> str | None:
    source_file = Path(source_file_key)
    repo_root = Path(repo_root_key)
    try:
        relative = source_file.relative_to(repo_root)
    except ValueError:
        try:
            relative = source_file.resolve().relative_to(repo_root.resolve())
        except ValueError:
            return None

    parts = relative.parts
    if len(parts) < 2 or parts[0] not in _SCOPED_RESOURCE_ROOTS:
        return None

    resource_kind = parts[0]
    if parts[1] in _PROJECT_BUCKETS:
        if len(parts) < 4:
            return None
        return str(repo_root / resource_kind / parts[1] / parts[2])

    if len(parts) < 3 or not (repo_root / resource_kind / parts[1]).is_dir():
        return None

    return str(repo_root / resource_kind / parts[1])


def _nearest_scoped_root(source_file: Path | None, repo_root: Path) -> Path | None:
    """Return the containing project/fond/rule/tool root for a source file."""
    if source_file is None:
        return None
    source_file_key = str(source_file if source_file.is_absolute() else source_file.resolve())
    repo_root_key = str(repo_root if repo_root.is_absolute() else repo_root.resolve())
    scoped_root = _nearest_scoped_root_cached(source_file_key, repo_root_key)
    return Path(scoped_root) if scoped_root else None


def _resolve_template_path(path_ref: str, repo_root: Path, source_file: Path | None = None) -> Path | None:
    """Resolve template paths like projects/{name}/ to actual paths."""
    try:
        scoped_root = _nearest_scoped_root(source_file, repo_root)
        if scoped_root is not None and path_ref.startswith(("scripts/", "output/")):
            scoped_relative = scoped_root / path_ref
            if scoped_relative.exists():
                return scoped_relative
            repo_relative = repo_root / path_ref
            if repo_relative.exists():
                return repo_relative
            if path_ref.startswith("scripts/"):
                return scoped_relative

        if path_ref.startswith("projects/project/"):
            project_names = _get_actual_project_names(repo_root)
            for project_name in project_names:
                actual_path = path_ref.replace("projects/project/", f"projects/{project_name}/")
                full_path = repo_root / actual_path
                if full_path.exists():
                    return full_path
            return None
        if path_ref.startswith("projects/{name}/"):
            return None
        if path_ref.startswith("infrastructure/"):
            return repo_root / path_ref
        if path_ref.startswith("scripts/"):
            return repo_root / path_ref
        if path_ref.startswith("output/project/"):
            project_names = _get_actual_project_names(repo_root)
            for project_name in project_names:
                actual_path = path_ref.replace("output/project/", f"output/{project_name}/")
                full_path = repo_root / actual_path
                if full_path.exists():
                    return full_path
            return None
        return repo_root / path_ref
    except OSError:
        return None


def _is_real_path_item(item_name: str) -> bool:
    """Check if a directory tree item looks like a real file/directory."""
    if any(skip in item_name.lower() for skip in ["...", "etc", "files", "more"]):
        return False
    if "{" in item_name and "}" in item_name:
        return False
    return True
