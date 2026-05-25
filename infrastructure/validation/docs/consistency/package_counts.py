"""Infrastructure package-count claim checks."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.validation.docs.consistency._shared import (
    Inconsistency,
    blank_fences,
    discover_infra_packages,
    iter_long_lived_docs,
    line_has_noqa,
    read_markdown,
)

_PACKAGE_COUNT_LINE_RE = re.compile(
    r"^(?=.*(?:\b(?:Python|importable|subpackages)\b|`infrastructure/`)).*?"
    r"(?:\*\*|__|`)?(?P<n>\d{2,}|[2-9])(?:\*\*|__|`)?"
    r"(?:\s+`infrastructure/`)?\s+"
    r"(?:top-level\s+)?(?:importable\s+)?(?:Python\s+)?(?:sub)?packages\b.*$",
    re.IGNORECASE | re.MULTILINE,
)
_SUBPACKAGE_COUNT_LINE_RE = re.compile(
    r"^.*?(?:\*\*|__|`)?(?P<n>\d{2,}|[2-9])(?:\*\*|__|`)?\s+subpackages\b.*?infrastructure.*$",
    re.IGNORECASE | re.MULTILINE,
)
_INFRASTRUCTURE_AREA_COUNT_LINE_RE = re.compile(
    r"^.*?(?:\*\*|__|`)?(?P<n>\d{2,}|[2-9])(?:\*\*|__|`)?\s+"
    r"documented\s+infrastructure\s+areas\b.*$",
    re.IGNORECASE | re.MULTILINE,
)
_PY_COUNT_RE = re.compile(r"\b\d{3}\s*(?:`?\.py`?|Python)\s+files\b", re.IGNORECASE)


def check_module_count_claims(repo_root: Path, expected_count: int | None = None) -> list[Inconsistency]:
    """Verify Markdown claims about ``N Python (sub)packages`` match reality."""
    expected = expected_count if expected_count is not None else len(discover_infra_packages(repo_root))
    issues: list[Inconsistency] = []
    for md in iter_long_lived_docs(repo_root):
        raw = read_markdown(md)
        if raw is None:
            continue
        text = blank_fences(raw)
        seen_lines: set[int] = set()
        for regex in (
            _PACKAGE_COUNT_LINE_RE,
            _SUBPACKAGE_COUNT_LINE_RE,
            _INFRASTRUCTURE_AREA_COUNT_LINE_RE,
        ):
            for match in regex.finditer(text):
                claimed = int(match.group("n"))
                if claimed != expected:
                    line = text[: match.start()].count("\n") + 1
                    if line in seen_lines:
                        continue
                    seen_lines.add(line)
                    line_text = text.splitlines()[line - 1] if 0 < line <= len(text.splitlines()) else ""
                    if line_has_noqa(line_text):
                        continue
                    issues.append(
                        Inconsistency(
                            file=md,
                            line=line,
                            category="module-count",
                            detail=(f"claims {claimed} Python (sub)packages but infrastructure/ ships {expected}"),
                        )
                    )
    return issues


def check_canonical_count_singularity(repo_root: Path) -> list[Inconsistency]:
    """Flag a bare ``NNN .py files`` literal outside canonical_facts.md."""
    from infrastructure.validation.docs.consistency._shared import SHELL_NOQA_RE

    canonical = repo_root / "docs" / "_generated" / "canonical_facts.md"
    issues: list[Inconsistency] = []
    for md in iter_long_lived_docs(repo_root):
        if md.resolve() == canonical.resolve():
            continue
        raw = read_markdown(md)
        if raw is None:
            continue
        for n, line in enumerate(raw.splitlines(), 1):
            if _PY_COUNT_RE.search(line) and not (line_has_noqa(line) or SHELL_NOQA_RE.search(line)):
                issues.append(
                    Inconsistency(
                        file=md,
                        line=n,
                        category="count-singularity",
                        detail=(
                            "hard-codes a volatile infrastructure .py-file count — link to "
                            "docs/_generated/canonical_facts.md instead (it drifts as the tree "
                            "changes); add `# noqa: docs-lint` only for a measured, dated note"
                        ),
                    )
                )
    return issues
