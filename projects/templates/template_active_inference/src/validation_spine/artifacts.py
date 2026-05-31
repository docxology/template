"""First-class validation-spine artifacts.

The validation spine promotes three formerly future-track ideas into concrete,
deterministic artifacts: provenance, reproducibility replay, and counterexample
coverage. The artifacts are intentionally small and local-only.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

CORE_ARTIFACT_PRODUCERS: dict[str, str] = {
    "output/data/parameter_sweep.csv": "run_analytical_sweep.py",
    "output/data/si_tmaze_summary.json": "simulate_si_tmaze.py",
    "output/data/si_tmaze_trace.json": "simulate_si_tmaze.py",
    "output/data/si_policy_comparison.json": "simulate_si_tmaze.py",
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
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _artifact_record(root: Path, rel: str, producer: str) -> dict[str, Any]:
    path = root / rel
    exists = path.is_file()
    return {
        "path": rel,
        "producer": producer,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
        "sha256": _sha256(path) if exists else "",
    }


def _config_record(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    exists = path.is_file()
    return {
        "path": rel,
        "exists": exists,
        "sha256": _sha256(path) if exists else "",
    }


def build_artifact_provenance(project_root: Path) -> dict[str, Any]:
    """Build deterministic artifact lineage and hash records."""
    root = project_root.resolve()
    artifacts = {
        rel: _artifact_record(root, rel, producer) for rel, producer in sorted(CORE_ARTIFACT_PRODUCERS.items())
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
    ]
    return {
        "schema": "template_active_inference.counterexample_matrix.v1",
        "rows": rows,
        "counterexample_count": len(rows),
        "all_expected_failures_documented": all(
            bool(row.get("expected_failure") and row.get("gate") and row.get("test") and row.get("mutation"))
            for row in rows
        ),
    }


def write_validation_spine_artifacts(project_root: Path) -> dict[str, Path]:
    """Write provenance, reproducibility, and counterexample artifacts."""
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
    if saved.get("all_hashed") is not True:
        issues.append("artifact_provenance.json does not record all_hashed=true")
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
    for row in saved_checks:
        row_id = row.get("id", "<unknown>")
        if row.get("passed") is not True:
            issues.append(f"{row_id}: replay check did not pass")
        for key in ("saved_sha256", "replay_sha256"):
            if key in row and row.get(key) is None:
                issues.append(f"{row_id}: missing {key}")
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
        for field in ("gate", "mutation", "test"):
            if not row.get(field):
                issues.append(f"{row_id}: missing {field}")
    if payload.get("all_expected_failures_documented") is not True:
        issues.append("counterexample_matrix.json does not record all expected failures")
    return issues


def validate_validation_spine(project_root: Path) -> list[str]:
    """Return all validation-spine artifact issues."""
    return [
        *validate_artifact_provenance(project_root),
        *validate_reproducibility_replay(project_root),
        *validate_counterexample_matrix(project_root),
    ]
