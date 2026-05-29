"""Integrity remediations: semantic claim bindings + over-claim guards.

These bind manuscript adjectives/counts to their oracles (closing the "shape gate
passes on a relabel / fallback zeros" class) and pin the RedTeam fixes:

* C1/C2 — SI rollout: mode advertised == mode run; summary records a measured rollout.
* H2    — a composed "merged" invariants section must have real simulation invariants.
* H3    — GNN↔ontology concordance catches a relabel, not just a deletion.
* H1    — Lean axioms audited via ``#print axioms`` (catches ``sorry``/``sorryAx``).
* M1    — pyproject version == manuscript config version (no skew).
* M2    — claim ledger fails CLOSED when coverage artifacts cannot load.
* M3    — pymdp (a hard dependency) is actually importable (canary, no silent skip).

No mocks: every test uses real temp files / the real shipped artifacts.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from gates.claim_ledger import validate_claim_ledger, verify_claim_bindings
from gates.lean import lean_axioms_clean, lean_project_present
from gnn.concordance import concordance_holds, parity_gaps
from gnn.parser import parse_gnn_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_summary(root: Path, *, steps: int, mode: str) -> None:
    (root / "output" / "data").mkdir(parents=True, exist_ok=True)
    (root / "output" / "data" / "si_tmaze_summary.json").write_text(
        json.dumps({"steps": steps, "mode": mode, "mean_belief_entropy": 0.32}), encoding="utf-8"
    )


def _write_pymdp_cfg(root: Path, mode: str) -> None:
    (root / "pymdp.yaml").write_text(f"mode: {mode}\nsteps: 2\nhorizon: 2\n", encoding="utf-8")


# ── C1/C2: SI rollout bindings ──────────────────────────────────────────────


def test_binding_flags_unmeasured_si_summary(tmp_path: Path) -> None:
    """steps == 0 (fallback zeros) is rejected — it is not a measured rollout."""
    _write_summary(tmp_path, steps=0, mode="state_inference")
    _write_pymdp_cfg(tmp_path, "state_inference")
    violations = verify_claim_bindings(tmp_path)
    assert any("positive measured count" in v for v in violations), violations


def test_binding_passes_measured_consistent_si_summary(tmp_path: Path) -> None:
    _write_summary(tmp_path, steps=2, mode="state_inference")
    _write_pymdp_cfg(tmp_path, "state_inference")
    assert verify_claim_bindings(tmp_path) == []


def test_binding_flags_mode_mismatch(tmp_path: Path) -> None:
    """Manuscript would advertise the config mode; recorded rollout mode must match."""
    _write_summary(tmp_path, steps=2, mode="state_inference")
    _write_pymdp_cfg(tmp_path, "policy_inference")
    violations = verify_claim_bindings(tmp_path)
    assert any("mode mismatch" in v for v in violations), violations


# ── H2: merged invariants ────────────────────────────────────────────────────


def test_binding_flags_merged_claim_without_simulation(tmp_path: Path) -> None:
    """A section that says 'merged' but ships no simulation invariants is rejected."""
    (tmp_path / "manuscript").mkdir(parents=True, exist_ok=True)
    (tmp_path / "manuscript" / "13_results_invariants.md").write_text(
        "Checks pass in the merged validation report.\n", encoding="utf-8"
    )
    (tmp_path / "output" / "reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "reports" / "invariants.json").write_text(
        json.dumps({"invariants": {"a": True}}), encoding="utf-8"  # analytical only, no 'simulation'
    )
    violations = verify_claim_bindings(tmp_path)
    assert any("merged" in v for v in violations), violations


def test_binding_passes_merged_claim_with_simulation(tmp_path: Path) -> None:
    (tmp_path / "manuscript").mkdir(parents=True, exist_ok=True)
    (tmp_path / "manuscript" / "13_results_invariants.md").write_text(
        "Checks pass in the merged validation report.\n", encoding="utf-8"
    )
    (tmp_path / "output" / "reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "reports" / "invariants.json").write_text(
        json.dumps({"invariants": {"a": True}, "simulation": {"s": True}}), encoding="utf-8"
    )
    assert verify_claim_bindings(tmp_path) == []


# ── H3: GNN concordance correctness (not just presence) ──────────────────────


def test_concordance_holds_with_expected_terms() -> None:
    model = parse_gnn_file(PROJECT_ROOT / "gnn" / "bernoulli_toy.gnn.md")
    expected = {v: model.ontology[v] for v in model.ontology}
    assert concordance_holds(model, expected_terms=expected)


def test_concordance_catches_ontology_relabel() -> None:
    """A variable silently re-annotated to a different valid term is caught."""
    model = parse_gnn_file(PROJECT_ROOT / "gnn" / "bernoulli_toy.gnn.md")
    expected = {v: model.ontology[v] for v in model.ontology}
    relabeled = replace(model, ontology={**model.ontology, "J": "EntangledJointPosterior"})
    gaps = parity_gaps(relabeled, expected_terms=expected)
    assert any("expected" in g and "J" in g for g in gaps), gaps


# ── H1: Lean axioms audit ────────────────────────────────────────────────────


def test_lean_axioms_clean_on_real_project() -> None:
    ok, output = lean_axioms_clean(PROJECT_ROOT)
    assert ok, output


@pytest.mark.skipif(shutil.which("lake") is None, reason="lake toolchain not installed")
def test_lean_axioms_catches_planted_sorry(tmp_path: Path) -> None:
    assert lean_project_present(PROJECT_ROOT)
    shutil.copytree(PROJECT_ROOT / "lean", tmp_path / "lean")
    target = tmp_path / "lean" / "TemplateActiveInference" / "SophisticatedInference.lean"
    target.write_text(
        "namespace TemplateActiveInference\n"
        "def defaultPolicyLen : Nat := 3\n"
        "theorem sophisticated_requires_horizon : defaultPolicyLen > 1 := by sorry\n"
        "end TemplateActiveInference\n",
        encoding="utf-8",
    )
    ok, _ = lean_axioms_clean(tmp_path)
    assert not ok, "a sorry-backed theorem must fail the axioms audit"


# ── M1 / M2 / M3 ─────────────────────────────────────────────────────────────


def test_pyproject_version_matches_config() -> None:
    """M1: single source of version truth — no skew between pyproject and config."""
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    py_version = next(
        line.split("=", 1)[1].strip().strip('"')
        for line in pyproject.splitlines()
        if line.strip().startswith("version =")
    )
    config = yaml.safe_load((PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    assert py_version == config["paper"]["version"]


def test_claim_ledger_fails_closed_without_coverage_artifacts(tmp_path: Path) -> None:
    """M2: coverage_no_gray cannot vacuously pass when its artifacts are absent."""
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    ledger = tmp_path / "data" / "claim_ledger.yaml"
    ledger.write_text(
        "claims:\n"
        "  - id: coverage_no_gray\n"
        "    statement: zero gray cells\n"
        "    path: data/claim_ledger.yaml\n",  # path exists; coverage JSON/manifest do NOT
        encoding="utf-8",
    )
    assert validate_claim_ledger(tmp_path) is False


def test_pymdp_canary_hard_dependency_importable() -> None:
    """M3: pymdp is a declared hard dependency — assert it imports, no silent skip."""
    from simulation.si_loop import pymdp_available

    assert pymdp_available(), "inferactively-pymdp is a hard dependency and must import"
