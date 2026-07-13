"""Portability cleanup for text publication artifacts."""

from __future__ import annotations

import re
from pathlib import Path

PUBLICATION_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".csv", ".html", ".json", ".jsonl", ".log", ".md", ".svg", ".tex", ".txt", ".yaml", ".yml"}
)
_MACHINE_HOME_RE = re.compile(r"(?:/Users|/home)/[^/\s\"'<>]+")


def sanitize_machine_local_paths(root: Path) -> tuple[Path, ...]:
    """Replace machine-local home prefixes in text artifacts under ``root``.

    The replacement preserves the remainder of each path, so diagnostics stay
    useful while checked publication evidence remains clone-independent.
    Unreadable or non-UTF-8 files are left untouched.
    """
    if not root.is_dir() or root.is_symlink():
        return ()
    changed: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.lower() not in PUBLICATION_TEXT_SUFFIXES:
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        sanitized = _MACHINE_HOME_RE.sub("<home>", original)
        if sanitized == original:
            continue
        path.write_text(sanitized, encoding="utf-8")
        changed.append(path)
    return tuple(changed)


__all__ = ["PUBLICATION_TEXT_SUFFIXES", "sanitize_machine_local_paths"]
