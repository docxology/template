"""Output gate validation tests."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

from PIL import Image
import pytest

from gates.artifact_manifest import REQUIRED_OUTPUT_CHECK_KEYS, REQUIRED_OUTPUTS
from gates.validation import validate_outputs

from gate_support import ensure_gate_artifacts, refresh_generated_gate_artifacts

pytestmark = [pytest.mark.timeout(300)]


@pytest.fixture
def prepared_output_gate_artifacts(project_root: Path) -> Path:
    ensure_gate_artifacts(project_root)
    return project_root


def _write_png(path: Path, *, blank: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (120, 80), (255, 255, 255))
    if not blank:
        image.putpixel((20, 20), (0, 0, 0))
    image.save(path, format="PNG")


# Regenerates heavy sheaf/roadmap gate artifacts; ~57-59s locally and can exceed the
# CI-wide --timeout=120 on slower runners. The per-module marker overrides the CLI value.

EXPECTED_DERIVED_OUTPUT_CHECK_KEYS = {
    "ablation_sensitivity_report_schema",
    "adversarial_audit_schema",
    "figures_nonblank",
    "analysis_statistics_schema",
    "analytical_assumption_index_schema",
    "analytical_observable_sweep_schema",
    "animation_frame_deltas_schema",
    "artifact_contract_index_schema",
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
    "security_posture_audit_schema",
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
    "track_lane_matrix_schema",
    "track_improvement_scope_schema",
    "uncertainty_summary_schema",
    "validation_dependency_graph_schema",
    "validation_gate_index_schema",
    "visualization_quality_audit_schema",
}

SELF_REFERENTIAL_STABILITY_EXEMPT_OUTPUTS = {
    "output/data/artifact_contract_index.json",
}


def test_validate_outputs_after_analysis() -> None:
    root = Path(__file__).resolve().parents[2]
    from analysis import run_analysis

    run_analysis(root)
    checks = validate_outputs(root)
    assert checks.get("output/data/parameter_sweep.csv")


def test_validate_outputs_required_artifacts(
    project_root: Path,
    prepared_output_gate_artifacts: Path,
) -> None:
    checks = validate_outputs(project_root)
    for key in REQUIRED_OUTPUT_CHECK_KEYS:
        assert checks.get(key), f"missing validate_outputs key: {key}"
    assert checks.get("si_invariants_all_pass") is True
    assert checks.get("invariants_all_pass") is True


def test_validate_outputs_key_surface_is_stable(
    project_root: Path,
    prepared_output_gate_artifacts: Path,
) -> None:
    checks = validate_outputs(project_root)

    assert set(checks) == set(REQUIRED_OUTPUTS) | EXPECTED_DERIVED_OUTPUT_CHECK_KEYS


@pytest.mark.long_running
def test_validate_outputs_no_regression_on_stable_artifact_tree(prepared_output_gate_artifacts: Path) -> None:
    refresh_generated_gate_artifacts(prepared_output_gate_artifacts)
    first_checks = validate_outputs(prepared_output_gate_artifacts)
    assert first_checks["figures_nonblank"] is True

    tracked = [
        prepared_output_gate_artifacts / rel
        for rel in REQUIRED_OUTPUTS
        if rel.startswith("output/") and rel not in SELF_REFERENTIAL_STABILITY_EXEMPT_OUTPUTS
    ]
    pre_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked if path.is_file()}

    checks = validate_outputs(prepared_output_gate_artifacts)

    assert checks["figures_nonblank"] is True
    for path, previous in pre_hashes.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == previous, path.relative_to(
            prepared_output_gate_artifacts
        )


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


def test_figures_nonblank_passes_on_real_tree(
    project_root: Path,
    prepared_output_gate_artifacts: Path,
) -> None:
    """Positive control: bootstrapped figures satisfy the integrity gate."""
    checks = validate_outputs(project_root)
    assert checks.get("figures_nonblank") is True


def test_figures_nonblank_negative_blank_png(
    project_root: Path,
    prepared_output_gate_artifacts: Path,
    tmp_path: Path,
) -> None:
    """A 0-byte PNG (empty-file sha is truthy under exists()) must fail the gate."""
    target = project_root / "output" / "figures" / "ising_mi_curve.png"
    assert target.is_file(), "expected bootstrapped figure to exist"
    backup = tmp_path / "ising_mi_curve.png.bak"
    backup.write_bytes(target.read_bytes())
    try:
        target.write_bytes(b"")  # 0-byte blank figure
        checks = validate_outputs(project_root)
        assert checks.get("figures_nonblank") is False
        assert checks.get("experiment_plan_metrics") is False
        # The mere-existence check still passes, proving the new check is what catches it.
        assert checks.get("output/figures/ising_mi_curve.png") is True
    finally:
        target.write_bytes(backup.read_bytes())


def test_figures_nonblank_validates_small_fixtures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Known tiny fixtures must pass/fail nonblank detection independently of full outputs."""
    from gates import output_checks

    fixture_root = tmp_path / "mini_project"
    nonblank = fixture_root / "output" / "figures" / "tiny_ok.png"
    blank = fixture_root / "output" / "figures" / "tiny_blank.png"

    _write_png(nonblank, blank=False)
    _write_png(blank, blank=True)

    with monkeypatch.context() as m:
        m.setattr(output_checks, "REQUIRED_OUTPUTS", ("output/figures/tiny_ok.png",))
        m.setattr(output_checks, "_MIN_FIGURE_BYTES", 1)
        assert output_checks._figures_nonblank(fixture_root) is True

    with monkeypatch.context() as m:
        m.setattr(output_checks, "REQUIRED_OUTPUTS", ("output/figures/tiny_blank.png",))
        m.setattr(output_checks, "_MIN_FIGURE_BYTES", 1)
        assert output_checks._figures_nonblank(fixture_root) is False


