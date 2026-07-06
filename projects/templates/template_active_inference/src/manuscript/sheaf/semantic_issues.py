"""Semantic cross-track disagreement aggregation for the manuscript sheaf."""

from __future__ import annotations

from pathlib import Path

from manuscript.variables import generate_variables
from ontology.bindings import (
    BERNOULLI_EXPECTED_TERMS,
    BERNOULLI_SYMBOL_MAP,
    SI_EXPECTED_TERMS,
    SI_SYMBOL_MAP,
    validate_all_gnn_ontology,
)

from manuscript.sheaf.coverage import gray_cell_count, load_sheaf_coverage_context
from manuscript.sheaf.semantic_evidence import validate_configured_artifact_producers
from manuscript.sheaf.semantic_restrictions import (
    _animation_frame_count,
    _expected_symbol_gaps,
    _gnn_symbols,
    _graph_world_restrictions,
    _lean_status,
    _load_json,
    _policy_comparison_restrictions,
    _policy_posterior_restrictions,
    _runtime_diagnostics_restrictions,
    _section_ontology_symbols,
)


def semantic_gluing_issues(project_root: Path) -> list[str]:
    """Return semantic cross-track disagreements not covered by structural laws."""
    root = project_root.resolve()
    issues: list[str] = []

    ctx = load_sheaf_coverage_context(root)
    missing = gray_cell_count(ctx.matrix)
    if missing:
        issues.append(f"coverage matrix has {missing} missing bound fragment(s)")

    issues.extend(validate_all_gnn_ontology(root))
    issues.extend(
        _expected_symbol_gaps(
            label="bernoulli_toy",
            gnn_symbols=_gnn_symbols(root, "gnn/bernoulli_toy.gnn.md"),
            section_symbols=_section_ontology_symbols(
                root,
                "manuscript/sections/imrad/methods_analytical/ontology.yaml",
            ),
            symbol_map=BERNOULLI_SYMBOL_MAP,
            expected_terms=BERNOULLI_EXPECTED_TERMS,
        )
    )
    issues.extend(
        _expected_symbol_gaps(
            label="si_tmaze",
            gnn_symbols=_gnn_symbols(root, "gnn/si_tmaze.gnn.md"),
            section_symbols=_section_ontology_symbols(
                root,
                "manuscript/sections/imrad/methods_pymdp/ontology.yaml",
            ),
            symbol_map=SI_SYMBOL_MAP,
            expected_terms=SI_EXPECTED_TERMS,
        )
    )

    variables_path = root / "output" / "data" / "manuscript_variables.json"
    if variables_path.is_file():
        saved = _load_json(variables_path)
        live = generate_variables(root, require_analysis_outputs=False)
        for key in ("sheaf_track_count", "pipeline_track_count", "imrad_manifest_rows"):
            if saved.get(key) != live.get(key):
                issues.append(f"manuscript variable {key!r} is stale: saved={saved.get(key)!r}, live={live.get(key)!r}")

    summary = _load_json(root / "output" / "data" / "si_tmaze_summary.json")
    stats = _load_json(root / "output" / "data" / "analysis_statistics.json")
    if summary and stats:
        if summary.get("mode") != stats.get("pymdp_mode"):
            issues.append(f"pymdp mode mismatch: summary={summary.get('mode')!r}, stats={stats.get('pymdp_mode')!r}")
        if summary.get("config_hash") != stats.get("pymdp_config_hash"):
            issues.append(
                f"pymdp config hash mismatch: summary={summary.get('config_hash')!r}, "
                f"stats={stats.get('pymdp_config_hash')!r}"
            )

    policy = _policy_comparison_restrictions(root)
    if set(policy["modes"]) != {"policy_inference", "state_inference"}:
        issues.append(f"policy comparison mode set invalid: {policy['modes']!r}")
    if policy["run_count"] < 4:
        issues.append(f"policy comparison run count too small: {policy['run_count']!r}")
    if not policy["complete_grid"]:
        issues.append("policy comparison grid is incomplete")
    if not policy["all_efe_rows_explained"]:
        issues.append("policy comparison EFE rows are not explained")

    posterior = _policy_posterior_restrictions(root)
    if posterior["row_count"] < 1:
        issues.append("pymdp policy posterior grid has no rows")
    if not posterior["all_available_posteriors_normalized"]:
        issues.append("pymdp policy posterior grid has unnormalized posterior rows")
    if not posterior["all_unavailable_rows_explained"]:
        issues.append("pymdp policy posterior grid has unexplained unavailable rows")

    runtime = _runtime_diagnostics_restrictions(root)
    if not runtime["ok"]:
        issues.append("pymdp runtime diagnostics are not ok")
    if runtime["unexpected_warning_count"] != 0:
        issues.append("pymdp runtime diagnostics captured unexpected warnings")

    graph_world = _graph_world_restrictions(root)
    if not graph_world["steps_match"]:
        issues.append(
            "graph-world summary/trace mismatch: "
            f"summary steps={graph_world['steps']!r}, trace steps={graph_world['trace_steps']!r}"
        )
    if not graph_world["goal_reached"]:
        issues.append("graph-world summary does not record goal_reached=true")

    frame_count = _animation_frame_count(root)
    if frame_count < 2:
        issues.append(f"animation frame count too small: {frame_count}")
    from visualizations.animation import validate_animation_frame_deltas

    issues.extend(validate_animation_frame_deltas(root))

    lean = _lean_status(root)
    if not lean["all_proved"]:
        issues.append("Lean boundary is not fully proved")

    issues.extend(validate_configured_artifact_producers(root))

    from validation_spine import validate_validation_spine

    issues.extend(validate_validation_spine(root))

    from roadmap_tracks import (
        validate_formal_interop_artifacts,
        validate_integration_audit_artifacts,
        validate_sheaf_track_artifacts,
        validate_toy_sweep_artifacts,
    )

    issues.extend(validate_toy_sweep_artifacts(root))
    issues.extend(validate_formal_interop_artifacts(root))
    issues.extend(validate_integration_audit_artifacts(root))
    issues.extend(validate_sheaf_track_artifacts(root, validate_saved_certificate=False))

    from gates.claim_ledger import validate_typed_claim_evidence

    if not validate_typed_claim_evidence(root, allow_missing_certificate=True):
        issues.append("typed claim evidence failed")

    return issues
