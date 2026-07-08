"""Deterministic toy sweep artifacts for promoted roadmap tracks.

Facade over the split modules:

- ``toy_sweep_types`` — schema constants and tolerances.
- ``toy_sweep_helpers`` — closed-form observable helpers.
- ``toy_sweep_builders`` — the ``build_*`` artifact builders.

The write/validate orchestration stays here, and every builder, helper, and
schema constant is re-exported so existing imports from
``roadmap_tracks.toy_sweep`` keep working unchanged.
"""

from __future__ import annotations

from pathlib import Path

from json_io import load_json, write_json
from roadmap_tracks.row_aggregates import all_rows
from roadmap_tracks.toy_sweep_builders import (
    _graph_world_trace_invariants,
    _topology_trace,
    build_analytical_assumption_index,
    build_analytical_observable_sweep,
    build_causal_ablation_matrix,
    build_efe_terms,
    build_graph_world_invariants,
    build_graph_world_topology_sweep,
    build_graph_world_topology_traces,
    build_policy_grid,
    build_sensitivity_sweep,
    build_state_space_catalog,
    build_toy_benchmark_matrix,
    build_uncertainty_summary,
)
from roadmap_tracks.toy_sweep_helpers import (
    _joint_entropy,
    _marginal_entropy,
    _posterior_correlation,
    _same_state_probability,
)
from roadmap_tracks.toy_sweep_types import (
    ASSUMPTION_INDEX_SCHEMA,
    EXPECTED_ASSUMPTION_EQUATIONS,
    OBSERVABLE_RESIDUAL_TOLERANCE,
    TOY_SWEEP_SCHEMA,
)

__all__ = [
    "ASSUMPTION_INDEX_SCHEMA",
    "EXPECTED_ASSUMPTION_EQUATIONS",
    "OBSERVABLE_RESIDUAL_TOLERANCE",
    "TOY_SWEEP_SCHEMA",
    "_graph_world_trace_invariants",
    "_joint_entropy",
    "_marginal_entropy",
    "_posterior_correlation",
    "_same_state_probability",
    "_topology_trace",
    "build_analytical_assumption_index",
    "build_analytical_observable_sweep",
    "build_causal_ablation_matrix",
    "build_efe_terms",
    "build_graph_world_invariants",
    "build_graph_world_topology_sweep",
    "build_graph_world_topology_traces",
    "build_policy_grid",
    "build_sensitivity_sweep",
    "build_state_space_catalog",
    "build_toy_benchmark_matrix",
    "build_uncertainty_summary",
    "validate_toy_sweep_artifacts",
    "write_toy_sweep_artifacts",
]


def write_toy_sweep_artifacts(project_root: Path) -> dict[str, Path]:
    """Write toy sweep artifacts to the output path."""
    root = project_root.resolve()
    return {
        "analytical_observable": write_json(
            root / "output" / "data" / "analytical_observable_sweep.json",
            build_analytical_observable_sweep(root),
        ),
        "analytical_assumptions": write_json(
            root / "output" / "data" / "analytical_assumption_index.json",
            build_analytical_assumption_index(root),
        ),
        "sensitivity": write_json(root / "output" / "data" / "sensitivity_sweep.json", build_sensitivity_sweep(root)),
        "uncertainty": write_json(
            root / "output" / "data" / "uncertainty_summary.json",
            build_uncertainty_summary(root),
        ),
        "benchmark": write_json(
            root / "output" / "data" / "toy_benchmark_matrix.json",
            build_toy_benchmark_matrix(root),
        ),
        "policy_grid": write_json(root / "output" / "data" / "si_policy_grid.json", build_policy_grid(root)),
        "efe_terms": write_json(root / "output" / "data" / "si_efe_terms.json", build_efe_terms(root)),
        "graph_topology": write_json(
            root / "output" / "data" / "si_graph_world_topology_sweep.json",
            build_graph_world_topology_sweep(root),
        ),
        "graph_topology_traces": write_json(
            root / "output" / "data" / "si_graph_world_topology_traces.json",
            build_graph_world_topology_traces(root),
        ),
        "graph_invariants": write_json(
            root / "output" / "reports" / "graph_world_invariants.json",
            build_graph_world_invariants(root),
        ),
        "state_space_catalog": write_json(
            root / "output" / "data" / "state_space_catalog.json",
            build_state_space_catalog(root),
        ),
        "causal_ablation": write_json(
            root / "output" / "data" / "causal_ablation_matrix.json",
            build_causal_ablation_matrix(root),
        ),
    }


