"""Decision-memory documentation propagation checks."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.docs.consistency._shared import Inconsistency, read_markdown

MEMORY_DECISION_RULE = "docs/rules/memory_and_decision_records.md"
MEMORY_DECISION_BASENAME = "memory_and_decision_records.md"

DEFAULT_REQUIRED_MEMORY_RULE_DOCS: tuple[str, ...] = (
    "docs/rules/AGENTS.md",
    "docs/rules/README.md",
    "docs/development/code-review-checklist.md",
    "docs/development/contributing.md",
    "docs/guides/new-project-setup.md",
    "docs/guides/new-project-one-shot-prompt.md",
    "projects/AGENTS.md",
)


def _has_memory_rule_link(text: str) -> bool:
    return MEMORY_DECISION_BASENAME in text or MEMORY_DECISION_RULE in text


def _line_for_end(path: Path) -> int:
    text = read_markdown(path)
    return len(text.splitlines()) if text else 1


def check_memory_decision_rule_links(
    repo_root: Path,
    *,
    required_relative_docs: Sequence[str] = DEFAULT_REQUIRED_MEMORY_RULE_DOCS,
    public_project_names: Sequence[str] = PUBLIC_PROJECT_NAMES,
) -> list[Inconsistency]:
    """Flag agent/workflow docs that omit the decision-memory rule link."""
    issues: list[Inconsistency] = []

    for relative in required_relative_docs:
        doc = repo_root / relative
        if not doc.is_file():
            continue
        text = read_markdown(doc)
        if text is None or _has_memory_rule_link(text):
            continue
        issues.append(
            Inconsistency(
                file=doc,
                line=_line_for_end(doc),
                category="memory-decision-rule",
                detail=(
                    "agent or workflow policy doc should link to "
                    f"{MEMORY_DECISION_RULE} so WHY comments, ADRs, local memory, "
                    "failure autopsies, selective ignorance, and negative controls "
                    "share one contract"
                ),
            )
        )

    for project_name in public_project_names:
        doc = repo_root / "projects" / project_name / "AGENTS.md"
        if not doc.is_file():
            continue
        text = read_markdown(doc)
        if text is None or _has_memory_rule_link(text):
            continue
        issues.append(
            Inconsistency(
                file=doc,
                line=_line_for_end(doc),
                category="memory-decision-rule",
                detail=(
                    "public exemplar AGENTS.md should link to "
                    f"{MEMORY_DECISION_RULE} so project-scale agent guidance inherits "
                    "the repo decision-memory and RedTeam negative-control contract"
                ),
            )
        )

    return issues


__all__ = [
    "DEFAULT_REQUIRED_MEMORY_RULE_DOCS",
    "MEMORY_DECISION_BASENAME",
    "MEMORY_DECISION_RULE",
    "check_memory_decision_rule_links",
]
