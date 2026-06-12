"""Integration-audit artifacts for canonical sheaf-track gates.

This module is the public facade for the integration-audit surface. The builders
live in two cohesive sibling modules to stay under the line-count gate:

* :mod:`roadmap_tracks.integration_audit_builders` — dependency graph, manuscript
  provenance, claims, and gate-index builders plus shared helpers.
* :mod:`roadmap_tracks.integration_audit_artifacts` — artifact diffoscope, license,
  release-notes, figure, scope-boundary, evidence-table, and semantic-snapshot builders.

Every builder and helper is re-exported here, so existing
``from roadmap_tracks.integration_audit import X`` imports resolve unchanged.
"""

from __future__ import annotations

from pathlib import Path

from roadmap_tracks.row_aggregates import all_rows

from .figure_provenance import _figure_sources_mapped
from .integration_audit_artifacts import (
    ALLOWED_CLAIM_LANES,
    REQUIRED_SCOPE_CATEGORIES,
    build_adversarial_audit,
    build_artifact_diffoscope,
    build_artifact_license_audit,
    build_figure_hash_manifest,
    build_figure_source_map,
    build_integration_semantic_snapshot,
    build_manuscript_evidence_tables,
    build_release_notes_evidence,
    build_scope_boundary_audit,
)
from .integration_audit_builders import (
    LATE_HYDRATION_PRODUCER,
    SELF_PRODUCER,
    SHEAF_TRACK_PRODUCER,
    TOKEN_MATCH_RE,
    TOKEN_RE,
    _analysis_scripts,
    _expected_token_value,
    _load_json,
    _sha256,
    _write_json,
    build_claim_evidence_audit,
    build_cross_track_symbol_table,
    build_integration_dependency_graph,
    build_manuscript_staleness_report,
    build_manuscript_token_provenance,
    build_producer_completeness,
    build_stale_artifact_report,
    build_validation_gate_index,
)
from .visualization_audit import (
    build_statistical_visualization_bridge,
    build_visualization_quality_audit,
    validate_statistical_visualization_bridge,
    validate_visualization_quality_audit,
)

__all__ = [
    "LATE_HYDRATION_PRODUCER",
    "SELF_PRODUCER",
    "SHEAF_TRACK_PRODUCER",
    "TOKEN_MATCH_RE",
    "TOKEN_RE",
    "_analysis_scripts",
    "_expected_token_value",
    "_load_json",
    "_sha256",
    "_write_json",
    "build_adversarial_audit",
    "build_artifact_diffoscope",
    "build_artifact_license_audit",
    "build_claim_evidence_audit",
    "build_cross_track_symbol_table",
    "build_figure_hash_manifest",
    "build_figure_source_map",
    "build_integration_dependency_graph",
    "build_integration_semantic_snapshot",
    "build_manuscript_evidence_tables",
    "build_manuscript_staleness_report",
    "build_manuscript_token_provenance",
    "build_producer_completeness",
    "build_release_notes_evidence",
    "build_scope_boundary_audit",
    "build_stale_artifact_report",
    "build_statistical_visualization_bridge",
    "build_validation_gate_index",
    "build_visualization_quality_audit",
    "validate_statistical_visualization_bridge",
    "validate_visualization_quality_audit",
    "write_integration_audit_artifacts",
    "write_manuscript_staleness_report",
    "validate_integration_audit_artifacts",
]


def write_manuscript_staleness_report(project_root: Path) -> Path:
    """Write the hydrated-manuscript staleness report."""
    root = project_root.resolve()
    return _write_json(
        root / "output" / "reports" / "manuscript_staleness_report.json",
        build_manuscript_staleness_report(root),
    )


