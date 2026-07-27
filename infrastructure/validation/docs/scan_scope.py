"""Shared repository documentation-scan scope.

Documentation and link validators should agree on which local paths are part of
the long-lived repository surface. Generated outputs, the non-rendered typed
project subfolders (``projects/working``, ``projects/published``,
``projects/archive``, ``projects/other`` — private symlinked work), virtual
environments, and agent worktrees are intentionally excluded so local state does
not create thousands of irrelevant diagnostics.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

DEFAULT_EXCLUDE_PARTS: frozenset[str] = frozenset(
    {
        ".agents",
        ".benchmarks",
        ".cache",
        ".claude",
        ".codegraph",
        ".codex",
        ".git",
        ".mypy_cache",
        ".omo",
        ".provenance",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "_skill-eval",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
        "output",
        # Non-rendered typed project subfolders (private symlinked work). Keep in
        # sync with infrastructure.project.discovery.NON_RENDERED_SUBDIRS.
        "archive",
        "other",
        "published",
        "working",
        "site-packages",
        "venv",
    }
)

# Regenerated skill-eval harness output under docs/prompts/_skill-eval/ (fixture
# response.md files with intentionally wrong relative links). Excluded from
# cross-link and doc-pair lint like output/ and _generated/.
SKILL_EVAL_DIR_NAME: str = "_skill-eval"


def should_exclude_path(path: Path, exclude_parts: Iterable[str] = DEFAULT_EXCLUDE_PARTS) -> bool:
    """Return True when any path component is outside the doc-scan scope."""
    excluded = set(exclude_parts)
    return any(part in excluded for part in path.parts)


def _discover_repo_root(roots: Iterable[Path]) -> Path | None:
    """Walk up from *roots* to the nearest directory holding ``.gitmodules``."""
    for root in roots:
        for candidate in (root, *root.parents):
            if (candidate / ".gitmodules").is_file():
                return candidate
    return None


def submodule_paths(repo_root: Path) -> frozenset[Path]:
    """Return absolute paths of git submodules declared in ``.gitmodules``.

    Submodule trees are upstream third-party checkouts. This repository cannot fix
    a defect in their documentation and must not edit it — an edit would be lost on
    the next ``git submodule update`` — so their Markdown is outside the doc-scan
    surface.
    """
    gitmodules = repo_root / ".gitmodules"
    if not gitmodules.is_file():
        return frozenset()
    paths: set[Path] = set()
    for line in gitmodules.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped.startswith("path"):
            continue
        _, _, value = stripped.partition("=")
        value = value.strip()
        if value:
            paths.add((repo_root / value).resolve())
    return frozenset(paths)


def _is_within_submodule(path: Path, submodules: frozenset[Path]) -> bool:
    """True when *path* lies inside any declared submodule tree."""
    return any(path == sub or sub in path.parents for sub in submodules)


def iter_markdown_files(
    roots: Iterable[Path],
    *,
    exclude_parts: Iterable[str] = DEFAULT_EXCLUDE_PARTS,
    exclude_globs: Iterable[str] = (),
    repo_root: Path | None = None,
) -> list[Path]:
    """Return Markdown files under *roots* while applying shared exclusions.

    Exclusions are evaluated against the path RELATIVE to its scan root, never
    the absolute path: a checkout whose own location contains an excluded
    component (agent worktrees live under ``.claude/worktrees/<name>/``) must
    not have its entire tree silently excluded — that failure mode made every
    doc gate riding this discovery return a vacuous pass in worktrees.
    """
    seen: set[Path] = set()
    out: list[Path] = []
    globs = tuple(exclude_globs)
    resolved_roots = [Path(root).resolve() for root in roots]

    if repo_root is None:
        repo_root = _discover_repo_root(resolved_roots)
    submodules = submodule_paths(repo_root) if repo_root is not None else frozenset()

    for root in resolved_roots:
        candidates = [root] if root.is_file() else root.rglob("*.md") if root.is_dir() else []
        for md in candidates:
            if md.suffix.lower() != ".md":
                continue
            try:
                scoped = md.relative_to(root)
            except ValueError:
                scoped = md
            if should_exclude_path(scoped, exclude_parts):
                continue
            if submodules and _is_within_submodule(md, submodules):
                continue
            if any(md.match(glob) for glob in globs):
                continue
            if md in seen:
                continue
            seen.add(md)
            out.append(md)

    return sorted(out)


__all__ = ["DEFAULT_EXCLUDE_PARTS", "SKILL_EVAL_DIR_NAME", "iter_markdown_files", "should_exclude_path"]
