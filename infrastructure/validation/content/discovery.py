"""Unified markdown file discovery for validation subsystems."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from infrastructure.core.exceptions import FileNotFoundError, NotADirectoryError

MarkdownDiscoveryScope = Literal["tree", "repo", "link_audit"]

_LINK_AUDIT_EXCLUDE_PARTS: frozenset[str] = frozenset(
    {
        ".git",
        ".omo",
        ".pytest_cache",
        "__pycache__",
        "htmlcov",
        "node_modules",
        "output",
        # Non-rendered typed project subfolders (private symlinked work). Keep in
        # sync with discovery.NON_RENDERED_SUBDIRS.
        "archive",
        "other",
        "published",
        "working",
        "site-packages",
        ".venv",
        "venv",
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