def write_integration_audit_artifacts(project_root: Path) -> dict[str, Path]:
    root = project_root.resolve()
    paths = {
        "producer_completeness": _write_json(
            root / "output" / "reports" / "producer_completeness.json",
            build_producer_completeness(root),
        ),
        "stale_artifacts": _write_json(
            root / "output" / "reports" / "stale_artifact_report.json",
            build_stale_artifact_report(root),
        ),
        "cross_track_symbols": _write_json(
            root / "output" / "data" / "cross_track_symbol_table.json",
            build_cross_track_symbol_table(root),
        ),
        "token_provenance": _write_json(
            root / "output" / "data" / "manuscript_token_provenance.json",
            build_manuscript_token_provenance(root),
        ),
        "claim_audit": _write_json(
            root / "output" / "reports" / "claim_evidence_audit.json",
            build_claim_evidence_audit(root),
        ),
        "gate_index": _write_json(
            root / "output" / "data" / "validation_gate_index.json",
            build_validation_gate_index(root),
        ),
        "figure_source_map": _write_json(
            root / "output" / "data" / "figure_source_map.json",
            build_figure_source_map(root),
        ),
        "figure_hash_manifest": _write_json(
            root / "output" / "reports" / "figure_hash_manifest.json",
            build_figure_hash_manifest(root),
        ),
        "visualization_quality": _write_json(
            root / "output" / "reports" / "visualization_quality_audit.json",
            build_visualization_quality_audit(root),
        ),
        "statistical_visualization_bridge": _write_json(
            root / "output" / "data" / "statistical_visualization_bridge.json",
            build_statistical_visualization_bridge(root),
        ),
        "scope_boundary": _write_json(
            root / "output" / "reports" / "scope_boundary_audit.json",
            build_scope_boundary_audit(root),
        ),
        "adversarial_audit": _write_json(
            root / "output" / "reports" / "adversarial_audit.json",
            build_adversarial_audit(root),
        ),
        "manuscript_staleness": _write_json(
            root / "output" / "reports" / "manuscript_staleness_report.json",
            build_manuscript_staleness_report(root),
        ),
        "artifact_diffoscope": _write_json(
            root / "output" / "reports" / "artifact_diffoscope.json",
            build_artifact_diffoscope(root),
        ),
        "artifact_license": _write_json(
            root / "output" / "reports" / "artifact_license_audit.json",
            build_artifact_license_audit(root),
        ),
        "release_notes": _write_json(
            root / "output" / "reports" / "release_notes_evidence.json",
            build_release_notes_evidence(root),
        ),
        "manuscript_tables": _write_json(
            root / "output" / "data" / "manuscript_evidence_tables.json",
            build_manuscript_evidence_tables(root),
        ),
    }
    return paths


