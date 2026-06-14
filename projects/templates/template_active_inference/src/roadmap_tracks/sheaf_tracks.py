"""Canonical deterministic sheaf-track artifacts (public facade).

Track ids and artifact paths stay canonical so the manuscript cannot accumulate
parallel ``*_vN`` proof surfaces for the same concept. Implementation lives in
focused sibling modules; this module re-exports the stable public surface.
"""

from __future__ import annotations


from roadmap_tracks.sheaf_tracks_builders_formal import (
    build_adversarial_audit,
    build_blocked_scope_manifest,
    build_counterexample_matrix,
    build_interop_roundtrip_report,
    build_model_checking_witnesses,
)
from roadmap_tracks.sheaf_tracks_builders_graph import (
    _pipeline_sheaf_tracks,
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
    _provenance_context,
)
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _bound_tracks,
    _claim_ids_by_path,
    _claim_ids_by_track,
    _config_digest,
    _deterministic_seed,
    _load_json,
    _load_structured,
    _load_yaml,
    _pipeline_tracks,
    _registry_tracks,
    _sha256,
    _source_commit,
)
from roadmap_tracks.sheaf_tracks_registry import (
    CANONICAL_ARTIFACTS,
    CANONICAL_SCHEMA,
    CANONICAL_TRACKS,
    DEPENDENCY_SCHEMA,
    LEGACY_ARTIFACTS,
    OPTIONAL_CLAIM_EXEMPT_TRACKS,
    PIPELINE_TRACK_SHEAF_ALIASES,
    REQUIRED_EDGE_TYPES,
    SEMANTIC_SCHEMA,
    SHEAF_TRACK_PRODUCER,
    VERSIONED_TRACK_RE,
)
from roadmap_tracks.sheaf_tracks_restrictions import _canonical_restrictions
from roadmap_tracks.sheaf_tracks_write import write_sheaf_track_artifacts

__all__ = [
    "CANONICAL_ARTIFACTS",
    "CANONICAL_SCHEMA",
    "CANONICAL_TRACKS",
    "DEPENDENCY_SCHEMA",
    "LEGACY_ARTIFACTS",
    "OPTIONAL_CLAIM_EXEMPT_TRACKS",
    "PIPELINE_TRACK_SHEAF_ALIASES",
    "REQUIRED_EDGE_TYPES",
    "SEMANTIC_SCHEMA",
    "SHEAF_TRACK_PRODUCER",
    "VERSIONED_TRACK_RE",
    "_ACTIVE_PROVENANCE_CONTEXT",
    "_ProvenanceContext",
    "_analysis_scripts",
    "_artifact_maps",
    "_bound_tracks",
    "_canonical_restrictions",
    "_claim_ids_by_path",
    "_claim_ids_by_track",
    "_config_digest",
    "_deterministic_seed",
    "_load_json",
    "_load_structured",
    "_load_yaml",
    "_pipeline_sheaf_tracks",
    "_pipeline_tracks",
    "_provenance_context",
    "_registry_tracks",
    "_sha256",
    "_source_commit",
    "build_adversarial_audit",
    "build_artifact_contract_index",
    "build_artifact_provenance",
    "build_blocked_scope_manifest",
    "build_counterexample_matrix",
    "build_evidence_field_index",
    "build_interop_roundtrip_report",
    "build_model_checking_witnesses",
    "build_release_bundle_manifest",
    "build_replay_matrix",
    "build_sensitivity_sweep",
    "build_theorem_traceability_matrix",
    "build_track_improvement_scope",
    "build_track_lane_matrix",
    "build_uncertainty_summary",
    "build_validation_dependency_graph",
    "validate_sheaf_track_artifacts",
    "validate_sheaf_track_source_contract",
    "write_sheaf_track_artifacts",
]

from .sheaf_track_validation import validate_sheaf_track_artifacts, validate_sheaf_track_source_contract  # noqa: E402,F401