def validate_toy_sweep_artifacts(project_root: Path) -> list[str]:
    """Validate toy sweep artifacts."""
    root = project_root.resolve()
    issues: list[str] = []
    # PR#23 hardening class: every aggregate below is re-derived from its rows
    # (matching the builder's own derivation) so a row-only forgery — rows
    # contradicting a True stored flag — cannot pass.
    sensitivity = load_json(root / "output" / "data" / "sensitivity_sweep.json")
    if sensitivity.get("schema") != "template_active_inference.sensitivity_sweep.v1":
        issues.append("sensitivity_sweep.json schema mismatch")
    sensitivity_rows = sensitivity.get("rows") or []
    sensitivity_complete = bool(sensitivity_rows) and len(sensitivity_rows) == sensitivity.get("expected_cells")
    if (
        sensitivity.get("row_count") != sensitivity.get("expected_cells")
        or sensitivity.get("complete_grid") is not True
        or sensitivity.get("complete_grid") != sensitivity_complete
    ):
        issues.append("sensitivity_sweep.json grid is incomplete")
    uncertainty = load_json(root / "output" / "data" / "uncertainty_summary.json")
    if uncertainty.get("schema") != "template_active_inference.uncertainty_summary.v1":
        issues.append("uncertainty_summary.json schema mismatch")
    uncertainty_normalized = all_rows(uncertainty, lambda row: bool(row.get("normalized")))
    if uncertainty.get("all_normalized") is not True or uncertainty.get("all_normalized") != uncertainty_normalized:
        issues.append("uncertainty_summary.json contains unnormalized rows")
    benchmark = load_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    if benchmark.get("schema") != "template_active_inference.toy_benchmark_matrix.v1":
        issues.append("toy_benchmark_matrix.json schema mismatch")
    if set(benchmark.get("models") or []) != {"bernoulli_ising", "si_tmaze", "graph_world"}:
        issues.append("toy_benchmark_matrix.json model set is incomplete")
    benchmark_complete = all_rows(
        benchmark, lambda row: bool(row.get("artifact")) and bool(row.get("metric")) and bool(row.get("gate_passed"))
    )
    if benchmark.get("all_models_complete") is not True or benchmark.get("all_models_complete") != benchmark_complete:
        issues.append("toy_benchmark_matrix.json has incomplete model rows")
    policy = load_json(root / "output" / "data" / "si_policy_grid.json")
    policy_rows = policy.get("rows") or []
    policy_summary = policy.get("summary") or {}
    policy_expected = (
        len(policy_summary.get("modes") or [])
        * len(policy_summary.get("horizons") or [])
        * len(policy_summary.get("seeds") or [])
    )
    policy_complete = bool(policy_rows) and len(policy_rows) == policy_expected
    if policy.get("complete_grid") is not True or not policy_complete:
        issues.append("si_policy_grid.json grid is incomplete")
    efe = load_json(root / "output" / "data" / "si_efe_terms.json")
    efe_rows = efe.get("rows") or []
    efe_derived = bool(efe_rows) and all(
        (row.get("terms_available") and bool((row.get("terms") or {}).get("values")))
        or (not row.get("terms_available") and bool(row.get("fallback_reason")))
        for row in efe_rows
    )
    if efe.get("schema") != "template_active_inference.si_efe_values.v1":
        issues.append("si_efe_terms.json schema mismatch")
    if efe.get("all_rows_explained") is not True or efe.get("all_rows_explained") != efe_derived:
        # Re-derived from rows, so a row claiming terms with none — or a tampered summary —
        # is caught even when the stored boolean still reads true.
        issues.append("si_efe_terms.json has unexplained EFE rows")
    topology = load_json(root / "output" / "data" / "si_graph_world_topology_sweep.json")
    topology_agree = all_rows(topology, lambda row: bool(row.get("summary_trace_agreement")))
    if topology.get("all_summary_trace_agree") is not True or topology.get("all_summary_trace_agree") != topology_agree:
        issues.append("si_graph_world_topology_sweep.json summary/trace mismatch")
    topology_traces = load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    traces_agree = all_rows(topology_traces, lambda row: bool(row.get("trace_summary_agree")))
    if (
        topology_traces.get("all_trace_summary_agree") is not True
        or topology_traces.get("all_trace_summary_agree") != traces_agree
    ):
        issues.append("si_graph_world_topology_traces.json summary/trace mismatch")
    if topology_traces.get("topology_count") != topology.get("topology_count"):
        issues.append("si_graph_world_topology_traces.json topology count mismatch")
    invariants = load_json(root / "output" / "reports" / "graph_world_invariants.json")
    invariant_rows = invariants.get("rows") or []
    invariants_derived = bool(invariant_rows) and all(row.get("passed") for row in invariant_rows)
    if invariants.get("all_passed") is not True or invariants.get("all_passed") != invariants_derived:
        # Re-derived from rows: a single failing invariant row — or a tampered summary that
        # keeps all_passed true over a failing row — fails closed.
        issues.append("graph_world_invariants.json records a failing invariant")
    catalog = load_json(root / "output" / "data" / "state_space_catalog.json")
    if catalog.get("schema") != "template_active_inference.state_space_catalog.v1":
        issues.append("state_space_catalog.json schema mismatch")
    catalog_finite = all_rows(catalog, lambda row: bool(row.get("finite")))
    catalog_counts = all_rows(
        catalog, lambda row: int(row.get("state_count", 0)) > 0 and int(row.get("policy_count", 0)) >= 1
    )
    if (
        catalog.get("all_finite") is not True
        or catalog.get("all_finite") != catalog_finite
        or catalog.get("all_counts_positive") is not True
        or catalog.get("all_counts_positive") != catalog_counts
    ):
        issues.append("state_space_catalog.json has missing or non-finite state spaces")
    ablation = load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    if ablation.get("schema") != "template_active_inference.causal_ablation_matrix.v1":
        issues.append("causal_ablation_matrix.json schema mismatch")
    ablation_rows = ablation.get("rows") or []
    ablation_complete = bool(ablation_rows) and len(ablation_rows) == ablation.get("expected_cells")
    ablation_deterministic = all_rows(ablation, lambda row: bool(row.get("deterministic")))
    if (
        ablation.get("complete_grid") is not True
        or ablation.get("complete_grid") != ablation_complete
        or ablation.get("all_deterministic") is not True
        or ablation.get("all_deterministic") != ablation_deterministic
    ):
        issues.append("causal_ablation_matrix.json has incomplete or non-deterministic cells")
    observable = load_json(root / "output" / "data" / "analytical_observable_sweep.json")
    observable_rows = observable.get("rows") or []
    observable_ids = {str(row.get("observable")) for row in observable_rows if row.get("observable")}
    required_observables = {
        "same_state_probability",
        "posterior_correlation",
        "ising_spin_correlation",
        "joint_entropy",
        "marginal_entropy",
    }
    observables_complete = required_observables.issubset(observable_ids) and all_rows(
        observable,
        lambda row: (
            bool(row.get("equation_id"))
            and bool(row.get("assumption_links"))
            and abs(float(row.get("residual", 1.0))) <= float(row.get("residual_tolerance", 0.0) or 0.0)
        ),
    )
    if float(observable.get("max_abs_residual", 1.0)) > OBSERVABLE_RESIDUAL_TOLERANCE:
        issues.append("analytical_observable_sweep.json residual exceeds tolerance")
    if not observables_complete:
        issues.append("analytical_observable_sweep.json observable set is incomplete")
    assumptions = load_json(root / "output" / "data" / "analytical_assumption_index.json")
    if assumptions.get("schema") != ASSUMPTION_INDEX_SCHEMA:
        issues.append("analytical_assumption_index.json schema mismatch")
    if set(assumptions.get("equation_ids") or []) != EXPECTED_ASSUMPTION_EQUATIONS:
        issues.append("analytical_assumption_index.json equation set is incomplete")
    assumptions_indexed = all_rows(
        assumptions,
        lambda row: (
            bool(row.get("assumptions")) and row.get("status") == "indexed" and bool(row.get("evidence_artifact"))
        ),
    )
    if (
        assumptions.get("all_equations_indexed") is not True
        or assumptions.get("all_equations_indexed") != assumptions_indexed
    ):
        issues.append("analytical_assumption_index.json has unindexed equations")
    return issues
