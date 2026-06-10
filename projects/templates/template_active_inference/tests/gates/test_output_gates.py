"""Output gate validation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gates.artifact_manifest import REQUIRED_OUTPUT_CHECK_KEYS, REQUIRED_OUTPUTS
from gates.validation import validate_outputs

from gate_support import ensure_gate_artifacts

EXPECTED_DERIVED_OUTPUT_CHECK_KEYS = {
    "ablation_sensitivity_report_schema",
    "adversarial_audit_schema",
    "analysis_statistics_schema",
    "analytical_assumption_index_schema",
    "analytical_observable_sweep_schema",
    "animation_frame_deltas_schema",
    "artifact_diffoscope_schema",
    "artifact_license_audit_schema",
    "artifact_provenance_schema",
    "blocked_scope_manifest_schema",
    "canonical_sheaf_track_schemas",
    "causal_ablation_matrix_schema",
    "claim_evidence_audit_schema",
    "counterexample_matrix_schema",
    "cross_track_symbol_table_schema",
    "evidence_field_index_schema",
    "experiment_plan_metrics",
    "figure_hash_manifest_schema",
    "figure_source_map_schema",
    "formal_interop_track_schemas",
    "gnn_lint_schema",
    "gnn_roundtrip_schema",
    "graph_world_invariants_schema",
    "integration_audit_track_schemas",
    "interop_roundtrip_schema",
    "invariants_all_pass",
    "lean_graph_world_inventory_schema",
    "lean_theorem_inventory_schema",
    "manuscript_evidence_tables_schema",
    "manuscript_staleness_report_schema",
    "manuscript_token_provenance_schema",
    "model_checking_witnesses_schema",
    "ontology_alias_schema",
    "ontology_profile_schema",
    "producer_completeness_schema",
    "proof_dependency_graph_schema",
    "proof_extraction_index_schema",
    "pymdp_policy_posterior_grid_schema",
    "pymdp_runtime_diagnostics_schema",
    "release_attestation_schema",
    "release_bundle_manifest_schema",
    "release_notes_evidence_schema",
    "replay_matrix_schema",
    "reproducibility_replay_schema",
    "scholarship_source_matrix_schema",
    "scope_boundary_audit_schema",
    "sensitivity_sweep_schema",
    "sheaf_evidence_crosswalk_schema",
    "sheaf_render_log_schema",
    "sheaf_section_status_matrix_schema",
    "si_efe_terms_schema",
    "si_graph_world_schema",
    "si_graph_world_topology_sweep_schema",
    "si_graph_world_topology_traces_schema",
    "si_invariants_all_pass",
    "si_log_present",
    "si_policy_comparison_schema",
    "si_policy_grid_schema",
    "si_summary_schema",
    "si_trace_present",
    "simulation_invariants_all_pass",
    "stale_artifact_report_schema",
    "state_space_catalog_schema",
    "state_transition_table_schema",
    "statistical_visualization_bridge_schema",
    "theorem_traceability_matrix_schema",
    "toy_benchmark_matrix_schema",
    "toy_sweep_track_schemas",
    "track_improvement_scope_schema",
    "uncertainty_summary_schema",
    "validation_dependency_graph_schema",
    "validation_gate_index_schema",
    "visualization_quality_audit_schema",
}


def test_validate_outputs_after_analysis() -> None:
    root = Path(__file__).resolve().parents[2]
    from analysis import run_analysis

    run_analysis(root)
    checks = validate_outputs(root)
    assert checks.get("output/data/parameter_sweep.csv")


# Regenerates heavy sheaf/roadmap gate artifacts; ~57-59s locally and can exceed the
# CI-wide --timeout=120 on slower runners. The per-test marker overrides the CLI value.
@pytest.mark.timeout(300)
def test_validate_outputs_required_artifacts(project_root: Path) -> None:
    ensure_gate_artifacts(project_root)
    checks = validate_outputs(project_root)
    for key in REQUIRED_OUTPUT_CHECK_KEYS:
        assert checks.get(key), f"missing validate_outputs key: {key}"
    assert checks.get("si_invariants_all_pass") is True
    assert checks.get("invariants_all_pass") is True


@pytest.mark.timeout(300)
def test_validate_outputs_key_surface_is_stable(project_root: Path) -> None:
    ensure_gate_artifacts(project_root)
    checks = validate_outputs(project_root)

    assert set(checks) == set(REQUIRED_OUTPUTS) | EXPECTED_DERIVED_OUTPUT_CHECK_KEYS


def test_validate_outputs_negative_si_invariants_fail(project_root: Path, tmp_path: Path) -> None:
    path = project_root / "output" / "reports" / "si_invariants.json"
    if not path.is_file():
        pytest.skip("SI invariants report missing; run analysis first")
    backup = tmp_path / "si_invariants.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["all_pass"] = False
    payload["invariants"] = {name: False for name in payload.get("invariants", {})}
    try:
        path.write_text(json.dumps(payload), encoding="utf-8")
        checks = validate_outputs(project_root)
        assert checks["si_invariants_all_pass"] is False
        assert checks["experiment_plan_metrics"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_validate_outputs_negative_analytical_invariants_fail(project_root: Path, tmp_path: Path) -> None:
    path = project_root / "output" / "reports" / "invariants.json"
    if not path.is_file():
        pytest.skip("invariants report missing; run analysis first")
    backup = tmp_path / "invariants.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["all_pass"] = False
    analytical = payload.get("invariants") or {}
    payload["invariants"] = {name: False for name in analytical}
    try:
        path.write_text(json.dumps(payload), encoding="utf-8")
        checks = validate_outputs(project_root)
        assert checks["invariants_all_pass"] is False
        assert checks["experiment_plan_metrics"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_write_invariants_report_preserves_simulation_merge(project_root: Path) -> None:
    from orchestration.analysis import write_invariants_report

    inv_path = project_root / "output" / "reports" / "invariants.json"
    si_summary = project_root / "output" / "data" / "si_tmaze_summary.json"
    if not inv_path.is_file() or not si_summary.is_file():
        from analysis import run_analysis
        from simulation.si_runner import pymdp_available, run_and_persist

        run_analysis(project_root)
        if not pymdp_available():
            pytest.skip("pymdp not installed")
        run_and_persist(project_root)

    before = json.loads(inv_path.read_text(encoding="utf-8"))
    assert before.get("simulation"), "expected merged simulation invariants before rewrite"

    write_invariants_report(project_root)
    after = json.loads(inv_path.read_text(encoding="utf-8"))
    assert after.get("simulation")
    assert after.get("all_pass") is True


def test_validate_outputs_negative_missing_si_invariants_report(project_root: Path, tmp_path: Path) -> None:
    summary = project_root / "output" / "data" / "si_tmaze_summary.json"
    si_inv = project_root / "output" / "reports" / "si_invariants.json"
    if not summary.is_file():
        pytest.skip("SI summary missing; run analysis first")
    backup = tmp_path / "si_invariants.json.bak"
    had_si_inv = si_inv.is_file()
    if had_si_inv:
        backup.write_text(si_inv.read_text(encoding="utf-8"), encoding="utf-8")
        si_inv.unlink()
    try:
        checks = validate_outputs(project_root)
        assert checks["si_invariants_all_pass"] is False
        assert checks["experiment_plan_metrics"] is False
    finally:
        if had_si_inv:
            si_inv.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_validate_outputs_negative_missing_sheaf_matrix(project_root: Path, tmp_path: Path) -> None:
    matrix = project_root / "output" / "data" / "sheaf_coverage_matrix.json"
    backup = tmp_path / "sheaf_coverage_matrix.json.bak"
    if matrix.is_file():
        backup.write_bytes(matrix.read_bytes())
        matrix.unlink()
    try:
        checks = validate_outputs(project_root)
        assert checks.get("output/data/sheaf_coverage_matrix.json") is False
    finally:
        if backup.is_file():
            matrix.write_bytes(backup.read_bytes())


def test_validate_outputs_negative_missing_sweep(project_root: Path, tmp_path: Path) -> None:
    sweep = project_root / "output" / "data" / "parameter_sweep.csv"
    backup = tmp_path / "parameter_sweep.csv.bak"
    if sweep.is_file():
        backup.write_bytes(sweep.read_bytes())
        sweep.unlink()
    try:
        checks = validate_outputs(project_root)
        assert checks.get("output/data/parameter_sweep.csv") is False
    finally:
        if backup.is_file():
            sweep.write_bytes(backup.read_bytes())
