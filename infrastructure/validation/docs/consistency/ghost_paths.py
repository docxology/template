"""Ghost-project path reference checks."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from infrastructure.project.discovery import discover_projects
from infrastructure.validation.docs.consistency._shared import (
    Inconsistency,
    blank_fences,
    iter_long_lived_docs,
    line_has_noqa,
    line_is_conditional,
    read_markdown,
)

STATIC_PLACEHOLDER_NAMES: frozenset[str] = frozenset(
    {
        "biology_textbook",
        "template",
        "code_project",
        "prose_project",
        "search_project",
        "research",
        "myresearch",
        "name",
        "project",
        "project_name",
        "PROJECT",
        "PROJECT_NAME",
        "PROJECT_SLUG",
    }
)


def is_placeholder_name(name: str) -> bool:
    """Return True if *name* looks like a template placeholder rather than a real project."""
    if "<" in name or "{" in name or ">" in name or "}" in name:
        return True
    if name.isupper():
        return True
    if name in STATIC_PLACEHOLDER_NAMES:
        return True
    lower = name.lower()
    for prefix in ("my_", "your_", "example_", "sample_", "custom_", "foo", "bar"):
        if lower.startswith(prefix):
            return True
    return False


def check_no_ghost_projects(
    repo_root: Path,
    canonical: tuple[str, ...] = (
        "template_code_project",
        "template_prose_project",
        "template_search_project",
    ),
    extra_active: Iterable[str] | None = None,
) -> list[Inconsistency]:
    """Flag unconditional ``projects/<name>/...`` references for non-active projects."""
    active_names = {p.name for p in discover_projects(repo_root)}
    if extra_active:
        active_names.update(extra_active)
    archive_root = repo_root / "projects_archive"
    archived_names = {p.name for p in archive_root.iterdir() if p.is_dir()} if archive_root.is_dir() else set()
    allow = active_names | set(canonical) | archived_names

    pattern = re.compile(r"(?<![A-Za-z0-9_/])projects/(?P<name>\{[^}]+\}|<[^>]+>|[A-Za-z0-9_][A-Za-z0-9_.-]*)/")

    issues: list[Inconsistency] = []
    for md in iter_long_lived_docs(repo_root):
        raw = read_markdown(md)
        if raw is None:
            continue
        text = blank_fences(raw)
        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            if line_is_conditional(raw_line) or line_has_noqa(raw_line):
                continue
            if "projects_archive/" in raw_line:
                continue
            for match in pattern.finditer(raw_line):
                name = match.group("name")
                if name in allow:
                    continue
                if name in {"AGENTS.md", "README.md"}:
                    continue
                if is_placeholder_name(name):
                    continue
                issues.append(
                    Inconsistency(
                        file=md,
                        line=line_no,
                        category="ghost-project",
                        detail=(
                            f"hard-codes 'projects/{name}/' but '{name}' is not in "
                            "docs/_generated/active_projects.md and is not a "
                            "canonical exemplar"
                        ),
                    )
                )
    return issues
