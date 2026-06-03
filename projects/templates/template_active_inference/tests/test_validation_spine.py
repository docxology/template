"""Validation-spine track artifacts and gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from gate_support import ensure_gate_artifacts


def _ensure_validation_spine_inputs(project_root: Path) -> None:
    from validation_spine.artifacts import CORE_ARTIFACT_PRODUCERS

    if not all((project_root / rel).is_file() for rel in CORE_ARTIFACT_PRODUCERS):
        ensure_gate_artifacts(project_root)


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
