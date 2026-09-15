"""Docs-invariant test for docs/rules/evidence_validation.md (lane evidence-rule).

Real file reads only - no mocks, per repo policy. Fails provably when the
rule file is missing, loses one of its three named invariants, or is no
longer linked from tests/regression/AGENTS.md's Related ("See Also") list.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RULE_PATH = REPO_ROOT / "docs" / "rules" / "evidence_validation.md"
REGRESSION_AGENTS = REPO_ROOT / "tests" / "regression" / "AGENTS.md"

LINK_TEXT = "[`../../docs/rules/evidence_validation.md`](../../docs/rules/evidence_validation.md)"

INVARIANT_MARKERS = {
    "run logs as evidence": "Run logs are the evidence channel",
    "exit status is not a result": "Exit status is not a result",
    "truncated output is not evidence of absence": ("Truncated output is not evidence of absence"),
}


@pytest.mark.parametrize("label,marker", sorted(INVARIANT_MARKERS.items()))
def test_rule_file_contains_named_invariant(label: str, marker: str) -> None:
    """Each of the three named invariants must appear verbatim in the rule."""
    assert RULE_PATH.is_file(), f"missing rule file: {RULE_PATH}"
    text = RULE_PATH.read_text()
    assert marker in text, f"rule file lost the '{label}' invariant"


def test_rule_file_linked_from_regression_agents() -> None:
    """The rule must stay linked from tests/regression/AGENTS.md Related list."""
    assert REGRESSION_AGENTS.is_file()
    text = REGRESSION_AGENTS.read_text()
    assert LINK_TEXT in text, "tests/regression/AGENTS.md no longer links docs/rules/evidence_validation.md"
