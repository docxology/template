from __future__ import annotations
import json
from pathlib import Path


def add_validation_spine_checks(root: Path, checks: dict[str, bool]) -> dict[str, Path]:
    """Add validation spine checks to the collection."""
    crosswalk_path = root / "output" / "data" / "sheaf_evidence_crosswalk.json"
    dependency_path = root / "output" / "data" / "validation_dependency_graph.json"
    if crosswalk_path.exists():
        crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
        checks["sheaf_evidence_crosswalk_schema"] = crosswalk.get(
            "schema"
        ) == "template_active_inference.evidence_crosswalk.v1" and int(crosswalk.get("claim_count", 0)) == len(
            crosswalk.get("claims") or []
        )
    if dependency_path.exists():
        dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
        artifacts = dependency.get("artifacts") or {}
        checks["validation_dependency_graph_schema"] = (
            dependency.get("schema") == "template_active_inference.validation_dependency_graph.v1"
            and not dependency.get("issues")
            and bool(artifacts.get("output/data/sheaf_gluing_certificate.json"))
            and bool(artifacts.get("output/figures/si_belief_trajectory.gif"))
        )

    provenance_path = root / "output" / "data" / "artifact_provenance.json"
    replay_path = root / "output" / "reports" / "reproducibility_replay.json"
    counterexample_path = root / "output" / "reports" / "counterexample_matrix.json"
    if provenance_path.exists():
        from validation_spine import validate_artifact_provenance

        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        checks["artifact_provenance_schema"] = (
            provenance.get("schema") == "template_active_inference.artifact_provenance.v1"
            and provenance.get("all_hashed") is True
            and provenance.get("all_seeded") is True
            and provenance.get("all_config_digests") is True
            and provenance.get("all_source_commits") is True
            and provenance.get("all_producers_configured") is True
            and not validate_artifact_provenance(root)
        )
    if replay_path.exists():
        from validation_spine import validate_reproducibility_replay

        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        checks["reproducibility_replay_schema"] = (
            replay.get("schema") == "template_active_inference.reproducibility_replay.v1"
            and replay.get("all_passed") is True
            and not validate_reproducibility_replay(root)
        )
    if counterexample_path.exists():
        from validation_spine import validate_counterexample_matrix

        counterexamples = json.loads(counterexample_path.read_text(encoding="utf-8"))
        checks["counterexample_matrix_schema"] = (
            counterexamples.get("schema") == "template_active_inference.counterexample_matrix.v1"
            and counterexamples.get("all_expected_failures_documented") is True
            and not validate_counterexample_matrix(root)
        )

    return {
        "crosswalk_path": crosswalk_path,
        "dependency_path": dependency_path,
        "provenance_path": provenance_path,
        "replay_path": replay_path,
        "counterexample_path": counterexample_path,
    }
