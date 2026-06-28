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
        ".codex",
        ".git",
        ".mypy_cache",
        ".omo",
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


def iter_markdown_files(
    roots: Iterable[Path],
    *,
    exclude_parts: Iterable[str] = DEFAULT_EXCLUDE_PARTS,
    exclude_globs: Iterable[str] = (),
) -> list[Path]:
    """Return Markdown files under *roots* while applying shared exclusions."""
    seen: set[Path] = set()
    out: list[Path] = []
    globs = tuple(exclude_globs)

    for root in roots:
        root = Path(root).resolve()
        candidates = [root] if root.is_file() else root.rglob("*.md") if root.is_dir() else []
        for md in candidates:
            if md.suffix.lower() != ".md":
                continue
            if should_exclude_path(md, exclude_parts):
                continue
            if any(md.match(glob) for glob in globs):
                continue
            if md in seen:
                continue
            seen.add(md)
            out.append(md)

    return sorted(out)


__all__ = ["DEFAULT_EXCLUDE_PARTS", "SKILL_EVAL_DIR_NAME", "iter_markdown_files", "should_exclude_path"]
