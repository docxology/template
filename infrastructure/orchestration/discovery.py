"""Project discovery helpers for the orchestration CLI.

Wraps :func:`infrastructure.project.discovery.discover_projects` with two
additions used by the interactive menu and CLI:

- :func:`validate_project_slug` — defensive slug check that rejects path
  traversal (``..``), absolute paths (leading ``/``), embedded NUL bytes,
  empty strings, and any name not present in the discovered project list.
- :func:`select_project_interactive` — small TTY picker used by ``run.sh``'s
  former ``p`` menu option. Pure function for testability: takes an input
  callable and an output callable so tests can drive it without stdin.

The two always-present canonical projects are ``template_code_project`` and
``template_prose_project``. Any other active project name comes from
:func:`infrastructure.project.discovery.discover_projects` at runtime, including
symlinked private projects when link-sync has run. The generated docs record the
current roster; this module does not hard-code it.
"""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO

from infrastructure.project.discovery import (
    NON_RENDERED_SUBDIRS,
    discover_projects,
    resolve_project_root,
)
from infrastructure.project.project_info import ProjectInfo
from infrastructure.project.project_info import build_project_info


def discover_qualified_names(repo_root: Path) -> list[str]:
    """Return a sorted list of qualified project names discovered under ``repo_root``."""
    projects = discover_projects(repo_root)
    return sorted(p.qualified_name for p in projects)


def _canonical_project_slug(slug: str, projects: Sequence[ProjectInfo]) -> str | None:
    """Return the discovered qualified slug for an exact or unique bare-name match."""
    exact = {project.qualified_name: project.qualified_name for project in projects}
    if slug in exact:
        return exact[slug]

    matches = [project.qualified_name for project in projects if project.name == slug]
    if not matches:
        return None
    priority = (
        f"active/{slug}",
        slug,
        f"templates/{slug}",
    )
    for candidate in priority:
        if candidate in matches:
            return candidate
    return sorted(matches)[0]


def validate_project_slug(slug: str, repo_root: Path) -> str:
    """Validate a user-supplied project slug against discovered projects.

    Rejects (in order):

    1. ``None`` / empty string
    2. embedded NUL bytes
    3. ``..`` anywhere (path traversal)
    4. leading ``/`` or ``-`` (absolute path or flag-spoofing)
    5. names not present in the discovered project list or an explicitly
       qualified, marker-bearing lifecycle tree

    Returns the validated slug verbatim on success.

    Raises:
        ValueError: with a precise reason for the rejection.
    """
    if not slug:
        raise ValueError("project slug must be a non-empty string")
    if "\x00" in slug:
        raise ValueError("project slug must not contain NUL bytes")
    if ".." in slug:
        raise ValueError(f"project slug must not contain '..': {slug!r}")
    if slug.startswith("/"):
        raise ValueError(f"project slug must not start with '/': {slug!r}")
    if slug.startswith("-"):
        raise ValueError(f"project slug must not start with '-': {slug!r}")

    projects = discover_projects(repo_root)
    resolved = _canonical_project_slug(slug, projects)
    if resolved is None:
        normalized = slug.replace("\\", "/")
        head = normalized.split("/", 1)[0]
        if "/" in normalized and head in NON_RENDERED_SUBDIRS:
            lifecycle_root = resolve_project_root(repo_root, normalized)
            has_markers = lifecycle_root.is_dir() and any(
                (lifecycle_root / marker).exists()
                for marker in ("src", "tests", "scripts", "manuscript", "docs/manuscript")
            )
            if has_markers:
                return normalized
    if resolved is None:
        available = sorted(p.qualified_name for p in projects)
        raise ValueError(f"project {slug!r} not found. Available: {', '.join(available) or '(none)'}")
    return resolved


def resolve_project_info(slug: str, repo_root: Path) -> ProjectInfo:
    """Resolve a validated rendered or qualified lifecycle project once."""
    qualified_name = validate_project_slug(slug, repo_root)
    for project in discover_projects(repo_root):
        if project.qualified_name == qualified_name:
            return project

    project_root = resolve_project_root(repo_root, qualified_name)
    program, separator, _name = qualified_name.rpartition("/")
    return build_project_info(project_root, program=program if separator else "")


def select_project_interactive(
    projects: Sequence[ProjectInfo],
    *,
    current: str | None = None,
    reader: Callable[[], str] = input,
    writer: TextIO | None = None,
) -> str | None:
    """Interactive project picker.

    Args:
        projects: Discovered projects to choose from.
        current: Currently-selected project (highlighted).
        reader: Zero-arg callable that returns the user input line. The
            production caller passes :func:`input`. Tests pass a closure
            over a queue of canned responses.
        writer: Optional text stream for the prompt UI. Defaults to ``None``
            (silent) which is what most tests want; production callers pass
            ``sys.stdout``.

    Returns:
        The qualified name of the selected project, or ``"all"`` if the
        user typed ``a``, or ``None`` if the user typed ``q``.
    """

    def _emit(line: str) -> None:
        if writer is not None:
            writer.write(line + "\n")

    if not projects:
        _emit("No projects available")
        return None

    while True:
        _emit("Available projects:")
        for idx, info in enumerate(projects):
            marker = "→" if info.qualified_name == current else " "
            _emit(f"  {marker} {idx}. {info.qualified_name}")
        _emit("  a. Run all projects")
        _emit("  q. Quit")

        if writer is not None:
            writer.write("Choice [index / a=all / q=quit]: ")
            writer.flush()

        try:
            choice = reader().strip()
        except EOFError:
            return None

        if not choice:
            continue
        if choice in {"q", "Q"}:
            return None
        if choice in {"a", "A"}:
            return "all"
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(projects):
                return projects[idx].qualified_name
        _emit(f"Invalid selection: {choice!r}")
