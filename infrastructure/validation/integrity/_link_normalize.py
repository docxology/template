"""Path normalization helpers for markdown link validation."""

from __future__ import annotations

from pathlib import Path

_PROJECT_BUCKETS: frozenset[str] = frozenset(
    {"templates", "active", "working", "ongoing", "published", "archive", "other"}
)


def _get_actual_project_names(repo_root: Path) -> list[str]:
    """Return discoverable project path segments for template substitution."""
    from infrastructure.project.discovery import discover_projects

    names: list[str] = []
    seen: set[str] = set()
    for project in discover_projects(repo_root):
        for candidate in (project.qualified_name, project.name):
            if candidate and candidate not in seen:
                names.append(candidate)
                seen.add(candidate)
    return names


def _nearest_project_root(source_file: Path | None, repo_root: Path) -> Path | None:
    """Return the containing project root for docs under ``projects/``."""
    if source_file is None:
        return None

    try:
        relative = source_file.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return None

    parts = relative.parts
    if len(parts) < 2 or parts[0] != "projects":
        return None

    if parts[1] in _PROJECT_BUCKETS:
        if len(parts) < 4:
            return None
        return repo_root / "projects" / parts[1] / parts[2]

    if len(parts) < 3 or not (repo_root / "projects" / parts[1]).is_dir():
        return None

    return repo_root / "projects" / parts[1]


def _resolve_template_path(path_ref: str, repo_root: Path, source_file: Path | None = None) -> Path | None:
    """Resolve template paths like projects/{name}/ to actual paths."""
    try:
        project_root = _nearest_project_root(source_file, repo_root)
        if project_root is not None and path_ref.startswith(("scripts/", "output/")):
            project_relative = project_root / path_ref
            if project_relative.exists():
                return project_relative
            repo_relative = repo_root / path_ref
            if repo_relative.exists():
                return repo_relative
            if path_ref.startswith("scripts/"):
                return project_relative

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
