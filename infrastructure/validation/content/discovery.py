"""Unified markdown file discovery for validation subsystems."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from infrastructure.core.exceptions import FileNotFoundError, NotADirectoryError

MarkdownDiscoveryScope = Literal["tree", "repo", "link_audit"]

# Keep the legacy integrity-audit scope aligned with the canonical repository
# documentation scope. This is repeated here rather than imported from the
# ``docs`` package because ``infrastructure.validation.content`` is imported by
# that package during initialization; a module-level import would create a
# circular dependency. Update both lists together when adding a local-only
# documentation tree.
_LINK_AUDIT_EXCLUDE_PARTS: frozenset[str] = frozenset(
    {
        ".agents",
        ".benchmarks",
        ".cache",
        ".claude",
        ".codegraph",
        ".codex",
        ".cursor",
        ".git",
        ".mypy_cache",
        ".omo",
        ".provenance",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "_skill-eval",
        "__pycache__",
        "archive",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
        "ongoing",
        "output",
        "site-packages",
        "venv",
        "working",
    }
)

__all__ = [
    "MarkdownDiscoveryScope",
    "discover_markdown_files",
]


def discover_markdown_files(
    root: Path,
    *,
    scope: MarkdownDiscoveryScope = "tree",
    repo_root: Path | None = None,
) -> list[Path]:
    """Discover markdown files under *root* according to *scope*.

    Args:
        root: Directory to search (``tree``) or repository root (``repo`` / ``link_audit``).
        scope: ``tree`` — non-recursive ``*.md`` in one directory; ``repo`` — shared
            doc-scan exclusions; ``link_audit`` — link-checker exclusions.
        repo_root: Optional override when *root* is not the repository root for
            recursive scopes.

    Returns:
        Sorted list of markdown file paths.

    Raises:
        FileNotFoundError: When ``scope='tree'`` and *root* does not exist.
        NotADirectoryError: When ``scope='tree'`` and *root* is not a directory.
    """
    root = Path(root)

    if scope == "tree":
        if not root.exists():
            raise FileNotFoundError(
                f"Markdown directory not found: {root}",
                context={"directory": str(root)},
            )
        if not root.is_dir():
            raise NotADirectoryError(
                f"Path is not a directory: {root}",
                context={"path": str(root)},
            )
        return sorted(root.glob("*.md"))

    search_root = Path(repo_root) if repo_root is not None else root
    from infrastructure.validation.docs.scan_scope import DEFAULT_EXCLUDE_PARTS, iter_markdown_files

    exclude = DEFAULT_EXCLUDE_PARTS if scope == "repo" else _LINK_AUDIT_EXCLUDE_PARTS
    return iter_markdown_files([search_root], exclude_parts=exclude)
