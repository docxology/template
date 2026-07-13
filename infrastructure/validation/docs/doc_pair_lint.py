"""Validate folder-level ``AGENTS.md`` and ``README.md`` coverage.

The permanent template surface is intentionally documented directory-by-directory:
``README.md`` gives a quick human reference and ``AGENTS.md`` gives local
automation guidance. This linter checks that every content-bearing directory in
that permanent surface carries both files while skipping generated/local trees.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.docs.scan_scope import DEFAULT_EXCLUDE_PARTS, SKILL_EVAL_DIR_NAME

PERMANENT_TEMPLATE_ROOTS: tuple[str, ...] = (
    ".github",
    "docs",
    "infrastructure",
    "scripts",
    "tests",
    *(f"projects/{name}" for name in PUBLIC_PROJECT_NAMES),
)

DOC_PAIR_EXCLUDE_PARTS: frozenset[str] = frozenset(
    {
        *DEFAULT_EXCLUDE_PARTS,
        SKILL_EVAL_DIR_NAME,
        ".benchmarks",
        ".cache",
        ".cursor",
        ".hypothesis",
        ".lake",
    }
)

DOC_FILENAMES = {"AGENTS.md", "README.md"}

_VENDORED_EXCLUDED_ROOTS: tuple[tuple[str, ...], ...] = (("infrastructure", "steganography", "kmyth"),)


def _is_generated_tests_fixture_payload(path: Path) -> bool:
    """Return True for downloaded/generated fixture payloads under ``tests/fixtures``."""
    parts = path.parts
    for index, part in enumerate(parts):
        if part != "fixtures" or index == 0 or parts[index - 1] != "tests":
            continue
        rel_parts = parts[index + 1 :]
        if not rel_parts:
            return False
        fixture_root = rel_parts[0]
        if fixture_root == "timeseries":
            return True
        if fixture_root == "real_codebases":
            return len(rel_parts) >= 2 and rel_parts[1] not in DOC_FILENAMES
        return False
    return False


def _is_recorded_generation_fixture(path: Path) -> bool:
    """Return True for SIA replay trees under ``fixtures/recorded_generations``."""
    return "recorded_generations" in path.parts


def _contains_path_parts(path: Path, needle: tuple[str, ...]) -> bool:
    parts = path.parts
    if len(needle) > len(parts):
        return False
    for start in range(len(parts) - len(needle) + 1):
        if parts[start : start + len(needle)] == needle:
            return True
    return False


@dataclass(frozen=True)
class DocPairIssue:
    """A content directory missing one or both folder-level docs."""

    path: Path
    missing_readme: bool
    missing_agents: bool

    def format(self) -> str:
        """Return a human-readable one-line diagnostic."""
        missing = []
        if self.missing_readme:
            missing.append("README.md")
        if self.missing_agents:
            missing.append("AGENTS.md")
        return f"{self.path}: missing {', '.join(missing)}"


def is_doc_pair_excluded_path(
    path: Path,
    *,
    exclude_parts: Iterable[str] = DOC_PAIR_EXCLUDE_PARTS,
) -> bool:
    """Return True when *path* is outside permanent-template doc-pair scope."""
    excluded = set(exclude_parts)
    if any(_contains_path_parts(path, root) for root in _VENDORED_EXCLUDED_ROOTS):
        return True
    if _is_generated_tests_fixture_payload(path):
        return True
    if _is_recorded_generation_fixture(path):
        return True
    return any(part in excluded or part.endswith(".egg-info") for part in path.parts)


def _has_content(path: Path) -> bool:
    """Return True when *path* contains non-doc files or in-scope child dirs."""
    for child in path.iterdir():
        if is_doc_pair_excluded_path(child):
            continue
        if child.is_file() and child.name not in DOC_FILENAMES:
            return True
        if child.is_dir():
            return True
    return False


def iter_doc_pair_candidate_dirs(
    repo_root: Path | str,
    *,
    roots: Sequence[str] = PERMANENT_TEMPLATE_ROOTS,
    include_repo_root: bool = True,
) -> Iterator[Path]:
    """Yield in-scope content directories that should carry a doc pair."""
    repo = Path(repo_root).resolve()
    seen: set[Path] = set()

    if include_repo_root and _has_content(repo):
        seen.add(repo)
        yield repo

    for rel_root in roots:
        base = (repo / rel_root).resolve()
        if not base.is_dir() or is_doc_pair_excluded_path(base):
            continue
        for raw_directory, child_names, _ in os.walk(base, topdown=True, followlinks=False):
            directory = Path(raw_directory)
            child_names[:] = sorted(
                name
                for name in child_names
                if not (directory / name).is_symlink() and not is_doc_pair_excluded_path(directory / name)
            )
            if directory in seen or is_doc_pair_excluded_path(directory):
                continue
            if not _has_content(directory):
                continue
            seen.add(directory)
            yield directory


def find_doc_pair_issues(
    repo_root: Path | str,
    *,
    roots: Sequence[str] = PERMANENT_TEMPLATE_ROOTS,
) -> list[DocPairIssue]:
    """Return missing doc-pair diagnostics for the permanent template surface."""
    repo = Path(repo_root).resolve()
    issues: list[DocPairIssue] = []
    for directory in iter_doc_pair_candidate_dirs(repo, roots=roots):
        missing_readme = not (directory / "README.md").is_file()
        missing_agents = not (directory / "AGENTS.md").is_file()
        if missing_readme or missing_agents:
            issues.append(
                DocPairIssue(
                    path=directory.relative_to(repo),
                    missing_readme=missing_readme,
                    missing_agents=missing_agents,
                )
            )
    return issues


__all__ = [
    "DOC_PAIR_EXCLUDE_PARTS",
    "PERMANENT_TEMPLATE_ROOTS",
    "DocPairIssue",
    "find_doc_pair_issues",
    "is_doc_pair_excluded_path",
    "iter_doc_pair_candidate_dirs",
]
