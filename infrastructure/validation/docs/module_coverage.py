"""Verify each package's folder docs enumerate its public Python modules.

The doc-pair linter (:mod:`infrastructure.validation.docs.doc_pair_lint`) checks
that the ``AGENTS.md`` + ``README.md`` pair *exists*. This linter checks the
complementary invariant: that a package's folder docs actually *reference* the
functional modules sitting beside them, so ``AGENTS.md`` stays a faithful
technical index instead of drifting behind newly added modules.

Only the **public** surface is required. These are deliberately excluded because
they are not part of a package's documented public API:

* ``_``-prefixed modules — internal split-outs (often forced by the module
  line-count gate) that the public entry points re-export.
* ``__init__.py`` / ``__main__.py`` — package markers and CLI shims.
* ``test_*.py`` — test modules (documented by ``tests/`` docs, not here).

A module counts as documented when its stem appears as a whole word in any of
the folder-local docs (``AGENTS.md``, ``README.md``, ``SKILL.md``).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from infrastructure.validation.docs.doc_pair_lint import iter_doc_pair_candidate_dirs

# Roots whose directories carry functional Python modules that AGENTS.md indexes.
CODE_DOC_ROOTS: tuple[str, ...] = ("infrastructure", "scripts")

# Folder-local docs consulted for a module reference, in priority order.
LOCAL_DOC_FILENAMES: tuple[str, ...] = ("AGENTS.md", "README.md", "SKILL.md")


def is_public_module(name: str) -> bool:
    """Return True for a ``.py`` file that is part of a package's public surface."""
    return name.endswith(".py") and not name.startswith("_") and not name.startswith("test_")


def iter_public_modules(directory: Path) -> list[str]:
    """Return sorted public module filenames directly inside *directory*."""
    return sorted(p.name for p in directory.glob("*.py") if is_public_module(p.name))


def _local_docs_text(directory: Path) -> str:
    """Return the lower-cased concatenation of the folder-local doc files."""
    parts: list[str] = []
    for name in LOCAL_DOC_FILENAMES:
        doc = directory / name
        if doc.is_file():
            parts.append(doc.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts).lower()


def module_is_referenced(module_stem: str, docs_lower: str) -> bool:
    """Return True when *module_stem* appears as a whole word in *docs_lower*."""
    stem = module_stem.lower()
    return re.search(rf"(?<![a-z0-9_]){re.escape(stem)}(?![a-z0-9_])", docs_lower) is not None


@dataclass(frozen=True)
class ModuleDocGap:
    """A package whose folder docs omit one or more public modules."""

    package: Path
    documented: int
    total: int
    undocumented: tuple[str, ...]

    def format(self) -> str:
        """Return a human-readable one-line diagnostic."""
        return f"{self.package}: [{self.documented}/{self.total} documented] missing: {', '.join(self.undocumented)}"


def find_module_doc_gaps(
    repo_root: Path | str,
    *,
    roots: Sequence[str] = CODE_DOC_ROOTS,
) -> list[ModuleDocGap]:
    """Return packages whose ``AGENTS.md`` omits public modules, worst first.

    A directory is only considered when it carries an ``AGENTS.md`` and at least
    one public module. Directory scope reuses
    :func:`iter_doc_pair_candidate_dirs`, so the same generated/vendored trees
    the doc-pair linter skips are skipped here too.
    """
    repo = Path(repo_root).resolve()
    gaps: list[ModuleDocGap] = []
    for directory in iter_doc_pair_candidate_dirs(repo, roots=tuple(roots), include_repo_root=False):
        if not (directory / "AGENTS.md").is_file():
            continue
        modules = iter_public_modules(directory)
        if not modules:
            continue
        docs_lower = _local_docs_text(directory)
        undocumented = tuple(m for m in modules if not module_is_referenced(Path(m).stem, docs_lower))
        if undocumented:
            gaps.append(
                ModuleDocGap(
                    package=directory.relative_to(repo),
                    documented=len(modules) - len(undocumented),
                    total=len(modules),
                    undocumented=undocumented,
                )
            )
    gaps.sort(key=lambda g: len(g.undocumented), reverse=True)
    return gaps


__all__ = [
    "CODE_DOC_ROOTS",
    "LOCAL_DOC_FILENAMES",
    "ModuleDocGap",
    "find_module_doc_gaps",
    "is_public_module",
    "iter_public_modules",
    "module_is_referenced",
]