def validate_integration_audit_artifacts(project_root: Path) -> list[str]:
    root = project_root.resolve()
    issues: list[str] = []
    producer = _load_json(root / "output" / "reports" / "producer_completeness.json")
    producer_rows = producer.get("rows") or []
    producer_derived = bool(producer_rows) and all(row.get("exists") and row.get("configured") for row in producer_rows)
    if producer.get("all_complete") is not True or producer.get("all_complete") != producer_derived:
        # Re-derived from rows: a row showing a missing/unconfigured producer fails closed even
        # if the stored all_complete bit was left true.
        issues.append("producer_completeness.json is incomplete")
    stale = _load_json(root / "output" / "reports" / "stale_artifact_report.json")
    stale_fresh = all_rows(stale, lambda row: bool(row.get("fresh")))
    if stale.get("all_fresh") is not True or stale.get("all_fresh") != stale_fresh:
        issues.append("stale_artifact_report.json records stale artifacts")
    for row in stale.get("rows") or []:
        path = root / str(row.get("artifact", ""))
        if not path.is_file():
            issues.append(f"stale_artifact_report.json missing artifact {row.get('artifact')}")
            continue
        if row.get("sha256") != _sha256(path):
            issues.append(f"stale_artifact_report.json hash mismatch for {row.get('artifact')}")
    tokens = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    tokens_derived = bool(tokens.get("tokens")) and all(
        row.get("mapped") and row.get("source_jsonpath") and row.get("hydrated_value_present")
        for row in tokens.get("tokens") or []
    )
    if tokens.get("all_tokens_mapped") is not True or tokens.get("all_tokens_mapped") != tokens_derived:
        issues.append("manuscript_token_provenance.json has unmapped tokens")
    figures = _load_json(root / "output" / "data" / "figure_source_map.json")
    figures_derived = all_rows(
        figures,
        lambda row: (
            row.get("mapped")
            # Re-derive `mapped` from the filesystem rather than trusting the
            # stored row field (PR#23 hardening: a forged mapped=true with a
            # nonexistent source path must fail).
            and _figure_sources_mapped(root, list(row.get("sources") or []))
            and row.get("source_artifact")
            and row.get("source_jsonpath")
            and row.get("renderer")
            and row.get("dimensions", {}).get("width", 0) > 0
            and row.get("dimensions", {}).get("height", 0) > 0
            and row.get("image_sha256")
            and row.get("axis_channel_mapping")
            and row.get("section_bindings")
            and row.get("claim_lanes")
            and set(str(lane) for lane in row.get("claim_lanes") or []).issubset(ALLOWED_CLAIM_LANES)
            and int(row.get("claim_lane_count", 0) or 0) == len(row.get("claim_lanes") or [])
            and row.get("pixel_provenance_ok") is True
        ),
    )
    if figures.get("all_figures_mapped") is not True or figures.get("all_figures_mapped") != figures_derived:
        issues.append("figure_source_map.json has unmapped figures")
    if (
        figures.get("all_figures_have_claim_lanes") is not True
        or figures.get("all_claim_lanes_valid") is not True
        or not figures_derived
    ):
        issues.append("figure_source_map.json has incomplete claim lanes")
    claim_audit = _load_json(root / "output" / "reports" / "claim_evidence_audit.json")
    claims_derived = bool(claim_audit.get("rows")) and all(
        row.get("has_evidence")
        and row.get("has_tracks")
        and row.get("substantive")
        and (row.get("predicate") or row.get("waiver"))
        and not row.get("failure_reason")
        for row in claim_audit.get("rows") or []
    )
    if claim_audit.get("all_claims_typed") is not True or claim_audit.get("all_claims_typed") != claims_derived:
        issues.append("claim_evidence_audit.json has untyped claims")
    scope = _load_json(root / "output" / "reports" / "scope_boundary_audit.json")
    scope_rows_ok = all_rows(
        scope,
        lambda row: (
            row.get("ok") is True
            and row.get("classification") in {"current", "future", "empirical"}
            and row.get("context") in {"toy_result", "future_extension", "blocked_language", "blocked_manifest"}
            and row.get("scope_category") in set(REQUIRED_SCOPE_CATEGORIES)
            and (
                (row.get("scope_category") == "current_toy" and row.get("current_result_toy_only") is True)
                or (row.get("scope_category") == "future_only" and row.get("non_live_context") is True)
                or (
                    str(row.get("scope_category") or "").startswith("blocked_")
                    and row.get("blocked_context") is True
                    and row.get("non_live_context") is True
                )
            )
        ),
    )
    required_categories = set(REQUIRED_SCOPE_CATEGORIES)
    present_categories = {str(row.get("scope_category")) for row in scope.get("rows") or []}
    if (
        scope.get("all_current_claims_toy") is not True
        or not scope_rows_ok
        or scope.get("all_required_scope_categories_present") is not True
        or not required_categories.issubset(present_categories)
        or scope.get("all_future_rows_non_live") is not True
        or scope.get("all_blocked_contexts_non_live") is not True
    ):
        issues.append("scope_boundary_audit.json records empirical scope leakage")
    adversarial = _load_json(root / "output" / "reports" / "adversarial_audit.json")
    if adversarial.get("all_expected_failures_documented") is not True:
        issues.append("adversarial_audit.json has undocumented expected failures")
    figure_hash = _load_json(root / "output" / "reports" / "figure_hash_manifest.json")
    figure_hash_derived = bool(figure_hash.get("rows")) and all(
        row.get("sha256") for row in figure_hash.get("rows") or []
    )
    if (
        figure_hash.get("all_hashes_present") is not True
        or figure_hash.get("all_hashes_present") != figure_hash_derived
    ):
        issues.append("figure_hash_manifest.json lacks hashes")
    issues.extend(validate_visualization_quality_audit(root))
    issues.extend(validate_statistical_visualization_bridge(root))
    tables = _load_json(root / "output" / "data" / "manuscript_evidence_tables.json")
    tables_derived = bool(tables.get("tables")) and all(
        int(table.get("row_count", 0) or 0) > 0 and table.get("source") for table in tables.get("tables") or []
    )
    if tables.get("all_source_backed") is not True or tables.get("all_source_backed") != tables_derived:
        issues.append("manuscript_evidence_tables.json has unbacked tables")
    staleness = _load_json(root / "output" / "reports" / "manuscript_staleness_report.json")
    if staleness.get("schema") != "template_active_inference.manuscript_staleness_report.v1":
        issues.append("manuscript_staleness_report.json schema mismatch")
    staleness_fresh = all_rows(staleness, lambda row: bool(row.get("fresh")))
    if staleness.get("all_fresh") is not True or staleness.get("all_fresh") != staleness_fresh:
        issues.append("manuscript_staleness_report.json records stale manuscript tokens")
    live_staleness = build_manuscript_staleness_report(root)
    saved_rows = [
        {key: row.get(key) for key in ("section", "token", "expected", "fresh")} for row in staleness.get("rows") or []
    ]
    live_rows = [
        {key: row.get(key) for key in ("section", "token", "expected", "fresh")}
        for row in live_staleness.get("rows") or []
    ]
    if staleness and saved_rows != live_rows:
        issues.append("manuscript_staleness_report.json is stale relative to live manuscript tokens")
    symbols = _load_json(root / "output" / "data" / "cross_track_symbol_table.json")
    symbols_derived = bool(symbols.get("rows")) and all(row.get("consistent") for row in symbols.get("rows") or [])
    required_symbol_kinds = {"gnn_variable", "lean_theorem", "manuscript_variable", "json_field", "figure_label"}
    if (
        symbols.get("all_consistent") is not True
        or symbols.get("all_consistent") != symbols_derived
        or not required_symbol_kinds.issubset(set(symbols.get("source_kinds") or []))
    ):
        issues.append("cross_track_symbol_table.json has inconsistent symbols")
    gate_index = _load_json(root / "output" / "data" / "validation_gate_index.json")
    gates_derived = all_rows(
        gate_index,
        lambda row: (
            row.get("indexed")
            and row.get("command")
            and row.get("required_inputs")
            and row.get("declared_outputs")
            and row.get("negative_control_id")
        ),
    )
    if gate_index.get("all_indexed") is not True or gate_index.get("all_indexed") != gates_derived:
        issues.append("validation_gate_index.json has unindexed gates")
    # PR#23 hardening: every aggregate below is re-derived from its rows so a
    # row-only forgery (rows contradict a True stored flag) cannot pass.
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    if diffoscope.get("schema") != "template_active_inference.artifact_diffoscope.v1":
        issues.append("artifact_diffoscope.json schema mismatch")
    diffoscope_equal = all_rows(diffoscope, lambda row: row.get("equal") is True)
    if diffoscope.get("all_equal") is not True or diffoscope.get("all_equal") != diffoscope_equal:
        issues.append("artifact_diffoscope.json records artifact drift")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    if license_audit.get("schema") != "template_active_inference.artifact_license_audit.v1":
        issues.append("artifact_license_audit.json schema mismatch")
    license_safe = all_rows(license_audit, lambda row: row.get("license_safe") is True)
    if license_audit.get("all_license_safe") is not True or license_audit.get("all_license_safe") != license_safe:
        issues.append("artifact_license_audit.json records unsafe artifacts")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    if release_notes.get("schema") != "template_active_inference.release_notes_evidence.v1":
        issues.append("release_notes_evidence.json schema mismatch")
    notes_backed = all_rows(release_notes, lambda row: bool(row.get("source")) and row.get("passed") is True)
    if (
        release_notes.get("all_notes_source_backed") is not True
        or release_notes.get("all_notes_source_backed") != notes_backed
    ):
        issues.append("release_notes_evidence.json has unsupported notes")
    return issues
