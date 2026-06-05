"""Tests for the EFE additive-identity Lean formalization."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from gates.lean import lean_axioms_clean, lean_project_present
from roadmap_tracks.formal_interop import (
    build_lean_theorem_inventory,
    build_proof_extraction_index,
)
from visualizations.lean_boundary import load_lean_boundary_rows


def test_efe_theorems_in_boundary_inventory(project_root: Path) -> None:
    names = {row.name for row in load_lean_boundary_rows(project_root)}
    assert "efe_additive_identity_from_relations" in names
    assert "efe_total_eq_neg_value" in names
    assert "efe_witness_residual_zero" in names


def test_efe_theorems_proved_status(project_root: Path) -> None:
    by_name = {row.name: row for row in load_lean_boundary_rows(project_root)}
    for name in (
        "efe_additive_identity_from_relations",
        "efe_total_eq_neg_value",
        "efe_witness_residual_zero",
    ):
        assert by_name[name].status == "proved"


def test_efe_theorems_in_lean_inventory(project_root: Path) -> None:
    inv = build_lean_theorem_inventory(project_root)
    names = {row["name"] for row in inv["rows"]}
    assert {"efe_additive_identity_from_relations", "efe_total_eq_neg_value"} <= names
    assert inv["all_proved"] is True
    assert inv["forbidden_tokens"] == []


def test_efe_module_is_constructive(project_root: Path) -> None:
    index = build_proof_extraction_index(project_root)
    by_name = {row["theorem"]: row for row in index["rows"]}
    # The proof-extraction-index regex keys on `theorem <name> : <stmt> := by`, so it
    # surfaces the parameter-free witness theorem (matching the existing extractor
    # behaviour where binder-carrying theorems like `tmaze_goal_absorbing` are skipped).
    row = by_name["efe_witness_residual_zero"]
    assert row["source"].endswith("EFEDecomposition.lean")
    assert row["leading_tactic"] == "decide"  # first tactic in the proof body
    assert row["extracted"] is True
    assert row["forbidden_tokens"] == []
    assert index["all_constructive"] is True


def test_efe_module_source_present(project_root: Path) -> None:
    src = project_root / "lean" / "TemplateActiveInference" / "EFEDecomposition.lean"
    text = src.read_text(encoding="utf-8")
    assert "efeIdentityResidual" in text
    # Mathlib-free invariant: must NOT use ring (unavailable); must close with omega.
    assert " ring" not in text
    assert "omega" in text
    assert "sorry" not in text
    assert "native_decide" not in text


@pytest.mark.skipif(shutil.which("lake") is None, reason="lake toolchain not installed")
def test_efe_theorem_axioms_clean(project_root: Path) -> None:
    assert lean_project_present(project_root)
    ok, output = lean_axioms_clean(
        project_root,
        declarations=(
            "TemplateActiveInference.efe_additive_identity_from_relations",
            "TemplateActiveInference.efe_total_eq_neg_value",
            "TemplateActiveInference.efe_witness_residual_zero",
        ),
    )
    assert ok, output
