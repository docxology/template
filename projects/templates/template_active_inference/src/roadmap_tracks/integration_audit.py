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

from .integration_audit_artifacts import (
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
    "build_validation_gate_index",
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
    if stale.get("all_fresh") is not True:
        issues.append("stale_artifact_report.json records stale artifacts")
    for row in stale.get("rows") or []:
        path = root / str(row.get("artifact", ""))
        if not path.is_file():
            issues.append(f"stale_artifact_report.json missing artifact {row.get('artifact')}")
            continue
        if row.get("sha256") != _sha256(path):
            issues.append(f"stale_artifact_report.json hash mismatch for {row.get('artifact')}")
    tokens = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    tokens_derived = bool(tokens.get("tokens")) and all(row.get("mapped") for row in tokens.get("tokens") or [])
    if tokens.get("all_tokens_mapped") is not True or tokens.get("all_tokens_mapped") != tokens_derived:
        issues.append("manuscript_token_provenance.json has unmapped tokens")
    figures = _load_json(root / "output" / "data" / "figure_source_map.json")
    figures_derived = bool(figures.get("rows")) and all(row.get("mapped") for row in figures.get("rows") or [])
    if figures.get("all_figures_mapped") is not True or figures.get("all_figures_mapped") != figures_derived:
        issues.append("figure_source_map.json has unmapped figures")
    claim_audit = _load_json(root / "output" / "reports" / "claim_evidence_audit.json")
    claims_derived = bool(claim_audit.get("rows")) and all(
        row.get("has_evidence") and row.get("has_tracks") for row in claim_audit.get("rows") or []
    )
    if claim_audit.get("all_claims_typed") is not True or claim_audit.get("all_claims_typed") != claims_derived:
        issues.append("claim_evidence_audit.json has untyped claims")
    scope = _load_json(root / "output" / "reports" / "scope_boundary_audit.json")
    if scope.get("all_current_claims_toy") is not True:
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
    tables = _load_json(root / "output" / "data" / "manuscript_evidence_tables.json")
    tables_derived = bool(tables.get("tables")) and all(
        int(table.get("row_count", 0) or 0) > 0 and table.get("source") for table in tables.get("tables") or []
    )
    if tables.get("all_source_backed") is not True or tables.get("all_source_backed") != tables_derived:
        issues.append("manuscript_evidence_tables.json has unbacked tables")
    staleness = _load_json(root / "output" / "reports" / "manuscript_staleness_report.json")
    if staleness.get("schema") != "template_active_inference.manuscript_staleness_report.v1":
        issues.append("manuscript_staleness_report.json schema mismatch")
    if staleness.get("all_fresh") is not True:
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
    if symbols.get("all_consistent") is not True or symbols.get("all_consistent") != symbols_derived:
        issues.append("cross_track_symbol_table.json has inconsistent symbols")
    gate_index = _load_json(root / "output" / "data" / "validation_gate_index.json")
    gates_derived = bool(gate_index.get("rows")) and all(row.get("indexed") for row in gate_index.get("rows") or [])
    if gate_index.get("all_indexed") is not True or gate_index.get("all_indexed") != gates_derived:
        issues.append("validation_gate_index.json has unindexed gates")
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    if diffoscope.get("schema") != "template_active_inference.artifact_diffoscope.v1":
        issues.append("artifact_diffoscope.json schema mismatch")
    if diffoscope.get("all_equal") is not True:
        issues.append("artifact_diffoscope.json records artifact drift")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    if license_audit.get("schema") != "template_active_inference.artifact_license_audit.v1":
        issues.append("artifact_license_audit.json schema mismatch")
    if license_audit.get("all_license_safe") is not True:
        issues.append("artifact_license_audit.json records unsafe artifacts")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    if release_notes.get("schema") != "template_active_inference.release_notes_evidence.v1":
        issues.append("release_notes_evidence.json schema mismatch")
    if release_notes.get("all_notes_source_backed") is not True:
        issues.append("release_notes_evidence.json has unsupported notes")
    return issues
