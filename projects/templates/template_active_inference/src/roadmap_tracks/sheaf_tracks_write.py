"""Deterministic multi-phase writer for canonical sheaf-track artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from roadmap_tracks.sheaf_tracks_builders_formal import (
    build_adversarial_audit,
    build_blocked_scope_manifest,
    build_counterexample_matrix,
    build_model_checking_witnesses,
)
from roadmap_tracks.sheaf_tracks_builders_graph import (
    build_artifact_contract_index,
    build_track_improvement_scope,
    build_track_lane_matrix,
    build_validation_dependency_graph,
)
from roadmap_tracks.sheaf_tracks_builders_provenance import build_artifact_provenance, build_replay_matrix
from roadmap_tracks.sheaf_tracks_builders_release import (
    build_evidence_field_index,
    build_release_bundle_manifest,
    build_theorem_traceability_matrix,
)
from roadmap_tracks.sheaf_tracks_builders_toy import build_sensitivity_sweep, build_uncertainty_summary
from roadmap_tracks.sheaf_tracks_context import (
    _ACTIVE_PROVENANCE_CONTEXT,
    _ProvenanceContext,
)
from roadmap_tracks.sheaf_tracks_helpers import _refresh_hydrated_manuscript, _remove_legacy_artifacts
from roadmap_tracks.sheaf_tracks_io import _config_digest, _deterministic_seed, _source_commit, _write_json
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS


def _run_prerequisite_promoters(root: Path) -> None:
    try:
        from roadmap_tracks import (
            write_formal_interop_artifacts,
            write_integration_audit_artifacts,
            write_toy_sweep_artifacts,
        )

        write_toy_sweep_artifacts(root)
        write_formal_interop_artifacts(root)
        write_integration_audit_artifacts(root)
    except (ImportError, OSError, ValueError, KeyError):
        pass


def _record_external_artifact_paths(root: Path, paths: dict[str, Path]) -> None:
    paths["artifact_diffoscope"] = root / CANONICAL_ARTIFACTS["artifact_diffoscope"]
    paths["artifact_license"] = root / CANONICAL_ARTIFACTS["artifact_license"]
    paths["release_notes"] = root / CANONICAL_ARTIFACTS["release_notes"]
    paths["proof_extraction"] = root / CANONICAL_ARTIFACTS["proof_extraction"]
    paths["state_space_catalog"] = root / CANONICAL_ARTIFACTS["state_space_catalog"]
    paths["causal_ablation"] = root / CANONICAL_ARTIFACTS["causal_ablation"]


def _write_primary_canonical_artifacts(root: Path, paths: dict[str, Path], context: _ProvenanceContext) -> None:
    from roadmap_tracks.scholarship import write_scholarship_source_matrix
    from roadmap_tracks.security import write_security_posture_audit

    paths["sensitivity"] = _write_json(root / CANONICAL_ARTIFACTS["sensitivity"], build_sensitivity_sweep(root))
    paths["uncertainty"] = _write_json(root / CANONICAL_ARTIFACTS["uncertainty"], build_uncertainty_summary(root))
    paths["counterexample"] = _write_json(
        root / CANONICAL_ARTIFACTS["counterexample"], build_counterexample_matrix(root)
    )
    paths["model_checking"] = _write_json(
        root / CANONICAL_ARTIFACTS["model_checking"],
        build_model_checking_witnesses(root),
    )
    paths["scholarship"] = write_scholarship_source_matrix(root)
    provenance = build_artifact_provenance(root, context=context)
    paths["dependency"] = _write_json(
        root / CANONICAL_ARTIFACTS["dependency"],
        build_validation_dependency_graph(root, provenance=provenance, provenance_context=context),
    )
    from manuscript.sheaf.status import write_sheaf_status_outputs

    paths.update(write_sheaf_status_outputs(root))
    paths["interop"] = root / CANONICAL_ARTIFACTS["interop"]
    paths["adversarial"] = _write_json(root / CANONICAL_ARTIFACTS["adversarial_audit"], build_adversarial_audit(root))
    paths["blocked_scope"] = _write_json(
        root / CANONICAL_ARTIFACTS["blocked_scope_manifest"],
        build_blocked_scope_manifest(root),
    )
    paths["evidence_fields"] = _write_json(
        root / CANONICAL_ARTIFACTS["evidence_fields"],
        build_evidence_field_index(root),
    )
    paths["theorem_traceability"] = _write_json(
        root / CANONICAL_ARTIFACTS["theorem_traceability"],
        build_theorem_traceability_matrix(root),
    )
    paths["release_bundle"] = _write_json(
        root / CANONICAL_ARTIFACTS["release_bundle"],
        build_release_bundle_manifest(root),
    )
    paths["security_posture"] = write_security_posture_audit(root)
    paths["artifact_contract_index"] = _write_json(
        root / CANONICAL_ARTIFACTS["artifact_contract_index"],
        build_artifact_contract_index(root),
    )
    _record_external_artifact_paths(root, paths)
    paths["track_improvement_scope"] = _write_json(
        root / CANONICAL_ARTIFACTS["track_improvement_scope"],
        build_track_improvement_scope(root),
    )
    paths["replay_matrix"] = _write_json(root / CANONICAL_ARTIFACTS["replay_matrix"], build_replay_matrix(root))


def _write_integration_audit_phase(root: Path, paths: dict[str, Path]) -> None:
    try:
        from roadmap_tracks.integration_audit import write_integration_audit_artifacts

        write_integration_audit_artifacts(root)
        _record_external_artifact_paths(root, paths)
    except (ImportError, OSError, ValueError, KeyError):
        pass


def _write_post_audit_canonical_artifacts(root: Path, paths: dict[str, Path], context: _ProvenanceContext) -> None:
    from manuscript.sheaf.status import write_sheaf_status_outputs
    from roadmap_tracks.scholarship import write_scholarship_source_matrix
    from roadmap_tracks.security import write_security_posture_audit

    paths["counterexample"] = _write_json(
        root / CANONICAL_ARTIFACTS["counterexample"], build_counterexample_matrix(root)
    )
    paths["adversarial"] = _write_json(root / CANONICAL_ARTIFACTS["adversarial_audit"], build_adversarial_audit(root))
    paths["evidence_fields"] = _write_json(
        root / CANONICAL_ARTIFACTS["evidence_fields"], build_evidence_field_index(root)
    )
    paths["theorem_traceability"] = _write_json(
        root / CANONICAL_ARTIFACTS["theorem_traceability"],
        build_theorem_traceability_matrix(root),
    )
    paths["release_bundle"] = _write_json(
        root / CANONICAL_ARTIFACTS["release_bundle"],
        build_release_bundle_manifest(root),
    )
    paths["security_posture"] = write_security_posture_audit(root)
    paths["artifact_contract_index"] = _write_json(
        root / CANONICAL_ARTIFACTS["artifact_contract_index"],
        build_artifact_contract_index(root),
    )
    paths["scholarship"] = write_scholarship_source_matrix(root)
    paths["track_lane_matrix"] = _write_json(
        root / CANONICAL_ARTIFACTS["track_lane_matrix"],
        build_track_lane_matrix(root),
    )
    paths["track_improvement_scope"] = _write_json(
        root / CANONICAL_ARTIFACTS["track_improvement_scope"],
        build_track_improvement_scope(root),
    )
    paths["replay_matrix"] = _write_json(root / CANONICAL_ARTIFACTS["replay_matrix"], build_replay_matrix(root))
    provenance = build_artifact_provenance(root, context=context)
    paths["dependency"] = _write_json(
        root / CANONICAL_ARTIFACTS["dependency"],
        build_validation_dependency_graph(root, provenance=provenance, provenance_context=context),
    )
    paths.update(write_sheaf_status_outputs(root))


def _write_semantic_artifacts(root: Path, paths: dict[str, Path]) -> None:
    try:
        from manuscript.sheaf.semantic import build_evidence_crosswalk, build_semantic_gluing_certificate

        paths["crosswalk"] = _write_json(
            root / "output" / "data" / "sheaf_evidence_crosswalk.json",
            build_evidence_crosswalk(root),
        )
        paths["semantic"] = _write_json(root / CANONICAL_ARTIFACTS["semantic"], build_semantic_gluing_certificate(root))
    except (ImportError, OSError, ValueError, KeyError):
        pass


def _write_supplemental_phase(root: Path, paths: dict[str, Path]) -> None:
    from roadmap_tracks.supplemental import write_supplemental_artifacts

    paths.update(write_supplemental_artifacts(root))


def _write_final_canonical_pass(root: Path, paths: dict[str, Path], context: _ProvenanceContext) -> None:
    from manuscript.sheaf.status import write_sheaf_status_outputs
    from roadmap_tracks.security import write_security_posture_audit

    _refresh_hydrated_manuscript(root)
    paths.update(write_sheaf_status_outputs(root))
    _write_semantic_artifacts(root, paths)
    _write_supplemental_phase(root, paths)
    paths["artifact_contract_index"] = _write_json(
        root / CANONICAL_ARTIFACTS["artifact_contract_index"],
        build_artifact_contract_index(root),
    )
    for _ in range(2):
        _write_integration_audit_phase(root, paths)
        paths["release_bundle"] = _write_json(
            root / CANONICAL_ARTIFACTS["release_bundle"],
            build_release_bundle_manifest(root),
        )
        paths["artifact_contract_index"] = _write_json(
            root / CANONICAL_ARTIFACTS["artifact_contract_index"],
            build_artifact_contract_index(root),
        )
        _write_semantic_artifacts(root, paths)
        _write_supplemental_phase(root, paths)
    _write_semantic_artifacts(root, paths)
    paths["security_posture"] = write_security_posture_audit(root)
    paths["track_lane_matrix"] = _write_json(
        root / CANONICAL_ARTIFACTS["track_lane_matrix"],
        build_track_lane_matrix(root),
    )
    paths["release_bundle"] = _write_json(
        root / CANONICAL_ARTIFACTS["release_bundle"],
        build_release_bundle_manifest(root),
    )
    paths["artifact_contract_index"] = _write_json(
        root / CANONICAL_ARTIFACTS["artifact_contract_index"],
        build_artifact_contract_index(root),
    )
    provenance = build_artifact_provenance(root, context=context)
    paths["dependency"] = _write_json(
        root / CANONICAL_ARTIFACTS["dependency"],
        build_validation_dependency_graph(root, provenance=provenance, provenance_context=context),
    )
    paths["provenance"] = _write_json(root / CANONICAL_ARTIFACTS["provenance"], provenance)
    _write_integration_audit_phase(root, paths)
    _write_supplemental_phase(root, paths)
    paths["security_posture"] = write_security_posture_audit(root)
    paths["release_bundle"] = _write_json(
        root / CANONICAL_ARTIFACTS["release_bundle"],
        build_release_bundle_manifest(root),
    )
    paths["artifact_contract_index"] = _write_json(
        root / CANONICAL_ARTIFACTS["artifact_contract_index"],
        build_artifact_contract_index(root),
    )
    provenance = build_artifact_provenance(root, context=context)
    paths["dependency"] = _write_json(
        root / CANONICAL_ARTIFACTS["dependency"],
        build_validation_dependency_graph(root, provenance=provenance, provenance_context=context),
    )
    paths["provenance"] = _write_json(root / CANONICAL_ARTIFACTS["provenance"], provenance)
    _refresh_hydrated_manuscript(root)
    paths.update(write_sheaf_status_outputs(root))
    paths["artifact_contract_index"] = _write_json(
        root / CANONICAL_ARTIFACTS["artifact_contract_index"],
        build_artifact_contract_index(root),
    )
    _write_semantic_artifacts(root, paths)
    _write_supplemental_phase(root, paths)
    paths["artifact_contract_index"] = _write_json(
        root / CANONICAL_ARTIFACTS["artifact_contract_index"],
        build_artifact_contract_index(root),
    )


def write_sheaf_track_artifacts(project_root: Path, *, finalize: bool = True) -> dict[str, Path]:
    """Write the canonical promoted sheaf artifacts in deterministic phases."""
    root = project_root.resolve()
    if finalize:
        from roadmap_tracks.fixed_point import run_semantic_fixed_point

        return cast(dict[str, Path], run_semantic_fixed_point(root, require_analysis_outputs=False))

    global _ACTIVE_PROVENANCE_CONTEXT
    context = _ProvenanceContext(
        config_digest=_config_digest(root),
        deterministic_seed=_deterministic_seed(root),
        source_commit=_source_commit(root),
    )
    paths: dict[str, Path] = {}

    previous_context = _ACTIVE_PROVENANCE_CONTEXT
    _ACTIVE_PROVENANCE_CONTEXT = context
    try:
        _run_prerequisite_promoters(root)
        _remove_legacy_artifacts(root)
        _write_primary_canonical_artifacts(root, paths, context)
        _write_integration_audit_phase(root, paths)
        _write_post_audit_canonical_artifacts(root, paths, context)
        _write_final_canonical_pass(root, paths, context)
        _remove_legacy_artifacts(root)
    finally:
        _ACTIVE_PROVENANCE_CONTEXT = previous_context
    return paths
