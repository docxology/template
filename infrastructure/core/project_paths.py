"""Project-path resolution primitives — the foundation layer's view of ``projects/``.

These are pure ``pathlib`` helpers with no dependency on the higher-level
``infrastructure.project`` package, so true-foundation modules
(``core.files``, ``core.runtime``) can resolve project directories without the
foundation importing upward into ``project`` (which would create a
``core ↔ project`` layering cycle). ``infrastructure.project.discovery``
re-exports these names, so existing ``from infrastructure.project.discovery
import resolve_project_root`` call sites keep working unchanged.
"""

from __future__ import annotations

from pathlib import Path

#: Typed subfolders under ``projects/`` that hold non-rendered lifecycle mirrors.
#: Their nested projects are deliberately excluded from discovery so they never
#: enter the render set. Only ``templates/`` (public exemplars) and optional
#: ``active/`` hot-seat entries are discovered. ``ongoing/`` holds long-lived
#: projects with no publication target — visible and qualified-resolvable
#: (``ongoing/<name>``) but never default-rendered. Keep in sync with
#: :data:`infrastructure.project.linking.LIFECYCLE_LINK_DIRS`.
NON_RENDERED_SUBDIRS: frozenset[str] = frozenset({"working", "ongoing", "published", "archive", "other"})


def find_repo_root() -> Path:
    """Return the repository root (the directory containing ``infrastructure/``).

    This module lives at ``infrastructure/core/project_paths.py``, so the repo
    root is two parents up from this file. Centralising the computation here lets
    callers stop hard-coding their own ``Path(__file__).resolve().parents[N]``
    depth, which is fragile under file moves and easy to get off by one.
    """
    return Path(__file__).resolve().parents[2]


def resolve_project_root(repo_root: Path | str, project_name: str) -> Path:
    """Return the directory for *project_name*, preferring the hot seat over WIP trees.

    Use this when a tool should find a work-in-progress tree (for example COGANT) that has not
    been promoted to ``projects/active/`` yet. If ``projects/active/<project_name>`` exists and
    looks like a project source tree, that path wins; otherwise
    ``projects/working/<project_name>`` is used when present, then a flat
    standalone ``projects/<project_name>`` tree. A skeletal generated-output
    directory does not shadow an actual WIP source tree.

    If none of those exist, returns ``projects/active/<project_name>`` so callers get a
    stable path for error messages.

    Args:
        repo_root: Repository root (directory containing ``infrastructure/``).
        project_name: Final path segment (e.g. ``"cogant"``).

    Returns:
        Absolute resolved path to the project directory.
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)

    def has_project_markers(path: Path) -> bool:
        """Return True if the directory contains project marker files."""
        return any((path / marker).exists() for marker in ("src", "tests", "scripts", "manuscript"))

    # A name that already carries a typed-subfolder prefix (e.g. ``active/demo``,
    # ``working/draft``, ``templates/template_code_project``) is resolved directly
    # under ``projects/`` without re-prepending the hot-seat prefix.
    head = project_name.replace("\\", "/").split("/", 1)[0]
    if head in (NON_RENDERED_SUBDIRS | {"active", "templates"}):
        qualified = repo_root / "projects" / project_name
        if qualified.is_dir():
            return qualified.resolve()
        return qualified

    primary = repo_root / "projects" / "active" / project_name
    if primary.is_dir() and has_project_markers(primary):
        return primary.resolve()
    wip = repo_root / "projects" / "working" / project_name
    if wip.is_dir():
        return wip.resolve()
    # A flat standalone tree only wins outright when it carries source markers.
    # An output-only flat skeleton (e.g. a stale ``projects/<name>/output/``
    # minted by a prior run) must not shadow a real exemplar under
    # ``projects/templates/`` — that shadow made bare-name consumers such as
    # ``build_evidence_graph`` silently see an empty project.
    flat = repo_root / "projects" / project_name
    if flat.is_dir() and has_project_markers(flat):
        return flat.resolve()
    # Public canonical exemplars live under ``projects/templates/<name>`` and
    # must resolve by bare name as well. Without this, an output-only shadow
    # under ``projects/active/<name>`` (or the stable error-path fallback below)
    # shadows a real exemplar source tree, so consumers such as
    # ``infrastructure.autoresearch.build_autoresearch_plan`` silently load
    # default config instead of the exemplar's own. Checked after the
    # hot-seat/WIP/flat trees so an actually-promoted project still wins.
    templated = repo_root / "projects" / "templates" / project_name
    if templated.is_dir() and has_project_markers(templated):
        return templated.resolve()
    # Marker-less flat tree with no exemplar counterpart: keep the historical
    # behavior of returning it so bespoke layouts and error paths still resolve.
    if flat.is_dir():
        return flat.resolve()
    if primary.is_dir():
        return primary.resolve()
    return primary


__all__ = ["NON_RENDERED_SUBDIRS", "find_repo_root", "resolve_project_root"]
