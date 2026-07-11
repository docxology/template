"""Validation-spine track artifacts and gates."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from gate_support import ensure_gate_artifacts


def _ensure_validation_spine_inputs(project_root: Path) -> None:
    from validation_spine.artifacts import CORE_ARTIFACT_PRODUCERS

    if not all((project_root / rel).is_file() for rel in CORE_ARTIFACT_PRODUCERS):
        ensure_gate_artifacts(project_root)


def test_artifact_provenance_looks_up_source_commit_once(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from validation_spine import artifacts

    calls: list[list[str]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = args[0]
        assert isinstance(cmd, list)
        calls.append([str(part) for part in cmd])
        assert kwargs["timeout"] == 5
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="abc123\n", stderr="")

    monkeypatch.setattr(artifacts.subprocess, "run", fake_run)

    provenance = artifacts.build_artifact_provenance(project_root)

    assert calls == [["git", "-C", str(project_root.resolve()), "rev-parse", "HEAD"]]
    assert {record["source_commit"] for record in (provenance.get("artifacts") or {}).values()} == {"abc123"}


def test_validation_spine_source_commit_times_out_to_unknown(
    project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from validation_spine import artifacts

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(artifacts.subprocess, "run", fake_run)

    assert artifacts._source_commit(project_root) == "unknown"


@pytest.mark.timeout(30)
def test_validation_spine_artifacts_are_written(project_root: Path) -> None:
    from validation_spine.artifacts import write_validation_spine_artifacts

    _ensure_validation_spine_inputs(project_root)
    paths = write_validation_spine_artifacts(project_root)

    provenance = json.loads(paths["provenance"].read_text(encoding="utf-8"))
    replay = json.loads(paths["reproducibility"].read_text(encoding="utf-8"))
    counterexamples = json.loads(paths["counterexample"].read_text(encoding="utf-8"))

    assert provenance["schema"] == "template_active_inference.artifact_provenance.v1"
    assert provenance["all_hashed"] is True
    assert provenance["all_seeded"] is True
    assert provenance["all_config_digests"] is True
    assert provenance["artifacts"]["output/data/si_graph_world_trace.json"]["producer"] == "simulate_si_graph_world.py"
    assert "deterministic_seed" in provenance["artifacts"]["output/data/si_graph_world_trace.json"]
    assert "output/reports/pymdp_runtime_diagnostics.json" in provenance["artifacts"]
    assert "output/data/pymdp_policy_posterior_grid.json" in provenance["artifacts"]
    assert "output/data/si_graph_world_topology_traces.json" in provenance["artifacts"]
    semantic_artifacts = [
        rel for rel in provenance["artifacts"] if rel.startswith("output/data/") or rel.startswith("output/reports/")
    ]
    assert all(provenance["artifacts"][rel]["deterministic_seed"] == 0 for rel in semantic_artifacts)
    assert all(provenance["artifacts"][rel]["config_digest"] for rel in semantic_artifacts)
    assert all(provenance["artifacts"][rel]["source_commit"] for rel in semantic_artifacts)
    assert replay["schema"] == "template_active_inference.reproducibility_replay.v1"
    assert replay["all_passed"] is True
    assert {check["id"] for check in replay["checks"]} >= {
        "graph_world_replay",
        "policy_comparison_replay",
    }
    assert counterexamples["schema"] == "template_active_inference.counterexample_matrix.v1"
    assert counterexamples["all_expected_failures_documented"] is True
    assert all(row["expected_failure"] for row in counterexamples["rows"])


@pytest.mark.timeout(30)
def test_validation_spine_rejects_stale_provenance_hash(project_root: Path) -> None:
    from validation_spine.artifacts import validate_artifact_provenance, write_validation_spine_artifacts

    _ensure_validation_spine_inputs(project_root)
    paths = write_validation_spine_artifacts(project_root)
    original = paths["provenance"].read_text(encoding="utf-8")
    payload = json.loads(original)
    try:
        payload["artifacts"]["output/data/si_graph_world_trace.json"]["sha256"] = "0" * 64
        paths["provenance"].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        issues = validate_artifact_provenance(project_root)
    finally:
        paths["provenance"].write_text(original, encoding="utf-8")

    assert any("si_graph_world_trace.json" in issue and "hash mismatch" in issue for issue in issues)


@pytest.mark.timeout(30)
def test_validation_spine_rejects_stale_seed_config_provenance(project_root: Path) -> None:
    from validation_spine.artifacts import validate_artifact_provenance, write_validation_spine_artifacts

    _ensure_validation_spine_inputs(project_root)
    paths = write_validation_spine_artifacts(project_root)
    original = paths["provenance"].read_text(encoding="utf-8")
    payload = json.loads(original)
    try:
        record = payload["artifacts"]["output/data/si_graph_world_trace.json"]
        record["deterministic_seed"] = 999
        record["config_digest"] = "0" * 64
        paths["provenance"].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        issues = validate_artifact_provenance(project_root)
    finally:
        paths["provenance"].write_text(original, encoding="utf-8")

    assert any("deterministic seed mismatch" in issue for issue in issues)
    assert any("config digest mismatch" in issue for issue in issues)


@pytest.mark.timeout(30)
def test_validation_spine_allows_nonempty_source_commit_drift(project_root: Path) -> None:
    from validation_spine.artifacts import validate_artifact_provenance, write_validation_spine_artifacts

    _ensure_validation_spine_inputs(project_root)
    paths = write_validation_spine_artifacts(project_root)
    original = paths["provenance"].read_text(encoding="utf-8")
    payload = json.loads(original)
    try:
        record = payload["artifacts"]["output/data/si_graph_world_trace.json"]
        record["source_commit"] = "0" * 40
        paths["provenance"].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        issues = validate_artifact_provenance(project_root)
    finally:
        paths["provenance"].write_text(original, encoding="utf-8")

    assert not any("source commit mismatch" in issue for issue in issues)
    assert not any("si_graph_world_trace.json" in issue and "missing source commit" in issue for issue in issues)


@pytest.mark.timeout(30)
def test_counterexample_matrix_rejects_undocumented_pass(project_root: Path) -> None:
    from validation_spine.artifacts import validate_counterexample_matrix, write_validation_spine_artifacts

    _ensure_validation_spine_inputs(project_root)
    paths = write_validation_spine_artifacts(project_root)
    original = paths["counterexample"].read_text(encoding="utf-8")
    payload = json.loads(original)
    try:
        payload["rows"][0]["expected_failure"] = False
        paths["counterexample"].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        issues = validate_counterexample_matrix(project_root)
    finally:
        paths["counterexample"].write_text(original, encoding="utf-8")

    assert any("expected_failure" in issue for issue in issues)


def test_reproducibility_replay_rejects_stale_saved_hash(project_root: Path) -> None:
    from validation_spine.artifacts import validate_reproducibility_replay, write_validation_spine_artifacts

    _ensure_validation_spine_inputs(project_root)
    paths = write_validation_spine_artifacts(project_root)
    original = paths["reproducibility"].read_text(encoding="utf-8")
    payload = json.loads(original)
    try:
        payload["checks"][0]["saved_sha256"] = "0" * 64
        paths["reproducibility"].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        issues = validate_reproducibility_replay(project_root)
    finally:
        paths["reproducibility"].write_text(original, encoding="utf-8")

    assert any("saved artifact hash is stale" in issue for issue in issues)


def test_validation_spine_tracks_are_registered_and_bound(project_root: Path) -> None:
    registry = yaml.safe_load((project_root / "manuscript" / "sheaf" / "tracks.yaml").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((project_root / "manuscript" / "sheaf" / "manifest.yaml").read_text(encoding="utf-8"))

    assert {"provenance", "replay_matrix", "counterexample", "adversarial_audit"} <= set(registry["tracks"])
    by_id = {section["id"]: section for section in manifest["sections"]}
    assert "provenance" in by_id["methods_sheaf"]["tracks"]
    assert "counterexample" in by_id["methods_sheaf"]["tracks"]
    assert "adversarial_audit" in by_id["methods_sheaf"]["tracks"]
    assert "replay_matrix" in by_id["results_invariants"]["tracks"]


def test_validation_spine_script_is_in_configured_analysis_dag(project_root: Path) -> None:
    from orchestration.pipeline_manifest import DEFAULT_ANALYSIS_SCRIPTS

    config = yaml.safe_load((project_root / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    configured = config["analysis"]["scripts"]

    assert "generate_validation_spine.py" in configured
    assert configured.index("generate_validation_spine.py") < configured.index("z_generate_manuscript_variables.py")
    assert configured == [step.script for step in DEFAULT_ANALYSIS_SCRIPTS]


def _walk_floats(value: object) -> list[float]:
    floats: list[float] = []
    if isinstance(value, bool):
        return floats
    if isinstance(value, float):
        floats.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            floats.extend(_walk_floats(item))
    elif isinstance(value, list):
        for item in value:
            floats.extend(_walk_floats(item))
    return floats


def _perturb_floats(value: object, shift: Callable[[float], float]) -> object:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return shift(value)
    if isinstance(value, dict):
        return {key: _perturb_floats(item, shift) for key, item in value.items()}
    if isinstance(value, list):
        return [_perturb_floats(item, shift) for item in value]
    return value


def test_replay_hashed_policy_artifacts_carry_quantized_floats_on_disk(project_root: Path) -> None:
    """Committed replay-hashed artifacts must sit exactly on the quantization grid.

    Raw exp/log-derived floats drift at ULP level across x86_64 numpy builds,
    which flips the sha256 recorded by reproducibility_replay.json when a test
    rewrites the artifact in-tree on a divergent CI lane.
    """
    from simulation.si_artifacts import REPLAY_FLOAT_DECIMALS

    _ensure_validation_spine_inputs(project_root)
    examined = 0
    for rel in ("output/data/si_policy_comparison.json", "output/data/pymdp_policy_posterior_grid.json"):
        payload = json.loads((project_root / rel).read_text(encoding="utf-8"))
        floats = _walk_floats(payload)
        assert floats, f"{rel}: expected float values to examine"
        examined += len(floats)
        off_grid = [value for value in floats if round(value, REPLAY_FLOAT_DECIMALS) != value]
        assert not off_grid, f"{rel}: floats off the replay quantization grid: {off_grid[:5]}"
    assert examined > 0


def test_policy_comparison_replay_hash_invariant_under_one_ulp_perturbation(tmp_path: Path) -> None:
    """1-ULP drift in writer inputs must not change the replay-hashed bytes.

    Positive control: a perturbation larger than the quantization grid MUST
    change the hash, proving this probe can detect a de-quantized writer.

    Known residual (accepted): a raw value within ~1 ULP of a half-way decimal
    boundary (k*1e-10 + 5e-11) can still round differently across platforms.
    Fixed-decimal quantization shrinks the per-value flip window from ~1.0 to
    ~2e-6, and cross-lane divergence for such a value is bounded to one grid
    step (1e-10), inside every downstream tolerance. No assertion can remove
    that window, so this test deliberately uses off-boundary values.
    """
    import hashlib
    import math

    from simulation.si_artifacts import write_policy_posterior_grid

    q_raw = [math.exp(-1.0 / 3.0), math.exp(-math.log(7.0) / 3.0)]
    q_total = sum(q_raw)
    q_pi = [value / q_total for value in q_raw]
    comparison = {
        "runs": [
            {
                "mode": "policy_inference",
                "horizon": 3,
                "seed": 0,
                "policy_posterior_steps": [
                    {
                        "step": 0,
                        "posterior_available": True,
                        "posterior_source": "pymdp.infer_policies",
                        "q_pi": q_pi,
                        "q_pi_sum": sum(q_pi),
                        "q_pi_entropy": -sum(p * math.log(p) for p in q_pi),
                        "fallback_reason": None,
                    }
                ],
            }
        ]
    }

    def _grid_hash(root: Path, payload: object) -> str:
        out = write_policy_posterior_grid(root, comparison=payload)
        return hashlib.sha256(out.read_bytes()).hexdigest()

    base = _grid_hash(tmp_path / "base", comparison)
    up = _grid_hash(tmp_path / "up", _perturb_floats(comparison, lambda v: math.nextafter(v, math.inf)))
    down = _grid_hash(tmp_path / "down", _perturb_floats(comparison, lambda v: math.nextafter(v, -math.inf)))
    assert base == up
    assert base == down

    control = _grid_hash(tmp_path / "control", _perturb_floats(comparison, lambda v: v + 1e-6))
    assert control != base


@pytest.mark.requires_pymdp
def test_fresh_policy_comparison_writer_emits_quantized_floats(project_root: Path) -> None:
    """A fresh writer run (not just the committed snapshot) stays on the grid.

    Committed-file-only scans miss writer regressions; this exercises the real
    simulation write boundary end-to-end.
    """
    from simulation.si_artifacts import REPLAY_FLOAT_DECIMALS, write_policy_comparison
    from simulation.si_runner import pymdp_available

    if not pymdp_available():
        pytest.skip("pymdp not installed")

    path = write_policy_comparison(project_root, horizons=(2,), seeds=(0,))
    grid_path = project_root / "output" / "data" / "pymdp_policy_posterior_grid.json"
    examined = 0
    for artifact in (path, grid_path):
        floats = _walk_floats(json.loads(artifact.read_text(encoding="utf-8")))
        assert floats, f"{artifact.name}: expected float values to examine"
        examined += len(floats)
        off_grid = [value for value in floats if round(value, REPLAY_FLOAT_DECIMALS) != value]
        assert not off_grid, f"{artifact.name}: floats off the replay quantization grid: {off_grid[:5]}"
    assert examined > 0
