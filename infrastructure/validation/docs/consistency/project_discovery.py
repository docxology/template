"""Project discovery documentation contract checks."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.validation.docs.consistency._shared import (
    Inconsistency,
    blank_fences,
    iter_long_lived_docs,
    line_has_noqa,
    read_markdown,
)

_CONFIG_DISCOVERY_RE = re.compile(
    r"project[^\n|.]{0,80}(?:auto-?discover|discover|finds?)[^\n|.]{0,120}"
    r"(?:manuscript/config\.yaml|`manuscript/config\.yaml`)"
    r"|(?:auto-?discover|auto-?discovered)[^\n|.]{0,120}"
    r"(?:manuscript/config\.yaml|`manuscript/config\.yaml`)"
    r"|(?:manuscript/config\.yaml|`manuscript/config\.yaml`)[^\n|.]{0,120}"
    r"project[^\n|.]{0,80}(?:auto-?discover|discover)",
    re.IGNORECASE,
)


def _mentions_required_markers(line: str) -> bool:
    low = line.lower()
    return "src/" in low and "tests/" in low


def check_project_discovery_claims(repo_root: Path) -> list[Inconsistency]:
    """Flag docs that describe ``manuscript/config.yaml`` as the project discovery predicate.

    The live discovery contract is stricter: ``validate_project_structure``
    requires ``src/`` with Python files and ``tests/``. ``manuscript/config.yaml``
    is metadata/rendering configuration, not the low-level discovery condition.
    """
    issues: list[Inconsistency] = []
    for md in iter_long_lived_docs(repo_root):
        raw = read_markdown(md)
        if raw is None:
            continue
        text = blank_fences(raw)
        lines = text.splitlines()
        for line_no, line in enumerate(lines, start=1):
            if line_has_noqa(line) or not _CONFIG_DISCOVERY_RE.search(line):
                continue
            window = " ".join(lines[max(0, line_no - 2) : min(len(lines), line_no + 2)])
            if _mentions_required_markers(window):
                continue
            issues.append(
                Inconsistency(
                    file=md,
                    line=line_no,
                    category="project-discovery",
                    detail=(
                        "describes manuscript/config.yaml as the discovery predicate; "
                        "live discovery requires src/ with Python files and tests/, while "
                        "config.yaml supplies metadata/render settings"
                    ),
                )
            )
    return issues
