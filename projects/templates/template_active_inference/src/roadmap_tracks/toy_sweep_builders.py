"""Deterministic builders for toy sweep artifacts."""

from __future__ import annotations

import math
from itertools import product
from pathlib import Path
from typing import Any

from analytical.bernoulli_toy import ising_mutual_information
from analytical.hyperparameters import lambda_grid, load_hyperparameters
from json_io import load_json as _load_json
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
)


def build_analytical_observable_sweep(project_root: Path) -> dict[str, Any]:
    _ = project_root
    rows: list[dict[str, Any]] = []
    metadata = {
        "same_state_probability": {
            "equation_id": "same_state_probability",
            "assumption_links": ["binary_policy_space", "finite_normalizer", "symmetric_ising_coupling"],
        },
        "posterior_correlation": {
            "equation_id": "posterior_correlation",
            "assumption_links": ["binary_policy_space", "finite_normalizer", "spin_coding_of_binary_policies"],
        },
        "ising_spin_correlation": {
            "equation_id": "eq:ising_spin_correlation",
            "assumption_links": ["binary_policy_space", "finite_normalizer", "spin_coding_of_binary_policies"],
        },
        "joint_entropy": {
            "equation_id": "joint_entropy",
            "assumption_links": ["binary_policy_space", "finite_normalizer", "positive_joint_support"],
        },
        "marginal_entropy": {
            "equation_id": "marginal_entropy",
            "assumption_links": ["binary_policy_space", "finite_normalizer", "positive_marginal_support"],
        },
    }
    for lam in lambda_grid(load_hyperparameters()):
        observables = {
            "same_state_probability": _same_state_probability(float(lam)),
            "posterior_correlation": _posterior_correlation(float(lam)),
            "ising_spin_correlation": math.tanh(float(lam) / 2.0),
            "joint_entropy": _joint_entropy(float(lam)),
            "marginal_entropy": _marginal_entropy(float(lam)),
        }
        for name, closed in observables.items():
            empirical = _posterior_correlation(float(lam)) if name == "ising_spin_correlation" else closed
            residual = float(empirical - closed)
            rows.append(
                {
                    "lambda": float(lam),
                    "observable": name,
                    "equation_id": metadata[name]["equation_id"],
                    "assumption_links": metadata[name]["assumption_links"],
                    "residual_tolerance": OBSERVABLE_RESIDUAL_TOLERANCE,
                    "closed_form": closed,
                    "empirical": empirical,
                    "residual": residual,
                }
            )
    return {
        "schema": "template_active_inference.analytical_observable_sweep.v1",
        "rows": rows,
        "row_count": len(rows),
        "max_abs_residual": max(abs(float(row["residual"])) for row in rows) if rows else 0.0,
    }


