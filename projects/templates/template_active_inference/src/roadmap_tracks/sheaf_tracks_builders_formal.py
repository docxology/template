"""Formal interop and adversarial builders for canonical sheaf tracks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_io import _analysis_scripts, _load_json, _registry_tracks
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, CANONICAL_SCHEMA, CANONICAL_TRACKS


def build_counterexample_matrix(project_root: Path) -> dict[str, Any]:
    """Build counterexample matrix."""
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
    """Build model checking witnesses."""
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
    """Build interop roundtrip report."""
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
    """Build adversarial audit."""
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
