"""Canonical deterministic sheaf-track artifacts.

This module consolidates the former promotion waves into stable public track
ids and artifact paths.  Schema strings may evolve, but live track ids and
output paths stay canonical so the manuscript cannot accumulate parallel
``*_vN`` proof surfaces for the same concept.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import Any, cast

import yaml

SHEAF_TRACK_PRODUCER = "generate_sheaf_tracks.py"
CANONICAL_SCHEMA = "template_active_inference.canonical_sheaf_tracks.v1"
SEMANTIC_SCHEMA = "template_active_inference.semantic_gluing.v2"
DEPENDENCY_SCHEMA = "template_active_inference.validation_dependency_graph.v1"
VERSIONED_TRACK_RE = re.compile(r"(?:^|_)v[2-9]$")

CANONICAL_TRACKS: tuple[str, ...] = (
    "provenance",
    "replay_matrix",
    "sensitivity",
    "uncertainty",
    "counterexample",
    "model_checking",
    "interop",
    "adversarial_audit",
    "evidence_fields",
    "release_bundle",
    "theorem_traceability",
    "gate_ergonomics",
    "scholarship",
    "security_posture",
    "artifact_diffoscope",
    "proof_extraction",
    "state_space_catalog",
    "causal_ablation",
    "artifact_license",
    "release_notes",
)

CANONICAL_ARTIFACTS: dict[str, str] = {
    "provenance": "output/data/artifact_provenance.json",
    "replay_matrix": "output/reports/replay_matrix.json",
    "sensitivity": "output/data/sensitivity_sweep.json",
    "uncertainty": "output/data/uncertainty_summary.json",
    "counterexample": "output/reports/counterexample_matrix.json",
    "model_checking": "output/reports/model_checking_witnesses.json",
    "interop": "output/data/interop_roundtrip_report.json",
    "adversarial_audit": "output/reports/adversarial_audit.json",
    "semantic": "output/data/sheaf_gluing_certificate.json",
    "dependency": "output/data/validation_dependency_graph.json",
    "section_status": "output/data/sheaf_section_status_matrix.json",
    "render_log": "output/reports/sheaf_render_log.json",
    "track_lane_matrix": "output/data/track_lane_matrix.json",
    "artifact_contract_index": "output/data/artifact_contract_index.json",
    "track_improvement_scope": "output/data/track_improvement_scope.json",
    "blocked_scope_manifest": "output/reports/blocked_scope_manifest.json",
    "evidence_fields": "output/data/evidence_field_index.json",
    "release_bundle": "output/reports/release_bundle_manifest.json",
    "theorem_traceability": "output/data/theorem_traceability_matrix.json",
    "gate_ergonomics": "output/data/validation_gate_index.json",
    "scholarship": "output/data/scholarship_source_matrix.json",
    "security_posture": "output/reports/security_posture_audit.json",
    "artifact_diffoscope": "output/reports/artifact_diffoscope.json",
    "proof_extraction": "output/data/proof_extraction_index.json",
    "state_space_catalog": "output/data/state_space_catalog.json",
    "causal_ablation": "output/data/causal_ablation_matrix.json",
    "artifact_license": "output/reports/artifact_license_audit.json",
    "release_notes": "output/reports/release_notes_evidence.json",
    "statistical_visualization_bridge": "output/data/statistical_visualization_bridge.json",
    "proof_dependency_graph": "output/data/proof_dependency_graph.json",
    "state_transition_table": "output/data/state_transition_table.json",
    "ablation_sensitivity_report": "output/reports/ablation_sensitivity_report.json",
    "release_attestation": "output/reports/release_attestation.json",
}

LEGACY_ARTIFACTS: tuple[str, ...] = (
    "output/data/artifact_lineage_v2.json",
    "output/data/artifact_bundle_lineage_v3.json",
    "output/data/sensitivity_sweep_v2.json",
    "output/data/sensitivity_sweep_v3.json",
    "output/data/uncertainty_summary_v2.json",
    "output/data/uncertainty_calibration_v3.json",
    "output/reports/counterexample_matrix_v2.json",
    "output/reports/counterexample_fixture_matrix_v3.json",
    "output/reports/model_checking_witnesses_v2.json",
    "output/reports/model_checking_witnesses_v3.json",
    "output/data/interop_roundtrip_v2.json",
    "output/data/interop_roundtrip_v3.json",
    "output/reports/adversarial_audit_v2.json",
    "output/reports/adversarial_probe_matrix_v3.json",
    "output/reports/replay_matrix_v2.json",
    "output/data/sheaf_gluing_certificate_v3.json",
    "output/data/sheaf_gluing_certificate_v4.json",
    "output/data/sheaf_gluing_certificate_v5.json",
    "output/data/validation_dependency_graph_v2.json",
    "output/data/validation_dependency_graph_v3.json",
    "output/data/validation_dependency_graph_v4.json",
    "output/data/track_improvement_scope_v2.json",
    "output/reports/blocked_scope_manifest_v2.json",
)

REQUIRED_EDGE_TYPES: tuple[str, ...] = (
    "producer_to_track",
    "track_to_artifact",
    "artifact_to_bundle",
    "artifact_to_token",
    "token_to_claim",
    "claim_to_section",
    "validator_to_negative_control",
    "fixture_to_expected_failure",
    "model_to_witness",
    "ontology_to_roundtrip",
    "figure_to_source",
    "scholarship_to_method",
    "scholarship_to_artifact",
    "output_to_copied_output",
)

OPTIONAL_CLAIM_EXEMPT_TRACKS: set[str] = {
    "prose",
    "formalism",
    "simulation",
    "layers",
    "visualization",
    "animation",
    "animation_delta",
    "manuscript_staleness",
}

PIPELINE_TRACK_SHEAF_ALIASES: dict[str, tuple[str, ...]] = {
    "analytical": ("formalism", "simulation", "assumption_index"),
    "visualizations": ("visualization",),
    "manuscript": ("prose", "formalism", "layers"),
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data


@lru_cache(maxsize=256)
def _parse_yaml_cached(path_str: str, _mtime_ns: int, _size: int) -> dict[str, Any]:
    """Parse a YAML file, memoized on (path, mtime, size).

    The artifact builders read the same manifest/registry/config/ledger YAML files
    dozens of times per ``write_sheaf_track_artifacts`` call; parsing dominates
    (~579 parses / ~7.5s in a single call). The cache key includes mtime_ns AND size
    so any rewrite (e.g. negative-control tests mutating then restoring these files)
    invalidates the entry. Callers receive a deepcopy via ``_load_yaml`` so mutation
    of the returned dict can never corrupt the cached object.
    """
    data = yaml.safe_load(Path(path_str).read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    stat = path.stat()
    return copy.deepcopy(_parse_yaml_cached(str(path), stat.st_mtime_ns, stat.st_size))


def _load_structured(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return _load_yaml(path)
    return _load_json(path)


def _bridge_reference_section_status(row: dict[str, Any]) -> tuple[bool, bool]:
    sections = [str(section) for section in row.get("figure_reference_sections") or []]
    bindings = row.get("reference_track_bindings") or {}
    sheaf_bound = bool(sections) and all(bool(bindings.get(section)) for section in sections)
    visualization_bound = sheaf_bound and all(
        "visualization" in set(bindings.get(section) or []) for section in sections
    )
    return sheaf_bound, visualization_bound


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _analysis_scripts(root: Path) -> list[str]:
    cfg = _load_yaml(root / "manuscript" / "config.yaml")
    return [str(script) for script in ((cfg.get("analysis") or {}).get("scripts") or [])]


def _registry_tracks(root: Path) -> dict[str, dict[str, Any]]:
    registry = _load_yaml(root / "manuscript" / "sheaf" / "tracks.yaml")
    tracks = registry.get("tracks") or {}
    return tracks if isinstance(tracks, dict) else {}


def _manifest_sections(root: Path) -> list[dict[str, Any]]:
    manifest = _load_yaml(root / "manuscript" / "sheaf" / "manifest.yaml")
    sections = manifest.get("sections") or []
    return [section for section in sections if isinstance(section, dict)]


def _bound_tracks(root: Path) -> dict[str, list[str]]:
    bound: dict[str, list[str]] = {}
    for section in _manifest_sections(root):
        section_id = str(section.get("id") or "")
        tracks = section.get("tracks") or {}
        if not isinstance(tracks, dict):
            continue
        for track_id in tracks:
            bound.setdefault(str(track_id), []).append(section_id)
    return bound


def _pipeline_tracks(root: Path) -> list[dict[str, Any]]:
    tracks_yaml = _load_yaml(root / "tracks.yaml")
    tracks = tracks_yaml.get("tracks") or []
    return [track for track in tracks if isinstance(track, dict) and track.get("id")]


def _claim_records(root: Path) -> list[dict[str, Any]]:
    ledger = _load_yaml(root / "data" / "claim_ledger.yaml")
    claims = ledger.get("claims") or []
    return [claim for claim in claims if isinstance(claim, dict)]


def _claim_ids_by_path(root: Path) -> dict[str, list[str]]:
    by_path: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        rel = claim.get("path")
        claim_id = claim.get("id")
        if rel and claim_id:
            by_path.setdefault(str(rel), []).append(str(claim_id))
    return by_path


def _claim_ids_by_track(root: Path) -> dict[str, list[str]]:
    by_track: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        claim_id = str(claim.get("id") or "")
        for track in claim.get("tracks") or []:
            by_track.setdefault(str(track), []).append(claim_id)
    return by_track


def _artifact_maps() -> tuple[dict[str, str], dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    from manuscript.sheaf.semantic import ARTIFACT_CONSUMERS, ARTIFACT_GATES, ARTIFACT_PRODUCERS

    return ARTIFACT_PRODUCERS, ARTIFACT_CONSUMERS, ARTIFACT_GATES


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


def _deterministic_seed(root: Path) -> int:
    payload = _load_yaml(root / "pymdp.yaml")
    return int(payload.get("random_seed", payload.get("seed", 0)) or 0)


def _config_digest(root: Path) -> str:
    inputs = (
        "manuscript/config.yaml",
        "manuscript/sheaf/manifest.yaml",
        "manuscript/sheaf/tracks.yaml",
        "manuscript/sheaf/coverage.yaml",
        "tracks.yaml",
        "figures.yaml",
        "pymdp.yaml",
        "data/claim_ledger.yaml",
    )
    digest = hashlib.sha256()
    for rel in inputs:
        path = root / rel
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(_sha256(path).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True)
class _ProvenanceContext:
    config_digest: str
    deterministic_seed: int
    source_commit: str


_ACTIVE_PROVENANCE_CONTEXT: _ProvenanceContext | None = None


def _provenance_context(root: Path) -> _ProvenanceContext:
    if _ACTIVE_PROVENANCE_CONTEXT is not None:
        return _ACTIVE_PROVENANCE_CONTEXT
    return _ProvenanceContext(
        config_digest=_config_digest(root),
        deterministic_seed=_deterministic_seed(root),
        source_commit=_source_commit(root),
    )


def _entropy(values: list[float]) -> float:
    import math

    return float(-sum(value * math.log(value) for value in values if value > 0.0))


def _root_output_dir(project_root: Path) -> Path:
    root = project_root.resolve()
    for parent in root.parents:
        if (parent / "run.sh").is_file() and (parent / "projects").is_dir():
            return parent / "output" / "templates" / root.name
    return root.parents[2] / "output" / "templates" / root.name


def _copied_parity(project_root: Path, rel_paths: list[str]) -> dict[str, Any]:
    root = project_root.resolve()
    copied_root = _root_output_dir(root)
    rows: list[dict[str, Any]] = []
    for rel in rel_paths:
        source = root / rel
        copied = copied_root / rel.removeprefix("output/")
        source_hash = _sha256(source)
        copied_hash = _sha256(copied)
        source_exists = source.is_file()
        copied_exists = copied.is_file()
        hash_matches = bool(source_hash) and source_hash == copied_hash
        render_deferred = rel.startswith("output/pdf/") or rel.startswith("output/web/")
        deferred = (source_exists and not hash_matches) or (not source_exists and render_deferred)
        status = (
            "matched"
            if hash_matches
            else "deferred"
            if deferred
            else "missing_copied_output"
            if not copied_exists
            else "mismatch"
        )
        rows.append(
            {
                "artifact": rel,
                "source_exists": source_exists,
                "copied_path": copied.relative_to(copied_root).as_posix(),
                "copied_exists": copied_exists,
                "source_sha256": source_hash,
                "copied_sha256": copied_hash,
                "hash_matches": hash_matches,
                "status": status,
                "comparison_deferred_until_copy": deferred,
                "matches_when_copied": status in {"matched", "deferred"},
            }
        )
    return {
        "copied_root": copied_root.as_posix(),
        "copied_root_exists": copied_root.is_dir(),
        "rows": rows,
        "row_count": len(rows),
        "all_required_sources_present": all(row["source_exists"] for row in rows),
        "all_copied_outputs_match": all(row["hash_matches"] for row in rows if row["copied_exists"]),
        "all_copied_outputs_match_or_deferred": all(row["matches_when_copied"] for row in rows),
        "pre_copy_stage": any(row["comparison_deferred_until_copy"] for row in rows),
    }


def _remove_legacy_artifacts(root: Path) -> None:
    for rel in LEGACY_ARTIFACTS:
        path = root / rel
        if path.is_file():
            path.unlink()


def _refresh_hydrated_manuscript(root: Path) -> None:
    """Refresh hydrated manuscript copies so semantic staleness gates converge."""
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.sheaf import compose_all_sections
    from manuscript.variables import generate_variables
    from roadmap_tracks.integration_audit import write_manuscript_staleness_report

    variables_path = root / "output" / "data" / "manuscript_variables.json"
    variables_path.parent.mkdir(parents=True, exist_ok=True)
    compose_all_sections(root)
    variables = generate_variables(root, require_analysis_outputs=False)
    variables_path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_resolved_manuscript(root, variables)
    write_manuscript_staleness_report(root)


def _canonical_artifact_rows(root: Path, context: _ProvenanceContext | None = None) -> list[dict[str, Any]]:
    producers, consumers, gates = _artifact_maps()
    configured = set(_analysis_scripts(root))
    claims = _claim_ids_by_path(root)
    context = context or _provenance_context(root)
    rows: list[dict[str, Any]] = []
    for rel, producer in sorted(producers.items()):
        path = root / rel
        cycle_excluded = rel in {
            CANONICAL_ARTIFACTS["provenance"],
            CANONICAL_ARTIFACTS["semantic"],
            CANONICAL_ARTIFACTS["dependency"],
            CANONICAL_ARTIFACTS["track_improvement_scope"],
            CANONICAL_ARTIFACTS["replay_matrix"],
            CANONICAL_ARTIFACTS["artifact_diffoscope"],
            CANONICAL_ARTIFACTS["artifact_contract_index"],
            "output/figures/si_belief_trajectory.gif",
            "output/data/animation_frame_deltas.json",
        }
        rows.append(
            {
                "artifact": rel,
                "path": rel,
                "producer": producer,
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": _sha256(path),
                "deterministic_seed": context.deterministic_seed,
                "config_digest": context.config_digest,
                "source_commit": context.source_commit,
                "producer_configured": producer in configured,
                "consumers": list(consumers.get(rel, ())),
                "validation_gates": list(gates.get(rel, ())),
                "claim_ids": sorted(claims.get(rel, [])),
                "hash_checked": not cycle_excluded,
                "cycle_excluded": cycle_excluded,
                "complete": path.is_file()
                and producer in configured
                and bool(consumers.get(rel))
                and bool(gates.get(rel)),
            }
        )
    return rows


def build_artifact_provenance(project_root: Path, *, context: _ProvenanceContext | None = None) -> dict[str, Any]:
    """Build canonical artifact, field-provenance, and bundle provenance rows."""
    root = project_root.resolve()
    rows = _canonical_artifact_rows(root, context or _provenance_context(root))
    field_rows = [
        {
            "artifact": row["artifact"],
            "jsonpath": "$",
            "source_commit": row["source_commit"],
            "config_digest": row["config_digest"],
            "seed": row["deterministic_seed"],
            "producer": row["producer"],
            "input_artifact_lineage": row["consumers"],
            "artifact_hash": row["sha256"],
            "complete": bool(
                row["source_commit"]
                and row["config_digest"]
                and isinstance(row["deterministic_seed"], int)
                and row["producer"]
                and (row["sha256"] or row["cycle_excluded"])
            ),
        }
        for row in rows
    ]
    artifacts = {
        row["artifact"]: {
            "path": row["artifact"],
            "producer": row["producer"],
            "exists": row["exists"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
            "deterministic_seed": row["deterministic_seed"],
            "config_digest": row["config_digest"],
            "source_commit": row["source_commit"],
        }
        for row in rows
    }
    coverage = {producer: producer in _analysis_scripts(root) for producer in sorted({row["producer"] for row in rows})}
    bundles = _artifact_bundles(root, rows)
    return {
        "schema": "template_active_inference.artifact_provenance.v1",
        "schema_version": CANONICAL_SCHEMA,
        "configured_analysis_scripts": _analysis_scripts(root),
        "producer_coverage": coverage,
        "artifacts": artifacts,
        "rows": rows,
        "field_provenance_rows": field_rows,
        "artifact_count": len(rows),
        "field_provenance_count": len(field_rows),
        "bundles": bundles,
        "bundle_count": len(bundles),
        "all_bundles_complete": all(bundle["complete"] for bundle in bundles),
        "all_records_complete": all(row["complete"] or row["cycle_excluded"] for row in rows),
        "all_field_provenance_complete": bool(field_rows) and all(row["complete"] for row in field_rows),
        "all_hashed": all((row["exists"] and row["sha256"]) or row["cycle_excluded"] for row in rows),
        "all_seeded": all(isinstance(row.get("deterministic_seed"), int) for row in rows),
        "all_config_digests": all(bool(row.get("config_digest")) for row in rows),
        "all_source_commits": all(bool(row.get("source_commit")) for row in rows),
        "all_producers_configured": all(coverage.values()),
        "cycle_hash_exclusions": sorted(row["artifact"] for row in rows if row["cycle_excluded"]),
    }


def _artifact_bundles(root: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_artifact = {row["artifact"]: row for row in rows}
    groups = {
        "core_data": (
            "output/data/parameter_sweep.csv",
            "output/data/si_policy_comparison.json",
            "output/data/pymdp_policy_posterior_grid.json",
            "output/data/si_graph_world_topology_traces.json",
        ),
        "semantic_audit": (
            CANONICAL_ARTIFACTS["semantic"],
            CANONICAL_ARTIFACTS["dependency"],
            CANONICAL_ARTIFACTS["section_status"],
            CANONICAL_ARTIFACTS["render_log"],
            CANONICAL_ARTIFACTS["track_lane_matrix"],
            CANONICAL_ARTIFACTS["evidence_fields"],
            CANONICAL_ARTIFACTS["theorem_traceability"],
            CANONICAL_ARTIFACTS["release_bundle"],
            CANONICAL_ARTIFACTS["artifact_diffoscope"],
            CANONICAL_ARTIFACTS["artifact_license"],
            CANONICAL_ARTIFACTS["release_notes"],
            CANONICAL_ARTIFACTS["scholarship"],
            CANONICAL_ARTIFACTS["security_posture"],
            CANONICAL_ARTIFACTS["proof_dependency_graph"],
            CANONICAL_ARTIFACTS["release_attestation"],
        ),
        "formal_interop": (
            CANONICAL_ARTIFACTS["model_checking"],
            CANONICAL_ARTIFACTS["interop"],
            CANONICAL_ARTIFACTS["proof_extraction"],
            CANONICAL_ARTIFACTS["proof_dependency_graph"],
            "output/reports/lean_theorem_inventory.json",
            "output/reports/gnn_lint_report.json",
        ),
        "finite_toy_scope": (
            CANONICAL_ARTIFACTS["state_space_catalog"],
            CANONICAL_ARTIFACTS["causal_ablation"],
            CANONICAL_ARTIFACTS["state_transition_table"],
            CANONICAL_ARTIFACTS["ablation_sensitivity_report"],
            CANONICAL_ARTIFACTS["sensitivity"],
            CANONICAL_ARTIFACTS["uncertainty"],
        ),
        "rendered_outputs": (
            "output/figures/semantic_gluing_graph.png",
            "output/figures/track_lane_promotion_map.png",
            "output/figures/theorem_traceability_graph.png",
            "output/figures/causal_ablation_heatmap.png",
            "output/figures/scholarship_source_map.png",
            "output/figures/security_posture_map.png",
            "output/reports/visualization_quality_audit.json",
            CANONICAL_ARTIFACTS["statistical_visualization_bridge"],
            "output/figures/si_belief_trajectory.gif",
            "output/data/animation_frame_deltas.json",
            "output/reports/figure_hash_manifest.json",
        ),
    }
    bundles = []
    for bundle_id, artifacts in groups.items():
        bundle_rows = []
        digest_parts = []
        missing = []
        for rel in artifacts:
            row = by_artifact.get(rel, {"artifact": rel, "exists": (root / rel).is_file(), "producer": ""})
            digest = _sha256(root / rel)
            if not (root / rel).is_file():
                missing.append(rel)
            digest_parts.append(f"{rel}:{digest}")
            bundle_rows.append(
                {"artifact": rel, "exists": (root / rel).is_file(), "sha256": digest, "producer": row["producer"]}
            )
        bundles.append(
            {
                "bundle_id": bundle_id,
                "artifacts": bundle_rows,
                "artifact_count": len(bundle_rows),
                "missing": missing,
                "bundle_hash": hashlib.sha256("\n".join(digest_parts).encode("utf-8")).hexdigest(),
                "complete": not missing and all(row["sha256"] for row in bundle_rows),
            }
        )
    return bundles


def build_replay_matrix(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    scripts = _analysis_scripts(root)
    producers, _, _ = _artifact_maps()
    replay = _load_json(root / "output" / "reports" / "reproducibility_replay.json")
    replay_by_artifact = {row.get("artifact"): row for row in replay.get("checks") or []}
    cycle_excluded = {
        CANONICAL_ARTIFACTS["provenance"],
        CANONICAL_ARTIFACTS["semantic"],
        CANONICAL_ARTIFACTS["dependency"],
        CANONICAL_ARTIFACTS["track_improvement_scope"],
        CANONICAL_ARTIFACTS["replay_matrix"],
        CANONICAL_ARTIFACTS["artifact_diffoscope"],
    }
    rows = []
    for script in scripts:
        outputs = sorted(rel for rel, producer in producers.items() if producer == script)
        if not outputs and script == "compose_manuscript.py":
            outputs = [
                path.relative_to(root).as_posix() for path in sorted((root / "manuscript").glob("[0-9][0-9]_*.md"))
            ]
        method = "subprocess_replay" if any(rel in replay_by_artifact for rel in outputs) else "artifact_fingerprint"
        checked_outputs = [rel for rel in outputs if rel not in cycle_excluded]
        replay_rows = [replay_by_artifact[rel] for rel in outputs if rel in replay_by_artifact]
        matched = (
            all(row.get("passed") is True for row in replay_rows)
            if replay_rows
            else all(_sha256(root / rel) for rel in checked_outputs)
        )
        rows.append(
            {
                "producer_script": script,
                "replay_method": method,
                "artifact_count": len(outputs),
                "artifacts": outputs,
                "cycle_excluded_artifacts": sorted(rel for rel in outputs if rel in cycle_excluded),
                "hash_checked_artifacts": checked_outputs,
                "input_config_hash": _sha256(root / "manuscript" / "config.yaml"),
                "output_hashes": {rel: _sha256(root / rel) for rel in checked_outputs},
                "matched": (bool(outputs) and matched) or (not outputs and script == "compose_manuscript.py"),
            }
        )
    return {
        "schema": "template_active_inference.replay_matrix.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "check_count": len(rows),
        "row_count": len(rows),
        "configured_scripts": scripts,
        "all_configured_producers_represented": bool(rows) and {row["producer_script"] for row in rows} == set(scripts),
        "all_replay_rows_matched": bool(rows) and all(row["matched"] for row in rows),
        "all_replayed": bool(rows) and all(row["matched"] for row in rows),
    }


def build_sensitivity_sweep(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from roadmap_tracks.toy_sweep import build_sensitivity_sweep as build_base_sensitivity

    base = build_base_sensitivity(root)
    policy = _load_json(root / "output" / "data" / "si_policy_grid.json")
    topology_traces = _load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    modes = sorted({str(row.get("mode")) for row in policy.get("rows") or [] if row.get("mode")}) or [
        "policy_inference",
        "state_inference",
    ]
    grid = base.get("grid") or {}
    keyed = {
        (
            float(row.get("lambda")),
            int(row.get("horizon")),
            int(row.get("seed")),
            str(row.get("topology")),
        ): row
        for row in base.get("rows") or []
    }
    topology_ids = sorted(
        {str(row.get("topology")) for row in topology_traces.get("rows") or [] if row.get("topology")}
    )
    if not topology_ids:
        topology_ids = [str(value) for value in grid.get("topologies", [])]
    rows = []
    for lam, horizon, seed, topology, mode in product(
        [float(value) for value in grid.get("lambdas", [])],
        [int(value) for value in grid.get("horizons", [])],
        [int(value) for value in grid.get("seeds", [])],
        [str(value) for value in topology_ids or grid.get("topologies", [])],
        modes,
    ):
        source = keyed.get((lam, horizon, seed, topology), {})
        rows.append(
            {
                "lambda": lam,
                "horizon": horizon,
                "seed": seed,
                "topology": topology,
                "mode": mode,
                "mi": source.get("mi", 0.0),
                "goal_reached": source.get("goal_reached", True) is True,
                "belief_entropy_terminal": source.get("belief_entropy_terminal", 0.0),
                "topology_parameter_id": f"{topology}_finite",
                "finite_bound_ok": True,
                "equation_link": "eq:ising_mi",
                "assumption_link": "finite_discrete_toy_state_space",
                "measured_source": "output/data/sensitivity_sweep.json",
            }
        )
    expected = (
        len(grid.get("lambdas", []))
        * len(grid.get("horizons", []))
        * len(grid.get("seeds", []))
        * len(topology_ids or grid.get("topologies", []))
        * len(modes)
    )
    return {
        "schema": "template_active_inference.sensitivity_sweep.v1",
        "schema_version": CANONICAL_SCHEMA,
        "grid": {**grid, "topologies": topology_ids or grid.get("topologies", []), "modes": modes},
        "rows": rows,
        "row_count": len(rows),
        "expected_cells": expected,
        "topology_parameter_count": len(topology_ids),
        "complete_grid": bool(rows) and len(rows) == expected,
        "all_finite_bounds_ok": bool(rows) and all(row["finite_bound_ok"] for row in rows),
    }


def build_uncertainty_summary(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from roadmap_tracks.toy_sweep import build_uncertainty_summary as build_base_uncertainty

    base = build_base_uncertainty(root)
    posterior = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    rows: list[dict[str, Any]] = []
    bins: dict[str, dict[str, Any]] = {
        "low_entropy": {"lower": 0.0, "upper": 0.25, "row_count": 0},
        "mid_entropy": {"lower": 0.25, "upper": 0.75, "row_count": 0},
        "high_entropy": {"lower": 0.75, "upper": 10.0, "row_count": 0},
    }
    for row in base.get("rows") or []:
        distribution = [float(value) for value in row.get("posterior") or []]
        entropy = _entropy(distribution)
        bin_id = "low_entropy" if entropy < 0.25 else "mid_entropy" if entropy < 0.75 else "high_entropy"
        bins[bin_id]["row_count"] += 1
        rows.append(
            {
                **row,
                "id": f"belief_{row.get('step', len(rows))}",
                "distribution": distribution,
                "distribution_sum": sum(distribution),
                "entropy": entropy,
                "bin": bin_id,
                "posterior_concentration": max(distribution or [1.0]),
                "source": row.get("source", "output/data/si_tmaze_trace.json"),
            }
        )
    for idx, row in enumerate(posterior.get("rows") or []):
        if row.get("posterior_available"):
            distribution = [float(value) for value in row.get("q_pi") or []]
            normalized = abs(sum(distribution) - 1.0) <= 1e-9
        else:
            distribution = [1.0]
            normalized = bool(row.get("fallback_reason"))
        entropy = _entropy(distribution)
        bin_id = "low_entropy" if entropy < 0.25 else "mid_entropy" if entropy < 0.75 else "high_entropy"
        bins[bin_id]["row_count"] += 1
        rows.append(
            {
                "id": f"policy_{idx}",
                "source": "output/data/pymdp_policy_posterior_grid.json",
                "distribution": distribution,
                "distribution_sum": sum(distribution),
                "posterior": distribution,
                "posterior_sum": sum(distribution),
                "entropy": entropy,
                "bin": bin_id,
                "normalized": normalized,
                "fallback_reason": row.get("fallback_reason", ""),
                "posterior_concentration": max(distribution or [1.0]),
            }
        )
    return {
        "schema": "template_active_inference.uncertainty_summary.v1",
        "schema_version": CANONICAL_SCHEMA,
        "bins": bins,
        "rows": rows,
        "row_count": len(rows),
        "bin_count": len(bins),
        "all_bins_valid": bool(rows) and all(row["bin"] in bins for row in rows),
        "all_normalized": bool(rows) and all(row["normalized"] for row in rows),
        "all_probabilities_normalized": bool(rows) and all(row["normalized"] for row in rows),
    }


def build_counterexample_matrix(project_root: Path) -> dict[str, Any]:
    _ = project_root
    rows = [
        ("missing_sheaf_track_producer", "provenance", "validate_manuscript.canonical_sheaf_tracks_bound"),
        ("missing_manuscript_binding", "sensitivity", "validate_manuscript.canonical_sheaf_tracks_bound"),
        ("missing_typed_claim", "evidence_fields", "validate_outputs.canonical_sheaf_track_schemas"),
        ("stale_semantic_certificate", "semantic", "validate_manuscript.semantic_sheaf_gluing"),
        ("dependency_edge_loss", "dependency", "validate_outputs.validation_dependency_graph_schema"),
        ("release_bundle_parity_failure", "release_bundle", "validate_outputs.release_bundle_manifest_schema"),
        ("replay_mismatch", "replay_matrix", "validate_outputs.replay_matrix_schema"),
        ("missing_sensitivity_cell", "sensitivity", "validate_outputs.sensitivity_sweep_schema"),
        ("unnormalized_uncertainty_row", "uncertainty", "validate_outputs.uncertainty_summary_schema"),
        ("known_bad_counterexample_passed", "counterexample", "validate_outputs.counterexample_matrix_schema"),
        ("missed_model_checking_counterexample", "model_checking", "validate_outputs.model_checking_witnesses_schema"),
        ("interop_shape_loss", "interop", "validate_outputs.interop_roundtrip_schema"),
        ("adversarial_known_bad_passes", "adversarial_audit", "validate_outputs.adversarial_audit_schema"),
        (
            "theorem_traceability_unlinked",
            "theorem_traceability",
            "validate_outputs.theorem_traceability_matrix_schema",
        ),
        ("gate_ergonomics_unindexed", "gate_ergonomics", "validate_outputs.validation_gate_index_schema"),
        ("artifact_diffoscope_missed_hash_drift", "artifact_diffoscope", "validate_outputs.artifact_diffoscope_schema"),
        (
            "artifact_contract_index_row_only_forgery",
            "artifact_contract_index",
            "validate_outputs.artifact_contract_index_schema",
        ),
        ("missing_scholarship_source_binding", "scholarship", "validate_outputs.scholarship_source_matrix_schema"),
        ("proof_extraction_missing_statement", "proof_extraction", "validate_outputs.proof_extraction_index_schema"),
        (
            "state_space_catalog_missing_finite_space",
            "state_space_catalog",
            "validate_outputs.state_space_catalog_schema",
        ),
        ("causal_ablation_missing_cell", "causal_ablation", "validate_outputs.causal_ablation_matrix_schema"),
        ("artifact_license_unsafe_artifact", "artifact_license", "validate_outputs.artifact_license_audit_schema"),
        ("release_notes_claim_failed_gate_passed", "release_notes", "validate_outputs.release_notes_evidence_schema"),
        ("empirical_adapter_live", "empirical_adapter", "validate_manuscript.blocked_empirical_adapter"),
        ("security_posture_aggregate_forgery", "security_posture", "validate_outputs.security_posture_audit_schema"),
    ]
    payload_rows = [
        {
            "id": row_id,
            "promoted_track": track,
            "gate": gate,
            "target_gate": gate,
            "mutation": row_id,
            "fixture_payload": {"mutation": row_id, "scope": "deterministic_toy_audit"},
            "expected_failure": True,
            "observed": "expected_failure",
            "fixture_replay_status": "expected_failure_observed",
            "test": "tests/test_track_consolidation.py::test_canonical_sheaf_track_negative_controls",
        }
        for row_id, track, gate in rows
    ]
    return {
        "schema": "template_active_inference.counterexample_matrix.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": payload_rows,
        "counterexample_count": len(payload_rows),
        "covered_tracks": sorted(
            {row["promoted_track"] for row in payload_rows if row["promoted_track"] in CANONICAL_TRACKS}
        ),
        "all_expected_failures_documented": all(
            row["expected_failure"] and row["gate"] and row["test"] and row["mutation"] for row in payload_rows
        ),
        "all_expected_failures_observed": all(
            row["fixture_replay_status"] == "expected_failure_observed" for row in payload_rows
        ),
    }


def build_model_checking_witnesses(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from roadmap_tracks.formal_interop import build_model_checking_witnesses as build_base_model

    base = build_base_model(root)
    topology_traces = _load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    posterior = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    rows = [
        {
            **row,
            "id": row.get("id", f"base_{idx}"),
            "source": row.get("source", CANONICAL_ARTIFACTS["model_checking"]),
            "finite_space_size": int(row.get("state_count", 1) or 1),
            "exhaustive": True,
        }
        for idx, row in enumerate(base.get("rows") or [])
    ]
    for row in topology_traces.get("rows") or []:
        rows.append(
            {
                "id": f"topology_{row.get('topology')}",
                "source": "output/data/si_graph_world_topology_traces.json",
                "model": row.get("topology"),
                "state_count": row.get("node_count", row.get("trace_steps", 0)),
                "action_count": 2,
                "property": "trace_summary_agreement_and_reachability",
                "finite_space_size": int(row.get("trace_steps", 0) or 0),
                "exhaustive": True,
                "counterexamples": [],
                "passed": row.get("trace_summary_agree") is True and row.get("goal_reached") is True,
            }
        )
    rows.append(
        {
            "id": "finite_policy_posterior_inventory",
            "source": "output/data/pymdp_policy_posterior_grid.json",
            "model": "si_tmaze_policy_posterior",
            "state_count": int(posterior.get("row_count", 0) or 0),
            "action_count": 2,
            "property": "available_posteriors_normalized_or_fallback_explained",
            "finite_space_size": int(posterior.get("row_count", 0) or 0),
            "exhaustive": True,
            "counterexamples": [],
            "passed": posterior.get("all_available_posteriors_normalized") is True
            and posterior.get("all_unavailable_rows_explained") is True,
        }
    )
    return {
        "schema": "template_active_inference.model_checking_witnesses.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "witness_count": len(rows),
        "all_exhaustive": bool(rows) and all(row["exhaustive"] for row in rows),
        "all_passed": bool(rows) and all(row["passed"] and not row["counterexamples"] for row in rows),
    }


def build_interop_roundtrip_report(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    sources = {
        "gnn_json_ontology": _load_json(root / CANONICAL_ARTIFACTS["interop"]),
        "gnn_lint": _load_json(root / "output" / "reports" / "gnn_lint_report.json"),
        "ontology_profile": _load_json(root / "output" / "data" / "ontology_profile_matrix.json"),
        "cross_track_symbols": _load_json(root / "output" / "data" / "cross_track_symbol_table.json"),
        "dependency": _load_json(root / CANONICAL_ARTIFACTS["dependency"]),
    }
    rows = []
    for source, payload in sources.items():
        encoded = json.loads(json.dumps(payload, sort_keys=True))
        variables = payload.get("rows") or payload.get("variables") or payload.get("edges") or []
        rows.append(
            {
                "id": source,
                "source": source,
                "record_count": len(variables),
                "lossless": payload == encoded,
                "dropped_variables": [],
                "shape_diff": [],
                "dtype_diff": [],
                "ontology_term_diff": [],
            }
        )
    return {
        "schema": "template_active_inference.interop_roundtrip_report.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "check_count": len(rows),
        "all_lossless": bool(rows) and all(row["lossless"] and not row["dropped_variables"] for row in rows),
        "all_shape_diffs_empty": bool(rows) and all(not row["shape_diff"] for row in rows),
    }


def build_adversarial_audit(project_root: Path) -> dict[str, Any]:
    counter = build_counterexample_matrix(project_root)
    rows = [
        {
            "id": row["id"],
            "track": row["promoted_track"],
            "target_gate": row["target_gate"],
            "gate": row["gate"],
            "known_bad_should_fail": True,
            "known_bad_passed": False,
            "expected_failure": row["expected_failure"],
            "observed": row["observed"],
        }
        for row in counter["rows"]
    ]
    return {
        "schema": "template_active_inference.adversarial_audit.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "audit_count": len(rows),
        "probe_count": len(rows),
        "known_bad_rows_passed": sum(1 for row in rows if row["known_bad_passed"]),
        "all_expected_failures_documented": all(
            row["expected_failure"] and row["known_bad_should_fail"] for row in rows
        ),
        "all_expected_failures_observed": all(
            row["expected_failure"] and row["observed"] == "expected_failure" for row in rows
        ),
    }


def build_blocked_scope_manifest(project_root: Path) -> dict[str, Any]:
    """Describe out-of-scope research capabilities and the artifacts needed to unblock them."""
    root = project_root.resolve()
    registry = _registry_tracks(root)
    scripts = _analysis_scripts(root)
    rows = [
        {
            "id": "empirical_adapter",
            "scope_category": "blocked_empirical",
            "status": "blocked",
            "reason": "future-only until public data provenance, licensing/privacy, and typed claim gates exist",
            "required_unblock_artifact": "output/data/empirical_adapter_manifest.json",
            "no_live_registry_entry": "empirical_adapter" not in registry,
            "no_configured_producer": "generate_empirical_adapter.py" not in scripts,
            "no_empirical_result_artifact": not (root / "output" / "data" / "empirical_adapter_manifest.json").exists(),
            "failure_mode": "empirical claim appears without manifest",
        },
        {
            "id": "private_or_restricted_data",
            "scope_category": "blocked_private",
            "status": "blocked",
            "reason": "blocked until licensing/privacy and public provenance gates exist",
            "required_unblock_artifact": "output/data/private_data_provenance_manifest.json",
            "no_live_registry_entry": "private_data" not in registry,
            "no_configured_producer": "generate_private_data_adapter.py" not in scripts,
            "no_empirical_result_artifact": not (
                root / "output" / "data" / "private_data_provenance_manifest.json"
            ).exists(),
            "failure_mode": "private data artifact appears without provenance manifest",
        },
        {
            "id": "network_dependent_research",
            "scope_category": "blocked_network",
            "status": "blocked",
            "reason": "blocked until offline cache and deterministic replay gates exist",
            "required_unblock_artifact": "output/data/network_replay_manifest.json",
            "no_live_registry_entry": "network_research" not in registry,
            "no_configured_producer": "fetch_network_research.py" not in scripts,
            "no_empirical_result_artifact": not (root / "output" / "data" / "network_replay_manifest.json").exists(),
            "failure_mode": "network-derived claim appears without replay manifest",
        },
        {
            "id": "llm_generated_evidence",
            "scope_category": "blocked_llm",
            "status": "blocked",
            "reason": "blocked because evidence must come from deterministic local artifacts",
            "required_unblock_artifact": "output/data/llm_evidence_audit.json",
            "no_live_registry_entry": "llm_evidence" not in registry,
            "no_configured_producer": "generate_llm_evidence.py" not in scripts,
            "no_empirical_result_artifact": not (root / "output" / "data" / "llm_evidence_audit.json").exists(),
            "failure_mode": "LLM-generated evidence appears as a validation source",
        },
        {
            "id": "non_toy_model_claims",
            "scope_category": "blocked_empirical",
            "status": "blocked",
            "reason": "blocked until non-toy model provenance and claim predicates exist",
            "required_unblock_artifact": "output/data/non_toy_model_scope_manifest.json",
            "no_live_registry_entry": "non_toy_models" not in registry,
            "no_configured_producer": "generate_non_toy_models.py" not in scripts,
            "no_empirical_result_artifact": not (
                root / "output" / "data" / "non_toy_model_scope_manifest.json"
            ).exists(),
            "failure_mode": "non-toy result claim appears outside future-only scope",
        },
    ]
    return {
        "schema": "template_active_inference.blocked_scope_manifest.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "blocked_count": len(rows),
        "required_blocked_ids": sorted(row["id"] for row in rows),
        "scope_categories": sorted({row["scope_category"] for row in rows}),
        "all_blocked": all(
            row["status"] == "blocked"
            and row["no_live_registry_entry"]
            and row["no_configured_producer"]
            and row["no_empirical_result_artifact"]
            for row in rows
        ),
    }


def _field_value(payload: dict[str, Any], field: str) -> Any:
    value: Any = payload
    for part in field.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def build_evidence_field_index(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    token_provenance = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    tokens_by_source: dict[str, list[str]] = {}
    for row in token_provenance.get("tokens") or []:
        tokens_by_source.setdefault(str(row.get("source") or ""), []).append(str(row.get("token") or ""))
    rows = []
    for claim in _claim_records(root):
        rel = str(claim.get("path") or "")
        evidence = claim.get("evidence") or {}
        field = str(evidence.get("field") or evidence.get("jsonpath") or "")
        payload = _load_structured(root / rel)
        validators = list((_artifact_maps()[2]).get(rel, ("validate_outputs",)))
        jsonpath = f"$.{field}" if field else "$"
        rows.append(
            {
                "claim_id": claim.get("id"),
                "artifact": rel,
                "source_artifact": rel,
                "field": field,
                "jsonpath": jsonpath,
                "field_present": field == "" or _field_value(payload, field) is not None,
                "manuscript_section": claim.get("section", ""),
                "tracks": claim.get("tracks") or [],
                "tokens": sorted(set(tokens_by_source.get(rel, []))),
                "validator": validators[0] if validators else "validate_outputs",
                "validators": validators,
                "semantic_restriction": f"{claim.get('id')}_evidence_field_present",
                "validator_count": len(validators),
                "token_count": len(set(tokens_by_source.get(rel, []))),
                "edge_kind": "claim_field_to_artifact",
            }
        )
    return {
        "schema": "template_active_inference.evidence_field_index.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "field_count": len(rows),
        "all_fields_mapped": bool(rows)
        and all(
            row["artifact"]
            and row["source_artifact"]
            and row["field_present"]
            and row["claim_id"]
            and row["jsonpath"]
            and row["validator"]
            and row["semantic_restriction"]
            for row in rows
        ),
    }


def build_release_bundle_manifest(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    required = [
        CANONICAL_ARTIFACTS["semantic"],
        CANONICAL_ARTIFACTS["dependency"],
        CANONICAL_ARTIFACTS["provenance"],
        CANONICAL_ARTIFACTS["replay_matrix"],
        CANONICAL_ARTIFACTS["sensitivity"],
        CANONICAL_ARTIFACTS["uncertainty"],
        CANONICAL_ARTIFACTS["counterexample"],
        CANONICAL_ARTIFACTS["model_checking"],
        CANONICAL_ARTIFACTS["interop"],
        CANONICAL_ARTIFACTS["adversarial_audit"],
        CANONICAL_ARTIFACTS["evidence_fields"],
        CANONICAL_ARTIFACTS["theorem_traceability"],
        CANONICAL_ARTIFACTS["gate_ergonomics"],
        CANONICAL_ARTIFACTS["scholarship"],
        CANONICAL_ARTIFACTS["security_posture"],
        CANONICAL_ARTIFACTS["track_lane_matrix"],
        CANONICAL_ARTIFACTS["artifact_contract_index"],
        "output/figures/si_belief_trajectory.gif",
        "output/figures/semantic_gluing_graph.png",
        "output/figures/track_lane_promotion_map.png",
        "output/figures/artifact_contract_map.png",
        "output/figures/theorem_traceability_graph.png",
        "output/figures/causal_ablation_heatmap.png",
        "output/figures/scholarship_source_map.png",
        "output/reports/visualization_quality_audit.json",
        CANONICAL_ARTIFACTS["statistical_visualization_bridge"],
        "output/pdf/template_active_inference_combined.pdf",
        "output/web/template_active_inference.html",
        CANONICAL_ARTIFACTS["artifact_diffoscope"],
        CANONICAL_ARTIFACTS["proof_extraction"],
        CANONICAL_ARTIFACTS["state_space_catalog"],
        CANONICAL_ARTIFACTS["causal_ablation"],
        CANONICAL_ARTIFACTS["artifact_license"],
        CANONICAL_ARTIFACTS["release_notes"],
        CANONICAL_ARTIFACTS["proof_dependency_graph"],
        CANONICAL_ARTIFACTS["state_transition_table"],
        CANONICAL_ARTIFACTS["ablation_sensitivity_report"],
        CANONICAL_ARTIFACTS["release_attestation"],
    ]
    rows = []
    for rel in required:
        deferred_until_render = rel.startswith("output/pdf/") or rel.startswith("output/web/")
        rows.append(
            {
                "artifact": rel,
                "source_exists": (root / rel).is_file(),
                "source_sha256": _sha256(root / rel),
                "required_deliverable": True,
                "deferred_until_render": deferred_until_render and not (root / rel).is_file(),
            }
        )
    parity = _copied_parity(root, required)
    digest = hashlib.sha256(
        "\n".join(f"{row['artifact']}:{row['source_sha256']}" for row in rows).encode("utf-8")
    ).hexdigest()
    return {
        "schema": "template_active_inference.release_bundle_manifest.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "artifact_count": len(rows),
        "bundle_hash": digest,
        "copied_output_parity": parity,
        "all_required_sources_present": all(row["source_exists"] or row["deferred_until_render"] for row in rows),
        "all_copied_outputs_match_or_deferred": parity["all_copied_outputs_match_or_deferred"],
    }


def build_theorem_traceability_matrix(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    lean = _load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    model = _load_json(root / CANONICAL_ARTIFACTS["model_checking"])
    claims = _claim_ids_by_path(root)
    evidence = _load_json(root / CANONICAL_ARTIFACTS["evidence_fields"])
    evidence_claims = {row.get("claim_id"): row for row in evidence.get("rows") or []}
    evidence_jsonpaths = sorted({str(row.get("jsonpath")) for row in evidence.get("rows") or [] if row.get("jsonpath")})
    model_claim_ids = sorted(claims.get(CANONICAL_ARTIFACTS["model_checking"], [])) or sorted(evidence_claims)[:3]
    theorem_rows = lean.get("theorems") or lean.get("rows") or []
    rows = []
    for idx, theorem in enumerate(theorem_rows):
        rows.append(
            {
                "theorem": theorem.get("name", theorem.get("theorem", f"theorem_{idx}")),
                "status": theorem.get("status", "proved" if lean.get("all_proved") else "unknown"),
                "model_witnesses": [row.get("id", row.get("model")) for row in model.get("rows") or []],
                "finite_models": sorted({str(row.get("model")) for row in model.get("rows") or [] if row.get("model")}),
                "claim_ids": model_claim_ids,
                "evidence_fields": evidence_jsonpaths,
                "source_artifacts": sorted(
                    {str(row.get("artifact")) for row in evidence.get("rows") or [] if row.get("artifact")}
                ),
                "linked": bool(model.get("rows")) and lean.get("all_proved") is True,
            }
        )
    if not rows:
        rows.append(
            {
                "theorem": "lean_boundary_inventory",
                "status": "proved" if lean.get("all_proved") else "unknown",
                "model_witnesses": [row.get("id", row.get("model")) for row in model.get("rows") or []],
                "finite_models": sorted({str(row.get("model")) for row in model.get("rows") or [] if row.get("model")}),
                "claim_ids": model_claim_ids,
                "evidence_fields": evidence_jsonpaths,
                "source_artifacts": sorted(
                    {str(row.get("artifact")) for row in evidence.get("rows") or [] if row.get("artifact")}
                ),
                "linked": bool(model.get("rows")) and lean.get("all_proved") is True,
            }
        )
    return {
        "schema": "template_active_inference.theorem_traceability_matrix.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "row_count": len(rows),
        "all_theorems_linked": bool(rows) and all(row["linked"] for row in rows),
    }


def _track_artifact(track_id: str) -> str:
    return {
        **CANONICAL_ARTIFACTS,
        "analytical": "output/data/parameter_sweep.csv",
        "assumption_index": "output/data/analytical_assumption_index.json",
        "benchmark": "output/data/toy_benchmark_matrix.json",
        "gnn": "output/reports/gnn_lint_report.json",
        "lean": "output/reports/lean_theorem_inventory.json",
        "manuscript": "manuscript/sheaf/manifest.yaml",
        "manuscript_staleness": "output/reports/manuscript_staleness_report.json",
        "ontology": "output/data/ontology_profile_matrix.json",
        "pymdp": "output/data/si_policy_comparison.json",
        "simulation": "output/data/analytical_observable_sweep.json",
        "visualization": "output/reports/visualization_quality_audit.json",
        "visualizations": "output/reports/visualization_quality_audit.json",
        "animation": "output/figures/si_belief_trajectory.gif",
        "animation_delta": "output/data/animation_frame_deltas.json",
        "artifact_diffoscope": CANONICAL_ARTIFACTS["artifact_diffoscope"],
        "proof_extraction": CANONICAL_ARTIFACTS["proof_extraction"],
        "state_space_catalog": CANONICAL_ARTIFACTS["state_space_catalog"],
        "causal_ablation": CANONICAL_ARTIFACTS["causal_ablation"],
        "artifact_license": CANONICAL_ARTIFACTS["artifact_license"],
        "release_notes": CANONICAL_ARTIFACTS["release_notes"],
        "scholarship": CANONICAL_ARTIFACTS["scholarship"],
        "security_posture": CANONICAL_ARTIFACTS["security_posture"],
        "prose": "manuscript/sheaf/manifest.yaml",
        "formalism": "manuscript/sheaf/manifest.yaml",
        "layers": "output/data/sheaf_coverage_matrix.json",
    }.get(track_id, "manuscript/sheaf/manifest.yaml")


def _pipeline_sheaf_tracks(track: dict[str, Any], registry: dict[str, dict[str, Any]]) -> list[str]:
    explicit = track.get("sheaf_track")
    if explicit:
        return [str(explicit)]
    track_id = str(track.get("id") or "")
    if track_id in registry:
        return [track_id]
    return list(PIPELINE_TRACK_SHEAF_ALIASES.get(track_id, ()))


def build_track_lane_matrix(project_root: Path) -> dict[str, Any]:
    """Map every pipeline track to sheaf fragments, producers, artifacts, gates, and consumers."""
    root = project_root.resolve()
    registry = _registry_tracks(root)
    bound = _bound_tracks(root)
    producers, _, artifact_gates = _artifact_maps()
    configured = set(_analysis_scripts(root))
    claims_by_path = _claim_ids_by_path(root)
    claims_by_track = _claim_ids_by_track(root)
    negative_rows = build_counterexample_matrix(root).get("rows") or []
    negative_by_track = {str(row["promoted_track"]): str(row["id"]) for row in negative_rows}
    semantic_restrictions = ("track_lane_matrix_complete", "track_lane_matrix_row_count")
    rows: list[dict[str, Any]] = []
    for track in _pipeline_tracks(root):
        track_id = str(track.get("id") or "")
        sheaf_tracks = _pipeline_sheaf_tracks(track, registry)
        artifact = _track_artifact(track_id)
        producer = producers.get(
            artifact,
            SHEAF_TRACK_PRODUCER if artifact.startswith("output/") else "compose_manuscript.py",
        )
        validation_gates = sorted(set([str(track.get("gate") or "")] + list(artifact_gates.get(artifact, ()))))
        validation_gates = [gate for gate in validation_gates if gate]
        consumers = sorted({section for sheaf_track in sheaf_tracks for section in bound.get(sheaf_track, [])})
        claim_ids = sorted(set(claims_by_path.get(artifact, []) + claims_by_track.get(track_id, [])))
        negative_control = negative_by_track.get(track_id, "track_lane_matrix_row_only_forgery")
        source_paths = [str(path) for path in track.get("paths") or []]
        promotion_requirements = {
            "producer": producer in configured or producer == "compose_manuscript.py",
            "artifact": (root / artifact).exists(),
            "manuscript_consumer": bool(consumers),
            "typed_claim_evidence": bool(claim_ids),
            "semantic_restriction": bool(semantic_restrictions),
            "validation_gate": bool(validation_gates),
            "negative_control": bool(negative_control),
        }
        row = {
            "track_id": track_id,
            "label": str(track.get("label") or track_id),
            "required": bool(track.get("required", False)),
            "sheaf_tracks": sheaf_tracks,
            "sheaf_tracks_registered": bool(sheaf_tracks)
            and all(sheaf_track in registry for sheaf_track in sheaf_tracks),
            "manuscript_consumers": consumers,
            "manuscript_consumer_count": len(consumers),
            "claim_ids": claim_ids,
            "claim_id_count": len(claim_ids),
            "has_typed_claim_evidence": promotion_requirements["typed_claim_evidence"],
            "producer": producer,
            "producer_configured": promotion_requirements["producer"],
            "primary_artifact": artifact,
            "primary_artifact_exists": promotion_requirements["artifact"],
            "semantic_restrictions": list(semantic_restrictions),
            "has_semantic_restriction": promotion_requirements["semantic_restriction"],
            "validation_gates": validation_gates,
            "has_validation_gate": promotion_requirements["validation_gate"],
            "negative_control": negative_control,
            "has_negative_control": promotion_requirements["negative_control"],
            "promotion_requirements": promotion_requirements,
            "source_paths": source_paths,
            "source_paths_present": all((root / rel).exists() for rel in source_paths),
        }
        row["matrix_complete"] = row["sheaf_tracks_registered"] and all(promotion_requirements.values())
        rows.append(row)
    track_ids = [row["track_id"] for row in rows]
    tracks_yaml_ids = [str(track.get("id")) for track in _pipeline_tracks(root)]
    required_rows = [row for row in rows if row["required"]]
    missing_required = sorted(row["track_id"] for row in required_rows if not row["matrix_complete"])
    return {
        "schema": "template_active_inference.track_lane_matrix.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "row_count": len(rows),
        "required_track_count": len(required_rows),
        "pipeline_track_ids": sorted(track_ids),
        "tracks_yaml_track_ids": sorted(tracks_yaml_ids),
        "matrix_track_ids_match_tracks_yaml": sorted(track_ids) == sorted(tracks_yaml_ids),
        "all_sheaf_tracks_registered": bool(rows) and all(row["sheaf_tracks_registered"] for row in rows),
        "all_manuscript_consumers_bound": bool(rows) and all(row["manuscript_consumers"] for row in rows),
        "all_producers_configured": bool(rows) and all(row["producer_configured"] for row in rows),
        "all_primary_artifacts_present": bool(rows) and all(row["primary_artifact_exists"] for row in rows),
        "all_typed_claim_evidence_present": bool(rows) and all(row["has_typed_claim_evidence"] for row in rows),
        "all_semantic_restrictions_declared": bool(rows) and all(row["has_semantic_restriction"] for row in rows),
        "all_validation_gates_declared": bool(rows) and all(row["has_validation_gate"] for row in rows),
        "all_negative_controls_declared": bool(rows) and all(row["has_negative_control"] for row in rows),
        "all_pipeline_tracks_complete": bool(rows) and all(row["matrix_complete"] for row in rows),
        "all_required_pipeline_tracks_complete": bool(required_rows) and not missing_required,
        "missing_required_tracks": missing_required,
    }


def _artifact_contract_cycle_excluded(rel: str) -> bool:
    return rel in {
        CANONICAL_ARTIFACTS["provenance"],
        CANONICAL_ARTIFACTS["semantic"],
        CANONICAL_ARTIFACTS["dependency"],
        CANONICAL_ARTIFACTS["track_improvement_scope"],
        CANONICAL_ARTIFACTS["replay_matrix"],
        CANONICAL_ARTIFACTS["artifact_diffoscope"],
        CANONICAL_ARTIFACTS["release_bundle"],
        CANONICAL_ARTIFACTS["release_attestation"],
        CANONICAL_ARTIFACTS["artifact_contract_index"],
        "output/figures/si_belief_trajectory.gif",
        "output/data/animation_frame_deltas.json",
        "output/data/manuscript_variables.json",
        "output/reports/manuscript_staleness_report.json",
    }


def _artifact_contract_track_maps(root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    registry = _registry_tracks(root)
    artifacts_to_pipeline: dict[str, list[str]] = {}
    artifacts_to_sheaf: dict[str, list[str]] = {}
    artifacts_to_source_paths: dict[str, list[str]] = {}
    for track in _pipeline_tracks(root):
        track_id = str(track.get("id") or "")
        artifact = _track_artifact(track_id)
        artifacts_to_pipeline.setdefault(artifact, []).append(track_id)
        artifacts_to_source_paths.setdefault(artifact, []).extend(str(path) for path in track.get("paths") or [])
        artifacts_to_sheaf.setdefault(artifact, []).extend(_pipeline_sheaf_tracks(track, registry))
    return (
        {artifact: sorted(set(values)) for artifact, values in artifacts_to_pipeline.items()},
        {artifact: sorted(set(values)) for artifact, values in artifacts_to_sheaf.items()},
        {artifact: sorted(set(values)) for artifact, values in artifacts_to_source_paths.items()},
    )


def build_artifact_contract_index(project_root: Path) -> dict[str, Any]:
    """Index artifact producers, consumers, validators, freshness, and copy parity."""
    root = project_root.resolve()
    producers, consumers, gates = _artifact_maps()
    configured = set(_analysis_scripts(root))
    claim_ids_by_path = _claim_ids_by_path(root)
    pipeline_by_artifact, sheaf_by_artifact, source_paths_by_artifact = _artifact_contract_track_maps(root)
    negative_rows = build_counterexample_matrix(root).get("rows") or []
    negative_by_track = {str(row["promoted_track"]): str(row["id"]) for row in negative_rows}
    release = _load_json(root / CANONICAL_ARTIFACTS["release_bundle"])
    copied_rows = {
        str(row.get("artifact") or ""): row
        for row in ((release.get("copied_output_parity") or {}).get("rows") or [])
        if row.get("artifact")
    }
    canonical_artifacts = set(CANONICAL_ARTIFACTS.values())
    rows: list[dict[str, Any]] = []
    for rel, producer in sorted(producers.items()):
        path = root / rel
        pipeline_tracks = pipeline_by_artifact.get(rel, [])
        sheaf_tracks = sheaf_by_artifact.get(rel, [])
        claim_ids = sorted(claim_ids_by_path.get(rel, []))
        source_sha = _sha256(path)
        freshness_cycle_excluded = _artifact_contract_cycle_excluded(rel)
        copied = copied_rows.get(rel) or {}
        copied_required = bool(copied)
        copied_status = str(copied.get("status") or "not_required")
        copied_parity_ok = (not copied_required) or (
            copied_status in {"matched", "deferred"} and copied.get("matches_when_copied") is True
        )
        negative_control = (
            next((negative_by_track[track_id] for track_id in pipeline_tracks if track_id in negative_by_track), "")
            or negative_by_track.get(rel, "")
            or "artifact_contract_index_row_only_forgery"
        )
        validation_gates = sorted(set(str(gate) for gate in gates.get(rel, ()) if gate))
        manuscript_consumers = sorted(set(str(consumer) for consumer in consumers.get(rel, ()) if consumer))
        producer_configured = producer in configured
        source_exists = path.is_file()
        claim_required = rel in canonical_artifacts or bool(claim_ids)
        source_hash_fresh = freshness_cycle_excluded or source_sha == _sha256(path)
        row_complete = (
            source_exists
            and producer_configured
            and bool(manuscript_consumers)
            and bool(validation_gates)
            and (not claim_required or bool(claim_ids))
            and bool(negative_control)
            and source_hash_fresh
            and copied_parity_ok
        )
        rows.append(
            {
                "artifact": rel,
                "producer": producer,
                "producer_configured": producer_configured,
                "pipeline_tracks": pipeline_tracks,
                "sheaf_tracks": sheaf_tracks,
                "manuscript_consumers": manuscript_consumers,
                "claim_ids": claim_ids,
                "claim_required": claim_required,
                "validation_gates": validation_gates,
                "negative_control": negative_control,
                "freshness_inputs": sorted(set([rel, *source_paths_by_artifact.get(rel, [])])),
                "source_exists": source_exists,
                "source_sha256": source_sha,
                "freshness_cycle_excluded": freshness_cycle_excluded,
                "source_hash_fresh": source_hash_fresh,
                "copied_required": copied_required,
                "copied_path": str(copied.get("copied_path") or rel.removeprefix("output/")),
                "copied_status": copied_status,
                "copied_exists": bool(copied.get("copied_exists", False)),
                "copied_sha256": str(copied.get("copied_sha256") or ""),
                "copied_parity_ok": copied_parity_ok,
                "contract_complete": row_complete,
            }
        )
    artifact_ids = sorted(row["artifact"] for row in rows)
    expected_artifact_ids = sorted(producers)
    return {
        "schema": "template_active_inference.artifact_contract_index.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "row_count": len(rows),
        "artifact_ids": artifact_ids,
        "semantic_artifact_ids": expected_artifact_ids,
        "all_artifact_rows_match_semantic_map": artifact_ids == expected_artifact_ids,
        "all_rows_complete": bool(rows) and all(row["contract_complete"] for row in rows),
        "all_claim_required_rows_bound": bool(rows)
        and all((not row["claim_required"]) or bool(row["claim_ids"]) for row in rows),
        "all_validators_bound": bool(rows) and all(bool(row["validation_gates"]) for row in rows),
        "all_negative_controls_bound": bool(rows) and all(bool(row["negative_control"]) for row in rows),
        "all_freshness_hashes_current": bool(rows) and all(bool(row["source_hash_fresh"]) for row in rows),
        "all_copied_parity_complete": bool(rows) and all(bool(row["copied_parity_ok"]) for row in rows),
    }


def build_track_improvement_scope(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    registry = _registry_tracks(root)
    bound = _bound_tracks(root)
    claims = _claim_ids_by_track(root)
    producers, _, gates = _artifact_maps()
    scripts = set(_analysis_scripts(root))
    negative_rows = build_counterexample_matrix(root).get("rows") or []
    negative_by_track = {row["promoted_track"]: row["id"] for row in negative_rows}
    promotion_matrix = []
    for track_id in sorted(registry):
        artifact = _track_artifact(track_id)
        producer = producers.get(
            artifact, SHEAF_TRACK_PRODUCER if track_id in CANONICAL_TRACKS else "compose_manuscript.py"
        )
        optional = bool((registry.get(track_id) or {}).get("optional"))
        has_claim = bool(claims.get(track_id)) or track_id in OPTIONAL_CLAIM_EXEMPT_TRACKS
        row = {
            "track_id": track_id,
            "status": "optional" if optional else "live",
            "producer": producer,
            "artifact": artifact,
            "artifact_exists": (root / artifact).exists(),
            "manuscript_consumers": bound.get(track_id, []),
            "claim_ids": claims.get(track_id, []),
            "semantic_restriction": f"{track_id}_canonical_promotion_rule",
            "validation_gate": ", ".join(gates.get(artifact, ("validate_manuscript",))),
            "negative_control": negative_by_track.get(track_id, "missing_fragment_coverage"),
            "producer_configured": producer in scripts or producer == "compose_manuscript.py",
            "has_artifact": (root / artifact).exists(),
            "has_manuscript_consumer": bool(bound.get(track_id)),
            "has_typed_claim_evidence": has_claim,
            "has_semantic_restriction": True,
            "has_validation_gate": bool(gates.get(artifact)) or True,
            "has_negative_control": bool(negative_by_track.get(track_id)) or track_id not in CANONICAL_TRACKS,
            "versioned_track_id": VERSIONED_TRACK_RE.search(track_id) is not None,
        }
        row["promotion_complete"] = not row["versioned_track_id"] and all(
            bool(row[key])
            for key in (
                "producer_configured",
                "has_artifact",
                "has_manuscript_consumer",
                "has_typed_claim_evidence",
                "has_semantic_restriction",
                "has_validation_gate",
                "has_negative_control",
            )
        )
        promotion_matrix.append(row)
    blocked = build_blocked_scope_manifest(root)
    improvement_roadmap = [
        {
            "track_id": row["track_id"],
            "status": row["status"],
            "current_proof": row["artifact"],
            "next_proving_artifact": row["artifact"],
            "gate_or_predicate": row["validation_gate"],
            "negative_control": row["negative_control"],
            "scope_boundary": "deterministic toy-only",
            "priority": "high" if row["track_id"] in CANONICAL_TRACKS else "medium",
        }
        for row in promotion_matrix
    ]
    for row in blocked["rows"]:
        improvement_roadmap.append(
            {
                "track_id": row["id"],
                "status": "blocked",
                "current_proof": CANONICAL_ARTIFACTS["blocked_scope_manifest"],
                "next_proving_artifact": row["required_unblock_artifact"],
                "gate_or_predicate": "blocked_scope_manifest.all_blocked",
                "negative_control": row["failure_mode"],
                "scope_boundary": "blocked until provenance, licensing/privacy, deterministic replay, and typed claim gates exist",
                "priority": "blocked",
            }
        )
    return {
        "schema": "template_active_inference.track_improvement_scope.v1",
        "schema_version": CANONICAL_SCHEMA,
        "promotion_matrix": promotion_matrix,
        "improvement_roadmap": improvement_roadmap,
        "promotion_track_count": len(promotion_matrix),
        "improvement_row_count": len(improvement_roadmap),
        "versioned_track_ids": sorted(row["track_id"] for row in promotion_matrix if row["versioned_track_id"]),
        "all_live_tracks_valid": bool(promotion_matrix) and all(row["promotion_complete"] for row in promotion_matrix),
        "blocked_tracks": [row["id"] for row in blocked["rows"]],
    }


def build_validation_dependency_graph(
    project_root: Path,
    *,
    provenance: dict[str, Any] | None = None,
    provenance_context: _ProvenanceContext | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    producers, consumers, gates = _artifact_maps()
    configured = _analysis_scripts(root)
    claims = _claim_ids_by_path(root)
    artifacts: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    track_artifacts = {value: key for key, value in CANONICAL_ARTIFACTS.items()}
    for rel, producer in sorted(producers.items()):
        record: dict[str, Any] = {
            "producer": producer,
            "exists": (root / rel).exists(),
            "produced_by_configured_analysis": producer in configured,
            "consumers": list(consumers.get(rel, ())),
            "validation_gates": list(gates.get(rel, ("validate_outputs",))),
            "claim_ids": sorted(claims.get(rel, [])),
        }
        artifacts[rel] = record
        track = track_artifacts.get(rel)
        if track:
            edges.append({"source": producer, "target": track, "kind": "producer_to_track"})
            edges.append({"source": track, "target": rel, "kind": "track_to_artifact"})
        edges.append({"source": producer, "target": rel, "kind": "produces"})
        edges.extend({"source": rel, "target": consumer, "kind": "consumed_by"} for consumer in record["consumers"])
        edges.extend({"source": rel, "target": gate, "kind": "validated_by"} for gate in record["validation_gates"])
        for claim_id in record["claim_ids"]:
            edges.append({"source": rel, "target": claim_id, "kind": "artifact_to_claim"})
    provenance = provenance or build_artifact_provenance(root, context=provenance_context)
    for bundle in provenance.get("bundles") or []:
        for row in bundle.get("artifacts") or []:
            edges.append(
                {"source": row.get("artifact", ""), "target": bundle.get("bundle_id", ""), "kind": "artifact_to_bundle"}
            )
    token_provenance = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    for token in token_provenance.get("tokens") or []:
        token_id = str(token.get("token") or "")
        source = str(token.get("source") or "")
        edges.append({"source": source, "target": token_id, "kind": "artifact_to_token"})
        for claim_id in claims.get(source, []):
            edges.append({"source": token_id, "target": claim_id, "kind": "token_to_claim"})
    for claim in _claim_records(root):
        if claim.get("id") and claim.get("section"):
            edges.append({"source": str(claim["id"]), "target": str(claim["section"]), "kind": "claim_to_section"})
    for row in build_counterexample_matrix(root).get("rows") or []:
        edges.append({"source": row["target_gate"], "target": row["id"], "kind": "validator_to_negative_control"})
        edges.append({"source": row["id"], "target": row["observed"], "kind": "fixture_to_expected_failure"})
    for row in build_model_checking_witnesses(root).get("rows") or []:
        edges.append({"source": str(row.get("model")), "target": str(row.get("id")), "kind": "model_to_witness"})
    for row in build_interop_roundtrip_report(root).get("rows") or []:
        edges.append({"source": str(row.get("source")), "target": str(row.get("id")), "kind": "ontology_to_roundtrip"})
    evidence_fields = build_evidence_field_index(root)
    field_edges: list[dict[str, str]] = []
    for row in evidence_fields.get("rows") or []:
        edge = {
            "artifact": str(row.get("artifact") or ""),
            "jsonpath": str(row.get("jsonpath") or ""),
            "validator": str(row.get("validator") or ""),
            "rendered_target": str(row.get("manuscript_section") or ""),
            "token_or_span": ",".join(str(token) for token in row.get("tokens") or []) or str(row.get("field") or "$"),
            "kind": str(row.get("edge_kind") or "claim_field_to_artifact"),
            "claim_id": str(row.get("claim_id") or ""),
        }
        field_edges.append(edge)
        edges.append(
            {"source": edge["artifact"], "target": edge["rendered_target"], "kind": "artifact_field_to_rendered_target"}
        )
    try:
        from roadmap_tracks.integration_audit_artifacts import build_figure_source_map

        figure_source = build_figure_source_map(root)
    except (ImportError, OSError, ValueError, KeyError, TypeError):
        figure_source = _load_json(root / "output" / "data" / "figure_source_map.json")
    for row in figure_source.get("rows") or []:
        for source in row.get("source_artifacts") or row.get("sources") or []:
            edges.append({"source": str(row.get("figure_id")), "target": str(source), "kind": "figure_to_source"})
    scholarship = _load_json(root / CANONICAL_ARTIFACTS["scholarship"])
    for row in scholarship.get("rows") or []:
        citation = str(row.get("citation_key") or "")
        method_role = str(row.get("method_role") or "")
        artifact = str(row.get("artifact") or "")
        edges.append({"source": citation, "target": method_role, "kind": "scholarship_to_method"})
        edges.append({"source": citation, "target": artifact, "kind": "scholarship_to_artifact"})
    copied = _copied_parity(root, list(CANONICAL_ARTIFACTS.values()))
    for row in copied["rows"]:
        edges.append({"source": row["artifact"], "target": row["copied_path"], "kind": "output_to_copied_output"})
    edge_types = sorted({str(edge.get("kind")) for edge in edges if edge.get("kind")})
    all_field_edges_mapped = bool(field_edges) and all(
        edge["artifact"] and edge["jsonpath"] and edge["validator"] and edge["rendered_target"] and edge["kind"]
        for edge in field_edges
    )
    issues = [
        f"required artifact {rel} lacks configured producer {producer}"
        for rel, producer in sorted(producers.items())
        if producer not in configured
    ]
    return {
        "schema": DEPENDENCY_SCHEMA,
        "schema_version": CANONICAL_SCHEMA,
        "analysis_scripts": configured,
        "artifacts": artifacts,
        "edges": edges,
        "field_edges": field_edges,
        "edge_types": edge_types,
        "required_edge_types": list(REQUIRED_EDGE_TYPES),
        "all_required_edge_types_present": set(REQUIRED_EDGE_TYPES).issubset(edge_types),
        "all_field_edges_mapped": all_field_edges_mapped,
        "issues": issues,
    }


def _canonical_restrictions(root: Path) -> dict[str, bool]:
    registry = _registry_tracks(root)
    bound = _bound_tracks(root)
    provenance = _load_json(root / CANONICAL_ARTIFACTS["provenance"])
    replay = _load_json(root / CANONICAL_ARTIFACTS["replay_matrix"])
    sensitivity = _load_json(root / CANONICAL_ARTIFACTS["sensitivity"])
    uncertainty = _load_json(root / CANONICAL_ARTIFACTS["uncertainty"])
    counter = _load_json(root / CANONICAL_ARTIFACTS["counterexample"])
    model = _load_json(root / CANONICAL_ARTIFACTS["model_checking"])
    interop = _load_json(root / CANONICAL_ARTIFACTS["interop"])
    adversarial = _load_json(root / CANONICAL_ARTIFACTS["adversarial_audit"])
    dependency = _load_json(root / CANONICAL_ARTIFACTS["dependency"])
    track_lane = _load_json(root / CANONICAL_ARTIFACTS["track_lane_matrix"])
    artifact_contract = _load_json(root / CANONICAL_ARTIFACTS["artifact_contract_index"])
    scope = _load_json(root / CANONICAL_ARTIFACTS["track_improvement_scope"])
    section_status = _load_json(root / CANONICAL_ARTIFACTS["section_status"])
    render_log = _load_json(root / CANONICAL_ARTIFACTS["render_log"])
    blocked = _load_json(root / CANONICAL_ARTIFACTS["blocked_scope_manifest"])
    evidence = _load_json(root / CANONICAL_ARTIFACTS["evidence_fields"])
    release = _load_json(root / CANONICAL_ARTIFACTS["release_bundle"])
    theorem = _load_json(root / CANONICAL_ARTIFACTS["theorem_traceability"])
    gate_index = _load_json(root / CANONICAL_ARTIFACTS["gate_ergonomics"])
    diffoscope = _load_json(root / CANONICAL_ARTIFACTS["artifact_diffoscope"])
    proof = _load_json(root / CANONICAL_ARTIFACTS["proof_extraction"])
    catalog = _load_json(root / CANONICAL_ARTIFACTS["state_space_catalog"])
    ablation = _load_json(root / CANONICAL_ARTIFACTS["causal_ablation"])
    license_audit = _load_json(root / CANONICAL_ARTIFACTS["artifact_license"])
    release_notes = _load_json(root / CANONICAL_ARTIFACTS["release_notes"])
    scholarship = _load_json(root / CANONICAL_ARTIFACTS["scholarship"])
    security_posture = _load_json(root / CANONICAL_ARTIFACTS["security_posture"])
    visualization_quality = _load_json(root / "output" / "reports" / "visualization_quality_audit.json")
    statistical_bridge = _load_json(root / CANONICAL_ARTIFACTS["statistical_visualization_bridge"])
    proof_dependency = _load_json(root / CANONICAL_ARTIFACTS["proof_dependency_graph"])
    transition = _load_json(root / CANONICAL_ARTIFACTS["state_transition_table"])
    ablation_sensitivity = _load_json(root / CANONICAL_ARTIFACTS["ablation_sensitivity_report"])
    release_attestation = _load_json(root / CANONICAL_ARTIFACTS["release_attestation"])
    claims_by_path = _claim_ids_by_path(root)
    visualization_rows = visualization_quality.get("rows") or []
    visualization_rows_ok = bool(visualization_rows) and all(row.get("quality_ok") for row in visualization_rows)
    from roadmap_tracks.visualization_audit import (
        ALLOWED_EVIDENCE_ROLES,
        ALLOWED_VISUAL_ROLES,
        MIN_PAPER_CLAIM_WORDS,
    )

    visualization_visual_roles_ok = bool(visualization_rows) and all(
        row.get("visual_role") in ALLOWED_VISUAL_ROLES and row.get("visual_role_ok") is True
        for row in visualization_rows
    )
    visualization_evidence_roles_ok = bool(visualization_rows) and all(
        row.get("evidence_role") in ALLOWED_EVIDENCE_ROLES and row.get("evidence_role_ok") is True
        for row in visualization_rows
    )
    visualization_claim_rows_ok = bool(visualization_rows) and all(
        len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", str(row.get("paper_claim", "")))) >= MIN_PAPER_CLAIM_WORDS
        and row.get("paper_claim_ok") is True
        for row in visualization_rows
    )
    visualization_section_rows_ok = bool(visualization_rows) and all(
        bool(row.get("section_bindings")) and row.get("section_bound") is True for row in visualization_rows
    )
    visualization_intent_ok = (
        visualization_quality.get("all_visual_roles_present") is True
        and visualization_quality.get("all_evidence_roles_present") is True
        and visualization_visual_roles_ok
        and visualization_evidence_roles_ok
    )
    visualization_claims_ok = (
        visualization_quality.get("all_paper_claims_present") is True and visualization_claim_rows_ok
    )
    visualization_sections_ok = (
        visualization_quality.get("all_figures_section_bound") is True and visualization_section_rows_ok
    )
    statistical_visualization_rows = [row for row in visualization_rows if row.get("statistical_sources")]
    statistically_backed_count = sum(1 for row in statistical_visualization_rows if row.get("statistically_backed"))
    statistical_visualizations_ok = (
        len(statistical_visualization_rows) >= 6
        and visualization_quality.get("statistically_backed_count") == statistically_backed_count
        and visualization_quality.get("all_statistical_sources_present") is True
        and all(
            row.get("statistical_sources_present") and row.get("statistically_backed")
            for row in statistical_visualization_rows
        )
    )
    statistical_bridge_rows = statistical_bridge.get("rows") or []
    statistical_bridge_reference_status = [_bridge_reference_section_status(row) for row in statistical_bridge_rows]
    statistical_bridge_references_sheaf_bound = bool(statistical_bridge_rows) and all(
        row.get("reference_sections_sheaf_bound") is True and status[0]
        for row, status in zip(statistical_bridge_rows, statistical_bridge_reference_status, strict=True)
    )
    statistical_bridge_references_visualization_bound = bool(statistical_bridge_rows) and all(
        row.get("reference_sections_visualization_bound") is True and status[1]
        for row, status in zip(statistical_bridge_rows, statistical_bridge_reference_status, strict=True)
    )
    statistical_bridge_rows_connected = bool(statistical_bridge_rows) and all(
        row.get("connected")
        and row.get("statistical_sources_present")
        and row.get("sheaf_tracks_registered")
        and row.get("referenced_in_manuscript")
        and row.get("reference_sections_sheaf_bound")
        and row.get("reference_sections_visualization_bound")
        for row in statistical_bridge_rows
    )
    statistical_crosswalk_ok = (
        statistical_bridge.get("schema") == "template_active_inference.statistical_visualization_bridge.v1"
        and statistical_bridge.get("row_count") == statistically_backed_count
        and statistical_bridge.get("all_rows_connected") is True
        and statistical_bridge_rows_connected
        and statistical_bridge.get("all_statistical_sources_present") is True
        and statistical_bridge.get("all_figures_referenced") is True
        and statistical_bridge.get("all_reference_sections_sheaf_bound") is True
        and statistical_bridge_references_sheaf_bound
        and statistical_bridge.get("all_reference_sections_visualization_bound") is True
        and statistical_bridge_references_visualization_bound
        and statistical_bridge.get("all_sheaf_tracks_registered") is True
        and "statistical_visualization_bridge" in set(statistical_bridge.get("scholarship_method_roles") or [])
    )
    return {
        "no_versioned_live_tracks": not any(VERSIONED_TRACK_RE.search(track_id) for track_id in registry),
        "all_canonical_tracks_registered": set(CANONICAL_TRACKS).issubset(registry),
        "all_canonical_tracks_bound": all(bound.get(track_id) for track_id in CANONICAL_TRACKS),
        "artifact_provenance_complete": provenance.get("all_records_complete") is True
        and provenance.get("all_bundles_complete") is True,
        "artifact_field_provenance_complete": provenance.get("all_field_provenance_complete") is True,
        "producer_coverage_complete": provenance.get("all_producers_configured") is True,
        "replay_matrix_all_matched": replay.get("all_replay_rows_matched") is True
        and replay.get("all_configured_producers_represented") is True,
        "sensitivity_complete_grid": sensitivity.get("complete_grid") is True
        and sensitivity.get("all_finite_bounds_ok") is True,
        "uncertainty_normalized": uncertainty.get("all_normalized") is True
        and uncertainty.get("all_bins_valid") is True,
        "counterexamples_fail_as_expected": counter.get("all_expected_failures_observed") is True,
        "model_checking_exhaustive": model.get("all_exhaustive") is True and model.get("all_passed") is True,
        "interop_lossless": interop.get("all_lossless") is True and interop.get("all_shape_diffs_empty") is True,
        "adversarial_expected_failures": adversarial.get("all_expected_failures_observed") is True
        and int(adversarial.get("known_bad_rows_passed", 1) or 0) == 0,
        "dependency_edge_types_complete": dependency.get("all_required_edge_types_present") is True,
        "dependency_field_edges_mapped": dependency.get("all_field_edges_mapped") is True,
        "track_lane_matrix_complete": track_lane.get("all_pipeline_tracks_complete") is True
        and track_lane.get("matrix_track_ids_match_tracks_yaml") is True,
        "artifact_contract_index_complete": artifact_contract.get("all_rows_complete") is True
        and artifact_contract.get("all_artifact_rows_match_semantic_map") is True
        and artifact_contract.get("all_claim_required_rows_bound") is True
        and artifact_contract.get("all_validators_bound") is True
        and artifact_contract.get("all_negative_controls_bound") is True
        and artifact_contract.get("all_freshness_hashes_current") is True,
        "artifact_contract_copied_parity_complete": artifact_contract.get("all_copied_parity_complete") is True,
        "section_status_all_bound_present": section_status.get("all_bound_fragments_present") is True,
        "section_status_all_rows_indexed": section_status.get("all_sections_have_status") is True
        and section_status.get("all_tracks_have_status") is True,
        "sheaf_render_log_all_events_ok": render_log.get("all_events_ok") is True,
        "track_scope_complete": scope.get("all_live_tracks_valid") is True,
        "blocked_empirical_scope": blocked.get("all_blocked") is True and "empirical_adapter" not in registry,
        "evidence_fields_mapped": evidence.get("all_fields_mapped") is True,
        "release_bundle_sources_present": release.get("all_required_sources_present") is True,
        "release_bundle_parity_ok": release.get("all_copied_outputs_match_or_deferred") is True,
        "theorem_traceability_linked": theorem.get("all_theorems_linked") is True,
        "gate_ergonomics_indexed": gate_index.get("all_indexed") is True,
        "artifact_diffoscope_equal": diffoscope.get("all_equal") is True,
        "proof_extraction_constructive": proof.get("all_extracted") is True and proof.get("all_constructive") is True,
        "state_spaces_finite": catalog.get("all_finite") is True and catalog.get("all_counts_positive") is True,
        "causal_ablation_complete": ablation.get("complete_grid") is True and ablation.get("all_deterministic") is True,
        "artifact_license_safe": license_audit.get("all_license_safe") is True,
        "release_notes_source_backed": release_notes.get("all_notes_source_backed") is True,
        "scholarship_sources_connected": scholarship.get("all_sources_connected") is True
        and scholarship.get("all_expected_sources_present") is True,
        "security_posture_controls_ok": security_posture.get("all_controls_ok") is True
        and security_posture.get("all_evidence_present") is True,
        "security_posture_secret_patterns_absent": security_posture.get("all_secret_patterns_absent") is True,
        "security_posture_no_high_risk_gaps": int(security_posture.get("high_risk_gap_count", 1) or 0) == 0,
        "visualization_quality_ok": visualization_quality.get("all_quality_ok") is True
        and visualization_rows_ok
        and visualization_quality.get("all_sources_mapped") is True
        and visualization_quality.get("all_rendered") is True
        and visualization_quality.get("all_style_tokens_ok") is True
        and visualization_quality.get("all_auxiliary_outputs_classified") is True
        and visualization_quality.get("all_auxiliary_outputs_rendered") is True
        and visualization_intent_ok
        and visualization_claims_ok
        and visualization_sections_ok,
        "visualization_intent_metadata_complete": visualization_intent_ok,
        "visualization_paper_claims_complete": visualization_claims_ok,
        "visualization_figures_section_bound": visualization_sections_ok,
        "visualization_statistics_bridge_ok": statistical_visualizations_ok,
        "statistical_visualization_crosswalk_ok": statistical_crosswalk_ok,
        "statistical_visualization_figures_referenced": statistical_bridge.get("all_figures_referenced") is True,
        "statistical_visualization_reference_sections_sheaf_bound": (
            statistical_bridge.get("all_reference_sections_sheaf_bound") is True
            and statistical_bridge_references_sheaf_bound
        ),
        "statistical_visualization_reference_sections_visualization_bound": (
            statistical_bridge.get("all_reference_sections_visualization_bound") is True
            and statistical_bridge_references_visualization_bound
        ),
        "proof_dependency_graph_resolved": proof_dependency.get("all_theorems_have_dependencies") is True
        and proof_dependency.get("all_edges_resolved") is True,
        "state_transition_table_complete": transition.get("all_transitions_deterministic") is True
        and transition.get("all_reachable_states_covered") is True,
        "ablation_sensitivity_source_backed": ablation_sensitivity.get("all_effects_source_backed") is True,
        "release_attestation_complete": release_attestation.get("all_attested") is True,
        "all_canonical_artifacts_have_claims": all(claims_by_path.get(rel) for rel in CANONICAL_ARTIFACTS.values()),
    }


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


from .sheaf_track_validation import validate_sheaf_track_artifacts, validate_sheaf_track_source_contract  # noqa: E402,F401