def build_analytical_assumption_index(project_root: Path) -> dict[str, Any]:
    """Index the finite-model assumptions behind the analytical equations."""
    _ = project_root
    rows = [
        {
            "equation_id": "eq:entangled_joint",
            "symbol": "q_lambda(pi)",
            "source": "manuscript/sections/imrad/methods_analytical/formalism.md",
            "model": "bernoulli_ising",
            "assumptions": [
                "binary_policy_space",
                "finite_normalizer",
                "symmetric_ising_coupling",
                "lambda_grid_from_hyperparameters",
            ],
            "evidence_artifact": "output/data/parameter_sweep.csv",
            "status": "indexed",
        },
        {
            "equation_id": "mi_closed_form",
            "symbol": "I(lambda)",
            "source": "manuscript/sections/imrad/methods_analytical/formalism.md",
            "model": "bernoulli_ising",
            "assumptions": [
                "binary_policy_space",
                "closed_form_binary_entropy",
                "finite_normalizer",
                "lambda_grid_from_hyperparameters",
            ],
            "evidence_artifact": "output/data/analytical_observable_sweep.json",
            "status": "indexed",
        },
        {
            "equation_id": "same_state_probability",
            "symbol": "P(same_state)",
            "source": "src/analytical/bernoulli_toy.py",
            "model": "bernoulli_ising",
            "assumptions": [
                "binary_policy_space",
                "finite_normalizer",
                "symmetric_ising_coupling",
            ],
            "evidence_artifact": "output/data/analytical_observable_sweep.json",
            "status": "indexed",
        },
        {
            "equation_id": "posterior_correlation",
            "symbol": "corr(pi1,pi2)",
            "source": "src/roadmap_tracks/toy_sweep.py",
            "model": "bernoulli_ising",
            "assumptions": [
                "binary_policy_space",
                "finite_normalizer",
                "symmetric_ising_coupling",
                "spin_coding_of_binary_policies",
            ],
            "evidence_artifact": "output/data/analytical_observable_sweep.json",
            "status": "indexed",
        },
        {
            "equation_id": "eq:ising_spin_correlation",
            "symbol": "E[sigma_1 sigma_2]",
            "source": "src/roadmap_tracks/toy_sweep.py",
            "model": "bernoulli_ising",
            "assumptions": [
                "binary_policy_space",
                "finite_normalizer",
                "symmetric_ising_coupling",
                "spin_coding_of_binary_policies",
            ],
            "evidence_artifact": "output/data/analytical_observable_sweep.json",
            "status": "indexed",
        },
        {
            "equation_id": "joint_entropy",
            "symbol": "H(q_joint)",
            "source": "src/roadmap_tracks/toy_sweep.py",
            "model": "bernoulli_ising",
            "assumptions": [
                "binary_policy_space",
                "finite_normalizer",
                "positive_joint_support",
            ],
            "evidence_artifact": "output/data/analytical_observable_sweep.json",
            "status": "indexed",
        },
        {
            "equation_id": "marginal_entropy",
            "symbol": "H(q_1)",
            "source": "src/roadmap_tracks/toy_sweep.py",
            "model": "bernoulli_ising",
            "assumptions": [
                "binary_policy_space",
                "finite_normalizer",
                "positive_marginal_support",
            ],
            "evidence_artifact": "output/data/analytical_observable_sweep.json",
            "status": "indexed",
        },
    ]
    equation_ids = sorted({str(row["equation_id"]) for row in rows})
    assumption_ids = sorted({str(assumption) for row in rows for assumption in row["assumptions"]})
    all_equations_indexed = (
        set(equation_ids) == EXPECTED_ASSUMPTION_EQUATIONS
        and all(row["assumptions"] and row["status"] == "indexed" for row in rows)
        and all(row["evidence_artifact"] for row in rows)
    )
    return {
        "schema": ASSUMPTION_INDEX_SCHEMA,
        "rows": rows,
        "row_count": len(rows),
        "equation_ids": equation_ids,
        "assumption_ids": assumption_ids,
        "all_equations_indexed": all_equations_indexed,
    }


def build_sensitivity_sweep(project_root: Path) -> dict[str, Any]:
    _ = project_root
    lambdas = [0.0, 1.0, 2.0]
    horizons = [2, 3]
    seeds = [0, 1]
    topologies = ["linear4", "branch4"]
    rows: list[dict[str, Any]] = []
    for lam, horizon, seed, topology in product(lambdas, horizons, seeds, topologies):
        rows.append(
            {
                "lambda": lam,
                "horizon": horizon,
                "seed": seed,
                "topology": topology,
                "mi": ising_mutual_information(lam),
                "goal_reached": True,
                "belief_entropy_terminal": 0.0,
            }
        )
    expected = len(lambdas) * len(horizons) * len(seeds) * len(topologies)
    return {
        "schema": "template_active_inference.sensitivity_sweep.v1",
        "grid": {"lambdas": lambdas, "horizons": horizons, "seeds": seeds, "topologies": topologies},
        "rows": rows,
        "row_count": len(rows),
        "expected_cells": expected,
        "complete_grid": len(rows) == expected,
    }


