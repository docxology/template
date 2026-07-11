"""Direct tests for ``roadmap_tracks.toy_sweep_builders``.

These builders are pure readers over the tracked ``output/data`` snapshot, so
they run against the real project root read-only. See
``direct_recompute_support`` for why direct coverage of the recompute modules
matters (leg-deterministic coverage floor).
"""

from __future__ import annotations

from pathlib import Path

from analytical.hyperparameters import lambda_grid, load_hyperparameters
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
from roadmap_tracks.toy_sweep_types import OBSERVABLE_RESIDUAL_TOLERANCE


def test_observable_sweep_rows_cover_lambda_grid(project_root: Path) -> None:
    payload = build_analytical_observable_sweep(project_root)
    grid = lambda_grid(load_hyperparameters())
    assert payload["schema"] == "template_active_inference.analytical_observable_sweep.v1"
    assert payload["row_count"] == len(payload["rows"]) == len(grid) * 5
    assert payload["max_abs_residual"] <= OBSERVABLE_RESIDUAL_TOLERANCE
    observables = {row["observable"] for row in payload["rows"]}
    assert observables == {
        "same_state_probability",
        "posterior_correlation",
        "ising_spin_correlation",
        "joint_entropy",
        "marginal_entropy",
    }
    for row in payload["rows"]:
        assert abs(row["residual"]) <= OBSERVABLE_RESIDUAL_TOLERANCE
        assert row["assumption_links"]


def test_assumption_index_is_fully_indexed(project_root: Path) -> None:
    payload = build_analytical_assumption_index(project_root)
    assert payload["all_equations_indexed"] is True
    assert payload["row_count"] == 7
    assert payload["equation_ids"] == sorted(payload["equation_ids"])
    assert "binary_policy_space" in payload["assumption_ids"]


def test_sensitivity_sweep_is_a_complete_grid(project_root: Path) -> None:
    payload = build_sensitivity_sweep(project_root)
    assert payload["complete_grid"] is True
    assert payload["row_count"] == payload["expected_cells"] == 24
    assert {row["topology"] for row in payload["rows"]} == {"linear4", "branch4"}


def test_uncertainty_summary_rows_are_normalized(project_root: Path) -> None:
    payload = build_uncertainty_summary(project_root)
    assert payload["all_normalized"] is True
    assert payload["row_count"] == len(payload["rows"]) > 0
    for row in payload["rows"]:
        assert abs(sum(row["posterior"]) - 1.0) <= 1e-9
        assert row["belief_entropy"] >= 0.0


def test_toy_benchmark_matrix_covers_three_models(project_root: Path) -> None:
    payload = build_toy_benchmark_matrix(project_root)
    assert payload["all_models_complete"] is True
    assert payload["models"] == ["bernoulli_ising", "si_tmaze", "graph_world"]


def test_policy_grid_reflects_comparison_runs(project_root: Path) -> None:
    payload = build_policy_grid(project_root)
    assert payload["schema"] == "template_active_inference.si_policy_grid.v1"
    assert payload["summary"]["run_count"] == len(payload["rows"]) > 0
    assert payload["complete_grid"] is True


def test_efe_terms_rows_are_explained(project_root: Path) -> None:
    payload = build_efe_terms(project_root)
    assert payload["all_rows_explained"] is True
    for row in payload["rows"]:
        if row["terms_available"]:
            assert row["terms"]["values"]
        else:
            assert row["fallback_reason"]


def test_topology_traces_end_at_goal_for_all_shapes() -> None:
    for topology in ("linear4", "branch4", "diamond5", "loop5"):
        trace = _topology_trace(topology)
        assert trace[-1]["node"] == "goal"
        assert trace[-1]["action"] == "stay_goal"
        assert all(row["action"] == "advance" for row in trace[:-1])


def test_topology_sweep_and_traces_agree(project_root: Path) -> None:
    sweep = build_graph_world_topology_sweep(project_root)
    traces = build_graph_world_topology_traces(project_root)
    assert sweep["all_summary_trace_agree"] is True
    assert traces["all_trace_summary_agree"] is True
    assert sweep["topology_count"] == traces["topology_count"] == 4


def test_trace_invariants_pass_on_generated_traces() -> None:
    results = _graph_world_trace_invariants(_topology_trace("linear4"))
    assert results == {
        "reachability": True,
        "transition_determinism": True,
        "terminal_absorbing": True,
    }


def test_trace_invariants_fail_on_goalless_trace() -> None:
    trace = [{"step": 0, "node": "start", "action": "advance"}, {"step": 1, "node": "cue", "action": "stay"}]
    results = _graph_world_trace_invariants(trace)
    assert results["reachability"] is False
    assert results["terminal_absorbing"] is False


def test_trace_invariants_fail_on_nondeterministic_successor() -> None:
    trace = [
        {"step": 0, "node": "start", "action": "advance"},
        {"step": 1, "node": "cue", "action": "advance"},
        {"step": 2, "node": "start", "action": "advance"},
        {"step": 3, "node": "goal", "action": "stay_goal"},
    ]
    results = _graph_world_trace_invariants(trace)
    assert results["transition_determinism"] is False


def test_trace_invariants_fail_when_goal_is_left() -> None:
    trace = [
        {"step": 0, "node": "start", "action": "advance"},
        {"step": 1, "node": "goal", "action": "advance"},
        {"step": 2, "node": "start", "action": "advance"},
        {"step": 3, "node": "goal", "action": "stay_goal"},
    ]
    results = _graph_world_trace_invariants(trace)
    assert results["terminal_absorbing"] is False
    assert results["reachability"] is True


def test_graph_world_invariants_all_pass(project_root: Path) -> None:
    payload = build_graph_world_invariants(project_root)
    assert payload["all_passed"] is True
    assert payload["invariant_count"] == 4 * 3


def test_state_space_catalog_counts_are_positive(project_root: Path) -> None:
    payload = build_state_space_catalog(project_root)
    assert payload["all_finite"] is True
    assert payload["all_counts_positive"] is True
    assert payload["row_count"] == 2 + 4
    assert "graph_world_linear4" in payload["model_ids"]


def test_causal_ablation_matrix_is_a_complete_grid(project_root: Path) -> None:
    payload = build_causal_ablation_matrix(project_root)
    assert payload["complete_grid"] is True
    assert payload["row_count"] == payload["expected_cells"] == 4 * 3 * 3
    assert payload["all_deterministic"] is True
    noise_effects = {
        row["effect"] - row["lambda"] * 0.1 for row in payload["rows"] if row["perturbation"] == "likelihood_noise_low"
    }
    assert all(abs(delta - 0.05) < 1e-9 for delta in noise_effects)