def test_reproducibility_replay_rebuild_passes_on_real_tree(
    project_root: Path,
    prepared_output_gate_artifacts: Path,
) -> None:
    """Positive control: the real rebuild=True replay reproduces every producer."""
    from validation_spine import validate_reproducibility_replay

    assert validate_reproducibility_replay(project_root, rebuild=True) == []


def test_reproducibility_replay_rebuild_catches_forged_sweep(
    project_root: Path,
    prepared_output_gate_artifacts: Path,
    tmp_path: Path,
) -> None:
    """A forged parameter_sweep.csv must make rebuild=True replay report a mismatch."""
    from validation_spine import validate_reproducibility_replay

    sweep = project_root / "output" / "data" / "parameter_sweep.csv"
    assert sweep.is_file(), "expected bootstrapped parameter sweep"
    backup = tmp_path / "parameter_sweep.csv.bak"
    backup.write_bytes(sweep.read_bytes())
    try:
        sweep.write_text(sweep.read_text(encoding="utf-8") + "forged,row,values\n", encoding="utf-8")
        issues = validate_reproducibility_replay(project_root, rebuild=True)
        assert any("parameter_sweep_replay" in issue for issue in issues), issues
    finally:
        sweep.write_bytes(backup.read_bytes())


def test_reproducibility_replay_recompute_catches_rows_vs_aggregate_forgery(
    project_root: Path,
    prepared_output_gate_artifacts: Path,
    tmp_path: Path,
) -> None:
    """Flipping a row to passed=false while leaving all_passed=true must be caught (cheap path)."""
    from validation_spine import validate_reproducibility_replay

    path = project_root / "output" / "reports" / "reproducibility_replay.json"
    if not path.is_file():
        ensure_gate_artifacts(project_root)
    assert path.is_file()
    backup = tmp_path / "reproducibility_replay.json.bak"
    backup.write_bytes(path.read_bytes())
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("checks") or []
        assert rows, "expected replay checks to forge"
        rows[0]["passed"] = False  # forge a failing row, keep aggregate all_passed=true
        payload["checks"] = rows
        payload["all_passed"] = True
        path.write_text(json.dumps(payload), encoding="utf-8")
        issues = validate_reproducibility_replay(project_root, rebuild=False)
        assert any("all_passed disagrees with per-row results" in issue for issue in issues), issues
    finally:
        path.write_bytes(backup.read_bytes())