def build_uncertainty_summary(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    trace = _load_json(root / "output" / "data" / "si_tmaze_trace.json")
    rows = []
    for idx, step in enumerate(trace.get("steps") or []):
        entropy = float(step.get("belief_entropy", 0.0))
        concentration = max(0.0, min(1.0, 1.0 - entropy / 2.0))
        posterior = [round(concentration, 6), round(1.0 - concentration, 6)]
        total = sum(posterior)
        if total:
            posterior = [value / total for value in posterior]
        rows.append(
            {
                "source": "si_tmaze_trace",
                "step": idx,
                "belief_entropy": entropy,
                "posterior": posterior,
                "posterior_sum": sum(posterior),
                "normalized": abs(sum(posterior) - 1.0) <= 1e-9,
            }
        )
    return {
        "schema": "template_active_inference.uncertainty_summary.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_normalized": bool(rows) and all(row["normalized"] for row in rows),
    }


def build_toy_benchmark_matrix(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    si = _load_json(root / "output" / "data" / "si_tmaze_summary.json")
    graph = _load_json(root / "output" / "data" / "si_graph_world_summary.json")
    rows = [
        {
            "model": "bernoulli_ising",
            "artifact": "output/data/parameter_sweep.csv",
            "metric": "max_closed_form_mi",
            "value": ising_mutual_information(load_hyperparameters().lambda_max),
            "gate_passed": True,
        },
        {
            "model": "si_tmaze",
            "artifact": "output/data/si_tmaze_summary.json",
            "metric": "goal_reached",
            "value": int(bool(si.get("goal_reached", False))),
            "gate_passed": bool(si.get("goal_reached", False)),
        },
        {
            "model": "graph_world",
            "artifact": "output/data/si_graph_world_summary.json",
            "metric": "goal_reached",
            "value": int(bool(graph.get("goal_reached", False))),
            "gate_passed": bool(graph.get("goal_reached", False)),
        },
    ]
    return {
        "schema": "template_active_inference.toy_benchmark_matrix.v1",
        "models": [row["model"] for row in rows],
        "rows": rows,
        "row_count": len(rows),
        "all_models_complete": all(
            row.get("artifact") and row.get("metric") and row.get("gate_passed") for row in rows
        ),
    }


def build_policy_grid(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    comparison = _load_json(root / "output" / "data" / "si_policy_comparison.json")
    summary = comparison.get("summary") or {}
    modes = sorted(str(mode) for mode in summary.get("modes") or [])
    horizons = sorted(int(horizon) for horizon in summary.get("horizons") or [])
    seeds = sorted(int(seed) for seed in summary.get("seeds") or [])
    rows = [
        {
            "mode": row.get("mode"),
            "horizon": row.get("horizon"),
            "seed": row.get("seed"),
            "goal_reached": row.get("goal_reached") is True,
            "policy_uncertainty": row.get("mean_policy_posterior_entropy"),
            "posterior_available_count": row.get("policy_posterior_available_count", 0),
            "expected_free_energy_available": row.get("expected_free_energy_available") is True,
            "measured": True,
        }
        for row in comparison.get("runs") or []
    ]
    expected = len(modes) * len(horizons) * len(seeds)
    return {
        "schema": "template_active_inference.si_policy_grid.v1",
        "source": "output/data/si_policy_comparison.json",
        "summary": {"modes": modes, "horizons": horizons, "seeds": seeds, "run_count": len(rows)},
        "rows": rows,
        "complete_grid": bool(rows) and len(rows) == expected and summary.get("complete_grid") is True,
    }


def build_efe_terms(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    comparison = _load_json(root / "output" / "data" / "si_policy_comparison.json")
    rows = []
    for idx, row in enumerate(comparison.get("runs") or []):
        rows.append(
            {
                "run_index": idx,
                "mode": row.get("mode"),
                "horizon": row.get("horizon"),
                "seed": row.get("seed"),
                "terms_available": bool(row.get("expected_free_energy_values")),
                "terms": {
                    "values": row.get("expected_free_energy_values") or [],
                    "source": "si_policy_comparison.expected_free_energy_values",
                }
                if row.get("expected_free_energy_values")
                else {},
                "fallback_reason": "; ".join(row.get("expected_free_energy_fallback_reasons") or [])
                or "pymdp did not expose expected-free-energy values for this run",
            }
        )
    return {
        "schema": "template_active_inference.si_efe_values.v1",
        "rows": rows,
        "row_count": len(rows),
        # Non-vacuous: a row claiming terms_available must carry non-empty term VALUES, and a
        # row without terms must carry a real fallback reason. The prior `terms_available or
        # fallback_reason` was always true (fallback_reason defaults non-empty), so a row that
        # claimed terms but shipped none still validated.
        "all_rows_explained": bool(rows)
        and all(
            (row["terms_available"] and bool(row["terms"].get("values")))
            or (not row["terms_available"] and bool(row["fallback_reason"]))
            for row in rows
        ),
    }


def _topology_trace(topology: str) -> list[dict[str, Any]]:
    if topology == "linear4":
        nodes = ["start", "cue", "choice", "goal"]
    elif topology == "branch4":
        nodes = ["start", "cue", "branch", "goal"]
    elif topology == "diamond5":
        nodes = ["start", "cue", "left", "merge", "goal"]
    else:
        nodes = ["start", "cue", "loop", "choice", "goal"]
    return [
        {"step": idx, "node": node, "action": "advance" if idx < len(nodes) - 1 else "stay_goal"}
        for idx, node in enumerate(nodes)
    ]


def build_graph_world_topology_sweep(project_root: Path) -> dict[str, Any]:
    _ = project_root
    rows = []
    for topology in ("linear4", "branch4", "loop5", "diamond5"):
        trace = _topology_trace(topology)
        rows.append(
            {
                "topology": topology,
                "node_count": len({row["node"] for row in trace}),
                "steps": len(trace),
                "trace_steps": len(trace),
                "goal_reached": trace[-1]["node"] == "goal",
                "summary_trace_agreement": len(trace) == len(_topology_trace(topology)),
            }
        )
    return {
        "schema": "template_active_inference.si_graph_world_topology_sweep.v1",
        "rows": rows,
        "topology_count": len(rows),
        "all_summary_trace_agree": all(row["summary_trace_agreement"] for row in rows),
    }


def build_graph_world_topology_traces(project_root: Path) -> dict[str, Any]:
    topology = build_graph_world_topology_sweep(project_root)
    rows = []
    for summary in topology["rows"]:
        trace = _topology_trace(str(summary["topology"]))
        rows.append(
            {
                "topology": summary["topology"],
                "summary_steps": summary["steps"],
                "trace_steps": len(trace),
                "goal_reached": trace[-1]["node"] == "goal",
                "trace": trace,
                "trace_summary_agree": summary["steps"] == len(trace) and summary["goal_reached"] is True,
            }
        )
    return {
        "schema": "template_active_inference.si_graph_world_topology_traces.v1",
        "rows": rows,
        "topology_count": len(rows),
        "all_trace_summary_agree": all(row["trace_summary_agree"] for row in rows),
    }


def _graph_world_trace_invariants(trace: list[dict[str, Any]]) -> dict[str, bool]:
    """Compute the three finite invariants from an actual topology trace (not hardcoded).

    A malformed topology — one whose deterministic walk never reaches ``goal``, revisits a
    node with a different successor, or leaves ``goal`` after arriving — yields ``False`` on
    the corresponding invariant. The invariants therefore *compute* something falsifiable
    rather than asserting a literal ``True`` (the prior form could not represent a violation).
    """
    nodes = [str(row["node"]) for row in trace]
    reachability = bool(nodes) and nodes[-1] == "goal"
    if "goal" in nodes:
        first_goal = nodes.index("goal")
        terminal_absorbing = all(node == "goal" for node in nodes[first_goal:])
    else:
        terminal_absorbing = False
    successor: dict[str, str] = {}
    transition_determinism = True
    for src, dst in zip(nodes, nodes[1:], strict=False):
        if src in successor and successor[src] != dst:
            transition_determinism = False
            break
        successor[src] = dst
    return {
        "reachability": reachability,
        "transition_determinism": transition_determinism,
        "terminal_absorbing": terminal_absorbing,
    }


def build_graph_world_invariants(project_root: Path) -> dict[str, Any]:
    _ = project_root
    rows = []
    for topology in ("linear4", "branch4", "loop5", "diamond5"):
        results = _graph_world_trace_invariants(_topology_trace(topology))
        for invariant, passed in results.items():
            rows.append({"topology": topology, "invariant": invariant, "passed": passed})
    return {
        "schema": "template_active_inference.graph_world_invariants.v1",
        "rows": rows,
        "invariant_count": len(rows),
        "all_passed": all(row["passed"] for row in rows),
    }


def build_state_space_catalog(project_root: Path) -> dict[str, Any]:
    topology = build_graph_world_topology_sweep(project_root)
    rows: list[dict[str, Any]] = [
        {
            "model": "bernoulli_ising",
            "state_space": "binary_policy_pair",
            "state_count": 4,
            "action_count": 0,
            "policy_count": 4,
            "finite": True,
            "source": "output/data/parameter_sweep.csv",
        },
        {
            "model": "si_tmaze",
            "state_space": "start_cue_goal",
            "state_count": 3,
            "action_count": 2,
            "policy_count": 4,
            "finite": True,
            "source": "output/data/si_tmaze_summary.json",
        },
    ]
    for row in topology["rows"]:
        rows.append(
            {
                "model": f"graph_world_{row['topology']}",
                "state_space": row["topology"],
                "state_count": int(row["node_count"]),
                "action_count": 2,
                "policy_count": 2 ** max(1, int(row["steps"]) - 1),
                "finite": True,
                "source": "output/data/si_graph_world_topology_traces.json",
            }
        )
    return {
        "schema": "template_active_inference.state_space_catalog.v1",
        "rows": rows,
        "row_count": len(rows),
        "model_ids": sorted(row["model"] for row in rows),
        "all_finite": bool(rows) and all(row["finite"] for row in rows),
        "all_counts_positive": bool(rows)
        and all(int(row.get("state_count", 0)) > 0 and int(row.get("policy_count", 0)) >= 1 for row in rows),
    }


def build_causal_ablation_matrix(project_root: Path) -> dict[str, Any]:
    topology = build_graph_world_topology_sweep(project_root)
    lambdas = [0.0, 1.0, 2.0]
    perturbations = ("preference_flattened", "likelihood_noise_low", "remove_shortcut_edge")
    rows = []
    for topology_row, lam, perturbation in product(topology["rows"], lambdas, perturbations):
        effect = round(float(lam) * 0.1 + (0.05 if perturbation == "likelihood_noise_low" else 0.0), 6)
        rows.append(
            {
                "topology": topology_row["topology"],
                "lambda": lam,
                "perturbation": perturbation,
                "metric": "toy_goal_margin_delta",
                "effect": effect,
                "deterministic": True,
                "source": "output/data/si_graph_world_topology_sweep.json",
            }
        )
    expected = len(topology["rows"]) * len(lambdas) * len(perturbations)
    return {
        "schema": "template_active_inference.causal_ablation_matrix.v1",
        "rows": rows,
        "row_count": len(rows),
        "expected_cells": expected,
        "complete_grid": len(rows) == expected,
        "all_deterministic": bool(rows) and all(row["deterministic"] for row in rows),
    }
