"""Claim-lane vocabulary and derivation helpers for integration audits."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ALLOWED_CLAIM_LANES = ("analytical", "formal", "pymdp", "release", "scope", "semantic", "visualization")

_SOURCE_LANE_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        (
            "parameter_sweep",
            "analytical_",
            "sensitivity_",
            "uncertainty_",
            "toy_benchmark",
            "causal_ablation",
            "ablation_sensitivity",
            "state_space",
            "state_transition",
            "invariants.json",
        ),
        "analytical",
    ),
    (("si_", "pymdp", "tmaze", "graph_world"), "pymdp"),
    (("lean", "theorem", "proof_", "model_checking"), "formal"),
    (
        (
            "sheaf_",
            "semantic_",
            "validation_dependency",
            "cross_track",
            "manuscript_token",
            "manuscript_staleness",
            "evidence_field",
            "producer_completeness",
            "stale_artifact",
            "claim_evidence",
            "validation_gate",
            "section_status",
            "render_log",
            "gnn_",
            "ontology_",
        ),
        "semantic",
    ),
    (("figure_", "visualization_", "statistical_visualization", "output/figures/", "animation_"), "visualization"),
    (
        (
            "release_",
            "artifact_diffoscope",
            "artifact_license",
            "artifact_provenance",
            "reproducibility_replay",
            "replay_matrix",
            "security_posture",
        ),
        "release",
    ),
    (("scope_boundary", "blocked_scope", "adversarial_audit", "scholarship"), "scope"),
)

_EVIDENCE_ROLE_LANES = {
    "formal": "formal",
    "schematic": "visualization",
    "scholarship": "scope",
    "sheaf": "semantic",
    "source_mapped": "semantic",
    "statistical": "analytical",
}

_TRACK_LANES = {
    "adversarial_audit": "scope",
    "animation": "visualization",
    "animation_delta": "visualization",
    "artifact_diffoscope": "release",
    "artifact_license": "release",
    "assumption_index": "analytical",
    "benchmark": "analytical",
    "causal_ablation": "analytical",
    "counterexample": "scope",
    "evidence_fields": "semantic",
    "formalism": "analytical",
    "gate_ergonomics": "release",
    "gnn": "semantic",
    "interop": "pymdp",
    "layers": "semantic",
    "lean": "formal",
    "manuscript_staleness": "semantic",
    "model_checking": "formal",
    "ontology": "semantic",
    "proof_extraction": "formal",
    "provenance": "release",
    "pymdp": "pymdp",
    "release_bundle": "release",
    "release_notes": "release",
    "replay_matrix": "release",
    "scholarship": "scope",
    "security_posture": "release",
    "sensitivity": "analytical",
    "simulation": "pymdp",
    "state_space_catalog": "analytical",
    "theorem_traceability": "formal",
    "uncertainty": "analytical",
    "visualization": "visualization",
}


def allowed_claim_lanes() -> tuple[str, ...]:
    """Return the stable figure/scope lane vocabulary used by validators."""
    return ALLOWED_CLAIM_LANES


def _lane_from_source(source: str) -> str:
    lowered = source.lower()
    for needles, lane in _SOURCE_LANE_HINTS:
        if any(needle in lowered for needle in needles):
            return lane
    return ""


def manifest_tracks_by_section(root: Path) -> dict[str, list[str]]:
    """Return sheaf track ids keyed by manuscript section id."""
    path = root / "manuscript" / "sheaf" / "manifest.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    sections = payload.get("sections") if isinstance(payload, dict) else []
    return {
        str(section.get("id")): sorted(str(track_id) for track_id in (section.get("tracks") or {}))
        for section in sections or []
        if section.get("id")
    }


def figure_claim_lanes(
    source_artifacts: list[str],
    section_tracks: list[str] | tuple[str, ...] = (),
    evidence_role: str = "",
) -> list[str]:
    """Derive claim lanes from source artifacts, sheaf tracks, and evidence role."""
    lanes = {_lane_from_source(str(source)) for source in source_artifacts}
    lanes.update(_TRACK_LANES.get(str(track), "") for track in section_tracks)
    lanes.add(_EVIDENCE_ROLE_LANES.get(str(evidence_role), ""))
    return sorted(lane for lane in lanes if lane in ALLOWED_CLAIM_LANES)


def claim_lane_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize per-figure claim lanes in a validation-friendly shape."""
    coverage = {lane: 0 for lane in ALLOWED_CLAIM_LANES}
    all_valid = True
    all_present = bool(rows)
    for row in rows:
        lanes = [str(lane) for lane in row.get("claim_lanes") or []]
        all_present = all_present and bool(lanes)
        all_valid = all_valid and all(lane in ALLOWED_CLAIM_LANES for lane in lanes)
        for lane in set(lanes):
            if lane in coverage:
                coverage[lane] += 1
    return {
        "allowed_claim_lanes": list(ALLOWED_CLAIM_LANES),
        "claim_lane_coverage": coverage,
        "all_figures_have_claim_lanes": all_present,
        "all_claim_lanes_valid": all_valid,
    }


__all__ = [
    "ALLOWED_CLAIM_LANES",
    "allowed_claim_lanes",
    "claim_lane_summary",
    "figure_claim_lanes",
    "manifest_tracks_by_section",
]
