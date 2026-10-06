"""Confined paths for trusted child source, exports, and runtime receipts."""

from __future__ import annotations

from pathlib import Path, PurePosixPath


def confined_path(root: Path, relative: str, *, regular: bool = False) -> Path:
    """Reject absolute paths, traversal, symlink components, and nonregular files."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("custody path must be a nonempty normalized relative path")
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or ".." in parsed.parts or parsed.as_posix() != relative or relative == ".":
        raise ValueError("custody path must be a normalized confined relative path")
    root = root.resolve()
    selected = root
    for component in parsed.parts:
        selected /= component
        if selected.is_symlink():
            raise ValueError("custody path must not contain symlinks")
    if not selected.resolve().is_relative_to(root):
        raise ValueError("custody path escapes its source root")
    if regular and not selected.is_file():
        raise ValueError("custody requires a regular existing file")
    return selected
