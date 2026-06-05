"""Regression tests for decision-memory documentation propagation."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.docs.consistency.memory_decision import (
    check_memory_decision_rule_links,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
RULE_LINK = "memory_and_decision_records.md"


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_memory_decision_rule_doc_is_linked_from_standards_hub() -> None:
    rule_doc = REPO_ROOT / "docs/rules/memory_and_decision_records.md"

    assert rule_doc.is_file()
    assert RULE_LINK in _read("docs/rules/AGENTS.md")
    assert RULE_LINK in _read("docs/rules/README.md")


def test_project_setup_docs_link_memory_decision_contract() -> None:
    for relative in (
        "docs/development/code-review-checklist.md",
        "docs/development/contributing.md",
        "docs/guides/new-project-setup.md",
        "docs/guides/new-project-one-shot-prompt.md",
        "projects/AGENTS.md",
    ):
        assert RULE_LINK in _read(relative), relative


def test_public_exemplar_agent_docs_link_memory_decision_contract() -> None:
    missing: list[str] = []
    for project_name in PUBLIC_PROJECT_NAMES:
        relative = f"projects/{project_name}/AGENTS.md"
        if RULE_LINK not in _read(relative):
            missing.append(relative)

    assert missing == []


def test_memory_decision_lint_flags_missing_required_link(tmp_path: Path) -> None:
    doc = tmp_path / "docs/rules/AGENTS.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Rules\n\nAgent policy lives here.\n", encoding="utf-8")

    issues = check_memory_decision_rule_links(
        tmp_path,
        required_relative_docs=("docs/rules/AGENTS.md",),
        public_project_names=(),
    )

    assert len(issues) == 1
    assert issues[0].category == "memory-decision-rule"
    assert "memory_and_decision_records.md" in issues[0].detail


def test_memory_decision_lint_accepts_required_link(tmp_path: Path) -> None:
    doc = tmp_path / "docs/rules/AGENTS.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(
        "# Rules\n\nSee [memory](memory_and_decision_records.md).\n",
        encoding="utf-8",
    )

    issues = check_memory_decision_rule_links(
        tmp_path,
        required_relative_docs=("docs/rules/AGENTS.md",),
        public_project_names=(),
    )

    assert issues == []
