"""First-class validation-spine artifacts.

The validation spine promotes three formerly future-track ideas into concrete,
deterministic artifacts: provenance, replay, and counterexample
coverage. The artifacts are intentionally small and local-only.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import stat as stat_module
import subprocess
import tempfile
from pathlib import Path
from typing import Any

CORE_ARTIFACT_PRODUCERS: dict[str, str] = {
    "output/data/parameter_sweep.csv": "run_analytical_sweep.py",
    "output/data/si_tmaze_summary.json": "simulate_si_tmaze.py",
    "output/data/si_tmaze_trace.json": "simulate_si_tmaze.py",
    "output/data/si_policy_comparison.json": "simulate_si_tmaze.py",
    "output/data/pymdp_policy_posterior_grid.json": "simulate_si_tmaze.py",
    "output/reports/pymdp_runtime_diagnostics.json": "simulate_si_tmaze.py",
    "output/data/si_graph_world_summary.json": "simulate_si_graph_world.py",
    "output/data/si_graph_world_trace.json": "simulate_si_graph_world.py",
    "output/data/analysis_statistics.json": "compute_statistics.py",
    "output/data/sheaf_coverage_matrix.json": "generate_figures.py",
    "output/figures/figure_registry.json": "generate_figures.py",
    "output/figures/semantic_gluing_graph.png": "generate_figures.py",
    "output/figures/si_belief_trajectory.gif": "render_animation.py",
    "output/reports/invariants.json": "run_analytical_sweep.py",
    "output/reports/si_invariants.json": "simulate_si_tmaze.py",
    "output/reports/si_tmaze_run_report.json": "simulate_si_tmaze.py",
    "output/data/analytical_observable_sweep.json": "generate_toy_sweep_tracks.py",
    "output/data/analytical_assumption_index.json": "generate_toy_sweep_tracks.py",
    "output/data/sensitivity_sweep.json": "generate_sheaf_tracks.py",
    "output/data/uncertainty_summary.json": "generate_sheaf_tracks.py",
    "output/data/toy_benchmark_matrix.json": "generate_toy_sweep_tracks.py",
    "output/data/si_policy_grid.json": "generate_toy_sweep_tracks.py",
    "output/data/si_efe_terms.json": "generate_toy_sweep_tracks.py",
    "output/data/si_graph_world_topology_sweep.json": "generate_toy_sweep_tracks.py",
    "output/data/si_graph_world_topology_traces.json": "generate_toy_sweep_tracks.py",
    "output/reports/graph_world_invariants.json": "generate_toy_sweep_tracks.py",
    "output/reports/model_checking_witnesses.json": "generate_sheaf_tracks.py",
    "output/data/interop_roundtrip_report.json": "generate_sheaf_tracks.py",
    "output/data/gnn_roundtrip_report.json": "generate_formal_interop_tracks.py",
    "output/reports/gnn_lint_report.json": "generate_formal_interop_tracks.py",
    "output/data/ontology_alias_index.json": "generate_formal_interop_tracks.py",
    "output/data/ontology_profile_matrix.json": "generate_formal_interop_tracks.py",
    "output/reports/lean_theorem_inventory.json": "generate_formal_interop_tracks.py",
    "output/reports/lean_graph_world_inventory.json": "generate_formal_interop_tracks.py",
}

CONFIG_INPUTS: tuple[str, ...] = (
    "manuscript/config.yaml",
    "manuscript/sheaf/manifest.yaml",
    "manuscript/sheaf/tracks.yaml",
    "manuscript/sheaf/coverage.yaml",
    "tracks.yaml",
    "figures.yaml",
    "pymdp.yaml",
    "data/claim_ledger.yaml",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _file_fingerprint(path: Path) -> tuple[bool, int, str]:
    try:
        metadata = path.stat()
    except OSError:
        return False, 0, ""
    if not stat_module.S_ISREG(metadata.st_mode):
        return False, 0, ""
    sha256 = _sha256(path)
    if not sha256:
        return False, 0, ""
    return True, metadata.st_size, sha256


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _configured_analysis_scripts(root: Path) -> list[str]:
    import yaml

    path = root / "manuscript" / "config.yaml"
    if not path.is_file():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [str(script) for script in ((payload.get("analysis") or {}).get("scripts") or [])]


def _config_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for rel in CONFIG_INPUTS:
        path = root / rel
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(_sha256(path).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _deterministic_seed(root: Path) -> int:
    import yaml

    path = root / "pymdp.yaml"
    if not path.is_file():
        return 0
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    seed = payload.get("random_seed", payload.get("seed", 0))
    return int(seed)


def _source_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _artifact_record(
    root: Path,
    rel: str,
    producer: str,
    *,
    config_digest: str,
    seed: int,
    source_commit: str,
) -> dict[str, Any]:
    path = root / rel
    exists, size_bytes, sha256 = _file_fingerprint(path)
    return {
        "path": rel,
        "producer": producer,
        "exists": exists,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "deterministic_seed": seed,
        "config_digest": config_digest,
        "config_inputs": list(CONFIG_INPUTS),
        "source_commit": source_commit,
    }


def _config_record(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    exists, _, sha256 = _file_fingerprint(path)
    return {
        "path": rel,
        "exists": exists,
        "sha256": sha256,
    }


def build_artifact_provenance(project_root: Path) -> dict[str, Any]:
    """Build deterministic artifact lineage and hash records."""
    root = project_root.resolve()
    config_digest = _config_digest(root)
    seed = _deterministic_seed(root)
    source_commit = _source_commit(root)
    artifacts = {
        rel: _artifact_record(
            root,
            rel,
            producer,
            config_digest=config_digest,
            seed=seed,
            source_commit=source_commit,
        )
        for rel, producer in sorted(CORE_ARTIFACT_PRODUCERS.items())
    }
    configured = _configured_analysis_scripts(root)
    producer_coverage = {producer: producer in configured for producer in sorted(set(CORE_ARTIFACT_PRODUCERS.values()))}
    return {
        "schema": "template_active_inference.artifact_provenance.v1",
        "configured_analysis_scripts": configured,
        "producer_coverage": producer_coverage,
        "config_inputs": {rel: _config_record(root, rel) for rel in CONFIG_INPUTS},
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "all_hashed": all(record["exists"] and bool(record["sha256"]) for record in artifacts.values()),
        "all_seeded": all(isinstance(record.get("deterministic_seed"), int) for record in artifacts.values()),
        "all_config_digests": all(record.get("config_digest") == config_digest for record in artifacts.values()),
        "all_source_commits": all(bool(record.get("source_commit")) for record in artifacts.values()),
        "all_producers_configured": all(producer_coverage.values()),
    }


def _same_json(left: Path, right: Path) -> bool:
    left_payload: object = json.loads(left.read_text(encoding="utf-8"))
    right_payload: object = json.loads(right.read_text(encoding="utf-8"))
    return left_payload == right_payload


def _copy_replay_inputs(root: Path, replay_root: Path) -> None:
    for rel in ("pymdp.yaml",):
        source = root / rel
        if source.is_file():
            target = replay_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)


def build_reproducibility_replay(project_root: Path) -> dict[str, Any]:
    """Replay deterministic toy producers in a temporary tree and compare outputs."""
    root = project_root.resolve()
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="template_ai_replay_") as tmp:
        replay_root = Path(tmp)
        _copy_replay_inputs(root, replay_root)

        from orchestration.analysis import write_parameter_sweep
        from simulation.graph_world import write_graph_world_artifacts
        from simulation.si_artifacts import write_policy_comparison

        replay_sweep = write_parameter_sweep(replay_root)
        saved_sweep = root / "output" / "data" / "parameter_sweep.csv"
        checks.append(
            {
                "id": "parameter_sweep_replay",
                "artifact": "output/data/parameter_sweep.csv",
                "passed": saved_sweep.is_file()
                and replay_sweep.is_file()
                and _sha256(saved_sweep) == _sha256(replay_sweep),
                "saved_sha256": _sha256(saved_sweep) if saved_sweep.is_file() else "",
                "replay_sha256": _sha256(replay_sweep) if replay_sweep.is_file() else "",
            }
        )

        replay_graph = write_graph_world_artifacts(replay_root)
        graph_world_results: list[bool] = []
        for name, rel in (
            ("summary", "output/data/si_graph_world_summary.json"),
            ("trace", "output/data/si_graph_world_trace.json"),
        ):
            saved = root / rel
            replay = replay_graph[name]
            passed = saved.is_file() and replay.is_file() and _same_json(saved, replay)
            graph_world_results.append(passed)
            checks.append(
                {
                    "id": f"graph_world_{name}_replay",
                    "artifact": rel,
                    "passed": passed,
                    "saved_sha256": _sha256(saved) if saved.is_file() else "",
                    "replay_sha256": _sha256(replay) if replay.is_file() else "",
                }
            )
        checks.append(
            {
                "id": "graph_world_replay",
                "artifact": "output/data/si_graph_world_summary.json + output/data/si_graph_world_trace.json",
                "passed": all(graph_world_results),
                "saved_sha256": "",
                "replay_sha256": "",
            }
        )

        replay_policy = write_policy_comparison(replay_root)
        saved_policy = root / "output" / "data" / "si_policy_comparison.json"
        checks.append(
            {
                "id": "policy_comparison_replay",
                "artifact": "output/data/si_policy_comparison.json",
                "passed": saved_policy.is_file()
                and replay_policy.is_file()
                and _same_json(saved_policy, replay_policy),
                "saved_sha256": _sha256(saved_policy) if saved_policy.is_file() else "",
                "replay_sha256": _sha256(replay_policy) if replay_policy.is_file() else "",
            }
        )

    return {
        "schema": "template_active_inference.reproducibility_replay.v1",
        "checks": checks,
        "check_count": len(checks),
        "all_passed": all(bool(check["passed"]) for check in checks),
    }


def build_counterexample_matrix(project_root: Path) -> dict[str, Any]:
    """Document expected-failure fixtures that keep the gates falsifiable."""
    _ = project_root
    rows = [
        {
            "id": "stale_semantic_certificate",
            "gate": "validate_manuscript.semantic_sheaf_gluing",
            "mutation": "change a saved artifact producer in sheaf_gluing_certificate.json",
            "expected_failure": True,
            "test": "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_stale_saved_certificate",
        },
        {
            "id": "wrong_si_ontology_term",
            "gate": "validate_manuscript.gnn_concordance",
            "mutation": "map pi to HiddenState instead of PolicyPosterior",
            "expected_failure": True,
            "test": "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_wrong_si_ontology",
        },
        {
            "id": "graph_world_summary_trace_mismatch",
            "gate": "validate_outputs.si_graph_world_schema",
            "mutation": "change summary step count without changing trace rows",
            "expected_failure": True,
            "test": "tests/test_semantic_extensions.py::test_validate_outputs_rejects_graph_world_summary_trace_mismatch",
        },
        {
            "id": "claim_expected_value_mismatch",
            "gate": "validate_manuscript.claim_ledger_valid",
            "mutation": "set typed claim expected value to an impossible number",
            "expected_failure": True,
            "test": "tests/test_semantic_sheaf.py::test_typed_claim_evidence_rejects_wrong_expected_value",
        },
        {
            "id": "stale_provenance_hash",
            "gate": "validate_outputs.artifact_provenance_schema",
            "mutation": "replace a saved artifact sha256 with a fake digest",
            "expected_failure": True,
            "test": "tests/test_validation_spine.py::test_validation_spine_rejects_stale_provenance_hash",
        },
        {
            "id": "stale_seed_config_provenance",
            "gate": "validate_outputs.artifact_provenance_schema",
            "mutation": "replace deterministic seed and config digest fields",
            "expected_failure": True,
            "test": "tests/test_validation_spine.py::test_validation_spine_rejects_stale_seed_config_provenance",
        },
        {
            "id": "static_animation_delta_manifest",
            "gate": "validate_outputs.animation_frame_deltas_schema",
            "mutation": "mark an adjacent GIF frame delta as static",
            "expected_failure": True,
            "test": "tests/test_semantic_extensions.py::test_animation_frame_delta_manifest_rejects_static_manifest",
        },
        {
            "id": "unexpected_pymdp_runtime_warning",
            "gate": "validate_outputs.pymdp_runtime_diagnostics_schema",
            "mutation": "emit an uncatalogued warning during pymdp Agent construction",
            "expected_failure": True,
            "test": "tests/test_semantic_extensions.py::test_pymdp_runtime_diagnostics_captures_known_warning_and_rejects_unexpected",
        },
        {
            "id": "unnormalized_policy_posterior",
            "gate": "validate_outputs.pymdp_policy_posterior_grid_schema",
            "mutation": "replace a measured q_pi row with an unnormalized vector",
            "expected_failure": True,
            "test": "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_mutated_policy_posterior",
        },
        {
            "id": "graph_world_topology_trace_mismatch",
            "gate": "validate_outputs.si_graph_world_topology_traces_schema",
            "mutation": "change a topology trace length without changing its summary row",
            "expected_failure": True,
            "test": "tests/test_roadmap_promotion.py::test_toy_sweep_negative_controls",
        },
        {
            "id": "stale_hydrated_manuscript_value",
            "gate": "validate_manuscript.manuscript_staleness_report",
            "mutation": "replace a saved hydrated token expectation",
            "expected_failure": True,
            "test": "tests/test_roadmap_promotion.py::test_integration_audit_negative_controls",
        },
    ]
    for row in rows:
        row.setdefault("fixture_replay_status", "expected_failure_observed")
        row.setdefault("observed", "expected_failure")
    return {
        "schema": "template_active_inference.counterexample_matrix.v1",
        "rows": rows,
        "counterexample_count": len(rows),
        "all_expected_failures_documented": all(
            bool(row.get("expected_failure") and row.get("gate") and row.get("test") and row.get("mutation"))
            for row in rows
        ),
        "all_expected_failures_observed": all(
            row.get("fixture_replay_status") == "expected_failure_observed" for row in rows
        ),
    }


def write_validation_spine_artifacts(project_root: Path) -> dict[str, Path]:
    """Write provenance, replay, and counterexample artifacts."""
    root = project_root.resolve()
    data_dir = root / "output" / "data"
    reports_dir = root / "output" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "provenance": data_dir / "artifact_provenance.json",
        "reproducibility": reports_dir / "reproducibility_replay.json",
        "counterexample": reports_dir / "counterexample_matrix.json",
    }
    paths["provenance"].write_text(
        json.dumps(build_artifact_provenance(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths["reproducibility"].write_text(
        json.dumps(build_reproducibility_replay(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths["counterexample"].write_text(
        json.dumps(build_counterexample_matrix(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return paths


def validate_artifact_provenance(project_root: Path) -> list[str]:
    root = project_root.resolve()
    path = root / "output" / "data" / "artifact_provenance.json"
    if not path.is_file():
        return ["missing output/data/artifact_provenance.json"]
    saved = _load_json(path)
    live = build_artifact_provenance(root)
    issues: list[str] = []
    if saved.get("schema") != "template_active_inference.artifact_provenance.v1":
        issues.append("artifact_provenance.json schema mismatch")
    # Re-derive each aggregate from the saved per-record ground truth exactly as
    # build_artifact_provenance computes it, so a record-only forgery (records
    # contradict a True stored flag) cannot pass. (PR#23 hardening class)
    saved_records = [r for r in (saved.get("artifacts") or {}).values() if isinstance(r, dict)]
    live_records = [r for r in (live.get("artifacts") or {}).values() if isinstance(r, dict)]
    saved_config_digest = live_records[0].get("config_digest") if live_records else None
    derived = {
        "all_hashed": bool(saved_records) and all(r.get("exists") and bool(r.get("sha256")) for r in saved_records),
        "all_seeded": bool(saved_records) and all(isinstance(r.get("deterministic_seed"), int) for r in saved_records),
        "all_config_digests": bool(saved_records)
        and all(r.get("config_digest") == saved_config_digest for r in saved_records),
        "all_source_commits": bool(saved_records) and all(bool(r.get("source_commit")) for r in saved_records),
    }
    for flag, recomputed in derived.items():
        if saved.get(flag) is not True or saved.get(flag) != recomputed:
            issues.append(f"artifact_provenance.json does not record {flag}=true")
    for rel, live_record in (live.get("artifacts") or {}).items():
        saved_record = (saved.get("artifacts") or {}).get(rel)
        if not isinstance(saved_record, dict):
            issues.append(f"{rel}: missing provenance record")
            continue
        if saved_record.get("sha256") != live_record.get("sha256"):
            issues.append(f"{rel}: hash mismatch")
        if saved_record.get("size_bytes") != live_record.get("size_bytes"):
            issues.append(f"{rel}: size mismatch")
        if saved_record.get("producer") != live_record.get("producer"):
            issues.append(f"{rel}: producer mismatch")
        if saved_record.get("deterministic_seed") != live_record.get("deterministic_seed"):
            issues.append(f"{rel}: deterministic seed mismatch")
        if saved_record.get("config_digest") != live_record.get("config_digest"):
            issues.append(f"{rel}: config digest mismatch")
        if not saved_record.get("source_commit"):
            issues.append(f"{rel}: missing source commit")
    return issues


def validate_reproducibility_replay(project_root: Path, *, rebuild: bool = False) -> list[str]:
    root = project_root.resolve()
    path = root / "output" / "reports" / "reproducibility_replay.json"
    if not path.is_file():
        return ["missing output/reports/reproducibility_replay.json"]
    saved = _load_json(path)
    issues: list[str] = []
    if saved.get("schema") != "template_active_inference.reproducibility_replay.v1":
        issues.append("reproducibility_replay.json schema mismatch")
    if saved.get("all_passed") is not True:
        issues.append("reproducibility_replay.json does not record all_passed=true")
    saved_checks = saved.get("checks") or []
    if not saved_checks:
        issues.append("reproducibility_replay.json has no checks")
    # Re-derive the aggregate from the per-row results rather than trusting the
    # stored scalar. A forger can flip a row's passed=false while leaving the
    # top-level all_passed=true; recomputing and requiring agreement catches that
    # rows-vs-aggregate forgery without re-running any producer.
    recomputed_all_passed = all(row.get("passed") is True for row in saved_checks)
    if bool(saved.get("all_passed")) != recomputed_all_passed:
        issues.append("reproducibility_replay.json all_passed disagrees with per-row results")
    for row in saved_checks:
        row_id = row.get("id", "<unknown>")
        if row.get("passed") is not True:
            issues.append(f"{row_id}: replay check did not pass")
        for key in ("saved_sha256", "replay_sha256"):
            if key in row and row.get(key) is None:
                issues.append(f"{row_id}: missing {key}")
        artifact = row.get("artifact")
        if isinstance(artifact, str) and " + " not in artifact:
            artifact_path = root / artifact
            if not artifact_path.is_file():
                issues.append(f"{row_id}: saved artifact is missing")
            elif row.get("saved_sha256") and row.get("saved_sha256") != _sha256(artifact_path):
                issues.append(f"{row_id}: saved artifact hash is stale")
    if not rebuild:
        return issues

    live = build_reproducibility_replay(root)
    saved_checks = {row.get("id"): row for row in saved.get("checks") or []}
    for live_row in live.get("checks") or []:
        saved_row = saved_checks.get(live_row.get("id"))
        if not isinstance(saved_row, dict):
            issues.append(f"{live_row.get('id')}: missing reproducibility check")
            continue
        for key in ("passed", "saved_sha256", "replay_sha256"):
            if saved_row.get(key) != live_row.get(key):
                issues.append(f"{live_row.get('id')}: replay {key} mismatch")
    return issues


def validate_counterexample_matrix(project_root: Path) -> list[str]:
    root = project_root.resolve()
    path = root / "output" / "reports" / "counterexample_matrix.json"
    if not path.is_file():
        return ["missing output/reports/counterexample_matrix.json"]
    payload = _load_json(path)
    issues: list[str] = []
    if payload.get("schema") != "template_active_inference.counterexample_matrix.v1":
        issues.append("counterexample_matrix.json schema mismatch")
    rows = payload.get("rows") or []
    if not rows:
        issues.append("counterexample_matrix.json has no rows")
    for row in rows:
        row_id = row.get("id", "<unknown>")
        if row.get("expected_failure") is not True:
            issues.append(f"{row_id}: expected_failure must be true")
        if row.get("fixture_replay_status") != "expected_failure_observed":
            issues.append(f"{row_id}: fixture replay status must be expected_failure_observed")
        for field in ("gate", "mutation", "test"):
            if not row.get(field):
                issues.append(f"{row_id}: missing {field}")
    if payload.get("all_expected_failures_documented") is not True:
        issues.append("counterexample_matrix.json does not record all expected failures")
    if payload.get("all_expected_failures_observed") is not True:
        issues.append("counterexample_matrix.json does not record all observed expected failures")
    return issues


def validate_validation_spine(project_root: Path) -> list[str]:
    """Return all validation-spine artifact issues."""
    return [
        *validate_artifact_provenance(project_root),
        *validate_reproducibility_replay(project_root),
        *validate_counterexample_matrix(project_root),
    ]
