"""Output gate validation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gates.artifact_manifest import REQUIRED_OUTPUT_CHECK_KEYS
from gates.validation import validate_outputs

from gate_support import ensure_gate_artifacts


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


@pytest.mark.timeout(300)
def test_figures_nonblank_passes_on_real_tree(project_root: Path) -> None:
    """Positive control: bootstrapped figures satisfy the integrity gate."""
    ensure_gate_artifacts(project_root)
    checks = validate_outputs(project_root)
    assert checks.get("figures_nonblank") is True


@pytest.mark.timeout(300)
def test_figures_nonblank_negative_blank_png(project_root: Path, tmp_path: Path) -> None:
    """A 0-byte PNG (empty-file sha is truthy under exists()) must fail the gate."""
    ensure_gate_artifacts(project_root)
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


@pytest.mark.timeout(300)
def test_reproducibility_replay_rebuild_passes_on_real_tree(project_root: Path) -> None:
    """Positive control: the real rebuild=True replay reproduces every producer."""
    from validation_spine import validate_reproducibility_replay

    ensure_gate_artifacts(project_root)
    assert validate_reproducibility_replay(project_root, rebuild=True) == []


@pytest.mark.timeout(300)
def test_reproducibility_replay_rebuild_catches_forged_sweep(project_root: Path, tmp_path: Path) -> None:
    """A forged parameter_sweep.csv must make rebuild=True replay report a mismatch."""
    from validation_spine import validate_reproducibility_replay

    ensure_gate_artifacts(project_root)
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
    project_root: Path, tmp_path: Path
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
