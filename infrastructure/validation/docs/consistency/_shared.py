"""Shared types and helpers for documentation consistency checks."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.scan_scope import DEFAULT_EXCLUDE_PARTS

logger = get_logger(__name__)

DEFAULT_LONG_LIVED_DOC_ROOTS: tuple[str, ...] = (
    "docs",
    "infrastructure",
    ".github",
    "tests",
    "projects/template_code_project",
    "projects/template_prose_project",
)

DEFAULT_GHOST_EXCLUDE_PARTS: frozenset[str] = DEFAULT_EXCLUDE_PARTS | frozenset({"_generated", "audit", "streams"})

CONDITIONAL_PHRASES: tuple[str, ...] = (
    "rotating",
    "rotate",
    "rotates",
    "in progress",
    "archived",
    "archive",
    "when present",
    "when checked out",
    "is checked out",
    "if exists",
    "if checked out",
    "if truthy",
    "in the working tree",
    "previously",
    "formerly",
    "absent",
    "may rotate",
    "no longer",
    "for example",
    "e.g.",
    "e.g ",
    "guard",
    "skipping",
    "skipped",
    "hashfiles",
    "promote",
    "promoted",
    "checked out under",
    "when the working tree",
    "when this tree",
    "is present",
    "when ",
    "only when",
    "only if",
    "conditional on",
    "if `",
    "noqa: docs-lint",
)

MD_GLOB = "*.md"

FENCE_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,}).*?\n.*?\n[ \t]*(?P=fence)",
    re.MULTILINE | re.DOTALL,
)

NOQA_RE = re.compile(r"<!--\s*noqa:\s*docs-lint", re.IGNORECASE)
SHELL_NOQA_RE = re.compile(r"#\s*noqa:\s*docs-lint", re.IGNORECASE)


@dataclass(frozen=True)
class Inconsistency:
    """A single doc consistency issue."""

    file: Path
    line: int
    category: str
    detail: str

    def format(self) -> str:
        """Return a single-line summary."""
        return f"{self.file}:{self.line}: [{self.category}] {self.detail}"


def blank_fences(text: str) -> str:
    """Replace fenced code blocks with same-shape whitespace so line numbers stay stable."""

    def _blank(match: re.Match[str]) -> str:
        s = match.group(0)
        return "".join("\n" if ch == "\n" else " " for ch in s)

    return FENCE_RE.sub(_blank, text)


def line_has_noqa(line: str) -> bool:
    """True if the line carries an inline ``<!-- noqa: docs-lint -->`` comment."""
    return bool(NOQA_RE.search(line))


def line_is_conditional(line: str) -> bool:
    """True if *line* contains language that contextualizes a rotating-project mention."""
    low = line.lower()
    return any(phrase in low for phrase in CONDITIONAL_PHRASES)


def discover_infra_packages(repo_root: Path) -> list[str]:
    """Return sorted package names directly under ``infrastructure/``."""
    infra_root = repo_root / "infrastructure"
    if not infra_root.is_dir():
        return []
    return sorted(
        d.name
        for d in infra_root.iterdir()
        if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_") and (d / "__init__.py").is_file()
    )


def iter_long_lived_docs(
    repo_root: Path,
    extra_roots: Iterable[Path] | None = None,
    exclude_parts: Iterable[str] = DEFAULT_GHOST_EXCLUDE_PARTS,
) -> list[Path]:
    """Yield Markdown files under long-lived doc roots."""
    roots: list[Path] = []
    for sub in DEFAULT_LONG_LIVED_DOC_ROOTS:
        candidate = repo_root / sub
        if candidate.is_dir():
            roots.append(candidate)
    if repo_root.is_dir():
        for md in repo_root.glob(MD_GLOB):
            roots.append(md)
    if extra_roots:
        roots.extend(Path(p) for p in extra_roots)

    excluded = set(exclude_parts)
    out: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root.is_file() and root.suffix.lower() == ".md":
            if root not in seen:
                seen.add(root)
                out.append(root)
            continue
        if not root.is_dir():
            continue
        for md in root.rglob(MD_GLOB):
            if any(part in excluded for part in md.parts):
                continue
            if md in seen:
                continue
            seen.add(md)
            out.append(md)
    return sorted(out)


def read_markdown(path: Path) -> str | None:
    """Read a markdown file, returning None on I/O or decode failure."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.debug("skipping %s: %s", path, exc)
        return None
