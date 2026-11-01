"""Composition JSON ordinals must be integers, without numeric coercion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.rendering.manuscript_composition import (
    COMBINED_RELATIVE_PATH,
    COMPOSITION_RELATIVE_PATH,
    read_manuscript_composition,
    write_manuscript_composition,
)

ALGORITHMS = (
    "web-renderer-combine-v1",
    "shared-combined-markdown-v1",
    "web-renderer-paper-frontmatter-v1",
    "shared-paper-frontmatter-markdown-v1",
)


def _evidence(project: Path, algorithm: str, input_root: str = "manuscript") -> Path:
    """Produce real evidence from two distinct files and a combined document."""
    (project / "manuscript").mkdir(parents=True)
    manuscript = project / input_root
    manuscript.mkdir(parents=True, exist_ok=True)
    first = manuscript / "01_model.md"
    second = manuscript / "02_execution.md"
    first.write_text("# Model\n\nA categorical model.\n", encoding="utf-8")
    second.write_text("# Execution\n\nExplicit backend admission.\n", encoding="utf-8")
    combined = project / COMBINED_RELATIVE_PATH
    combined.parent.mkdir(parents=True)
    combined.write_bytes(first.read_bytes() + b"\n" + second.read_bytes())
    write_manuscript_composition(project, "ordinal-fixture", [first, second], combined, algorithm=algorithm)
    return project / COMPOSITION_RELATIVE_PATH


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("input_root", ("manuscript", "output/manuscript"))
def test_integer_ordinals_preserve_evidence_bytes(tmp_path: Path, algorithm: str, input_root: str) -> None:
    evidence = _evidence(tmp_path, algorithm, input_root)
    before = evidence.read_bytes()
    expected = json.loads(before)
    composition = read_manuscript_composition(evidence)
    assert [row.ordinal for row in composition.ordered_inputs] == [1, 2]
    assert all(type(row.ordinal) is int for row in composition.ordered_inputs)
    assert composition.algorithm == algorithm
    assert composition.input_root_kind == ("source" if input_root == "manuscript" else "hydrated")
    assert composition.to_dict() == expected
    assert evidence.read_bytes() == before


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize(
    ("row_index", "invalid"),
    (
        (0, True),
        (0, False),
        (0, 1.0),
        (0, 1.5),
        (0, "1"),
        (0, None),
        (0, 0),
        (0, -1),
        (0, 2),
        (1, True),
        (1, 2.0),
        (1, "2"),
        (1, 1),
        (1, 3),
    ),
)
def test_noninteger_or_noncontiguous_ordinals_are_refused(
    tmp_path: Path,
    algorithm: str,
    row_index: int,
    invalid: object,
) -> None:
    evidence = _evidence(tmp_path, algorithm)
    payload = json.loads(evidence.read_bytes())
    # Retain the genuine digests: coercing true/1.0 to 1 would falsely pass them.
    payload["ordered_inputs"][row_index]["ordinal"] = invalid
    evidence.write_text(json.dumps(payload), encoding="utf-8")
    malformed_bytes = evidence.read_bytes()
    with pytest.raises(ValueError, match="input ordinals must be contiguous and ordered"):
        read_manuscript_composition(evidence)
    assert evidence.read_bytes() == malformed_bytes
