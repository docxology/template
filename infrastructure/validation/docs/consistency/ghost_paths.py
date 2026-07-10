"""Ghost-project path reference checks."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from infrastructure.project.discovery import discover_projects
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
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


#: Typed lifecycle subfolders that sit directly under ``projects/``. References
#: like ``projects/<type>/`` are structural and always allowed; the project name
#: to validate is the segment *after* the type prefix. Keep ``archive`` in sync
#: with discovery.NON_RENDERED_SUBDIRS plus the rendered ``active``/``templates``.
TYPED_PROJECT_SUBDIRS: frozenset[str] = frozenset(
    {"active", "working", "ongoing", "published", "archive", "other", "templates"}
)


def check_no_ghost_projects(
    repo_root: Path,
    canonical: tuple[str, ...] = PUBLIC_PROJECT_NAMES,
    extra_active: Iterable[str] | None = None,
) -> list[Inconsistency]:
    """Flag unconditional ``projects/<name>/...`` references for non-active projects.

    Recognizes the typed-subfolder layout: ``projects/<type>/<name>/`` references
    are checked against ``<name>`` (the type prefix itself is structural). The
    non-rendered typed subfolders (``working``/``published``/``archive``/
    ``other``) hold rotating private work, so any name beneath them is allowed.
    """
    active_qualified_names = {p.qualified_name for p in discover_projects(repo_root)}
    if extra_active:
        active_qualified_names.update(extra_active)
    allow = active_qualified_names | set(canonical)

    # Optional typed-subfolder prefix, then the project-name segment.
    pattern = re.compile(
        r"(?<![A-Za-z0-9_/])projects/"
        r"(?:(?P<type>active|working|ongoing|published|archive|other|templates)/)?"
        r"(?P<name>\{[^}]+\}|<[^>]+>|[A-Za-z0-9_][A-Za-z0-9_.-]*)/"
    )

    issues: list[Inconsistency] = []
    for md in iter_long_lived_docs(repo_root):
        raw = read_markdown(md)
        if raw is None:
            continue
        text = blank_fences(raw)
        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            if line_is_conditional(raw_line) or line_has_noqa(raw_line):
                continue
            for match in pattern.finditer(raw_line):
                prefix = match.group("type")
                # Non-rendered typed subfolders hold rotating private work — any
                # name beneath them is allowed (they are not ghost references).
                if prefix in {"working", "ongoing", "published", "archive", "other"}:
                    continue
                name = match.group("name")
                # A bare ``projects/<subfolder>/`` reference (no project name after
                # the typed subfolder) is structural, not a project — the regex
                # captures the subfolder itself as ``name`` when nothing follows.
                if prefix is None and name in TYPED_PROJECT_SUBDIRS:
                    continue
                if name in allow:
                    continue
                if name in {"AGENTS.md", "README.md"}:
                    continue
                if is_placeholder_name(name):
                    continue
                if prefix is None:
                    project_ref = name
                    displayed = f"projects/{name}/"
                else:
                    project_ref = f"{prefix}/{name}"
                    displayed = f"projects/{project_ref}/"
                if project_ref in allow:
                    continue
                issues.append(
                    Inconsistency(
                        file=md,
                        line=line_no,
                        category="ghost-project",
                        detail=(
                            f"hard-codes '{displayed}' but '{project_ref}' is not in "
                            "docs/_generated/active_projects.md and is not a "
                            "canonical exemplar"
                        ),
                    )
                )
    return issues
