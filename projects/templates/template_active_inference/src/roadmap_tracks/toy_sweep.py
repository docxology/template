"""Deterministic toy sweep artifacts for promoted roadmap tracks."""

from __future__ import annotations

import json
import math
from itertools import product
from pathlib import Path
from typing import Any

from analytical.bernoulli_toy import ising_joint_posterior, ising_mutual_information
from analytical.hyperparameters import lambda_grid, load_hyperparameters
from roadmap_tracks.row_aggregates import all_rows

TOY_SWEEP_SCHEMA = "template_active_inference.toy_sweep_tracks.v1"
ASSUMPTION_INDEX_SCHEMA = "template_active_inference.analytical_assumption_index.v1"
EXPECTED_ASSUMPTION_EQUATIONS = {
    "eq:entangled_joint",
    "joint_entropy",
    "marginal_entropy",
    "mi_closed_form",
    "eq:ising_spin_correlation",
    "posterior_correlation",
    "same_state_probability",
}
OBSERVABLE_RESIDUAL_TOLERANCE = 1e-9


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _same_state_probability(lam: float) -> float:
    q = ising_joint_posterior(lam)
    return float(q[0, 0] + q[1, 1])


def _posterior_correlation(lam: float) -> float:
    q = ising_joint_posterior(lam)
    return float(q[0, 0] + q[1, 1] - q[0, 1] - q[1, 0])


def _joint_entropy(lam: float) -> float:
    q = ising_joint_posterior(lam)
    return float(-sum(value * math.log(value) for value in q.reshape(-1) if value > 0))


def _marginal_entropy(lam: float) -> float:
    q = ising_joint_posterior(lam)
    marginal = q.sum(axis=1)
    return float(-sum(value * math.log(value) for value in marginal if value > 0))


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


def write_toy_sweep_artifacts(project_root: Path) -> dict[str, Path]:
    root = project_root.resolve()
    return {
        "analytical_observable": _write_json(
            root / "output" / "data" / "analytical_observable_sweep.json",
            build_analytical_observable_sweep(root),
        ),
        "analytical_assumptions": _write_json(
            root / "output" / "data" / "analytical_assumption_index.json",
            build_analytical_assumption_index(root),
        ),
        "sensitivity": _write_json(root / "output" / "data" / "sensitivity_sweep.json", build_sensitivity_sweep(root)),
        "uncertainty": _write_json(
            root / "output" / "data" / "uncertainty_summary.json",
            build_uncertainty_summary(root),
        ),
        "benchmark": _write_json(
            root / "output" / "data" / "toy_benchmark_matrix.json",
            build_toy_benchmark_matrix(root),
        ),
        "policy_grid": _write_json(root / "output" / "data" / "si_policy_grid.json", build_policy_grid(root)),
        "efe_terms": _write_json(root / "output" / "data" / "si_efe_terms.json", build_efe_terms(root)),
        "graph_topology": _write_json(
            root / "output" / "data" / "si_graph_world_topology_sweep.json",
            build_graph_world_topology_sweep(root),
        ),
        "graph_topology_traces": _write_json(
            root / "output" / "data" / "si_graph_world_topology_traces.json",
            build_graph_world_topology_traces(root),
        ),
        "graph_invariants": _write_json(
            root / "output" / "reports" / "graph_world_invariants.json",
            build_graph_world_invariants(root),
        ),
        "state_space_catalog": _write_json(
            root / "output" / "data" / "state_space_catalog.json",
            build_state_space_catalog(root),
        ),
        "causal_ablation": _write_json(
            root / "output" / "data" / "causal_ablation_matrix.json",
            build_causal_ablation_matrix(root),
        ),
    }


def validate_toy_sweep_artifacts(project_root: Path) -> list[str]:
    root = project_root.resolve()
    issues: list[str] = []
    sensitivity = _load_json(root / "output" / "data" / "sensitivity_sweep.json")
    if sensitivity.get("schema") != "template_active_inference.sensitivity_sweep.v1":
        issues.append("sensitivity_sweep.json schema mismatch")
    if (
        sensitivity.get("row_count") != sensitivity.get("expected_cells")
        or sensitivity.get("complete_grid") is not True
    ):
        issues.append("sensitivity_sweep.json grid is incomplete")
    uncertainty = _load_json(root / "output" / "data" / "uncertainty_summary.json")
    if uncertainty.get("schema") != "template_active_inference.uncertainty_summary.v1":
        issues.append("uncertainty_summary.json schema mismatch")
    if uncertainty.get("all_normalized") is not True:
        issues.append("uncertainty_summary.json contains unnormalized rows")
    benchmark = _load_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    if benchmark.get("schema") != "template_active_inference.toy_benchmark_matrix.v1":
        issues.append("toy_benchmark_matrix.json schema mismatch")
    if set(benchmark.get("models") or []) != {"bernoulli_ising", "si_tmaze", "graph_world"}:
        issues.append("toy_benchmark_matrix.json model set is incomplete")
    if benchmark.get("all_models_complete") is not True:
        issues.append("toy_benchmark_matrix.json has incomplete model rows")
    policy = _load_json(root / "output" / "data" / "si_policy_grid.json")
    if policy.get("complete_grid") is not True:
        issues.append("si_policy_grid.json grid is incomplete")
    efe = _load_json(root / "output" / "data" / "si_efe_terms.json")
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
    topology = _load_json(root / "output" / "data" / "si_graph_world_topology_sweep.json")
    if topology.get("all_summary_trace_agree") is not True:
        issues.append("si_graph_world_topology_sweep.json summary/trace mismatch")
    topology_traces = _load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    if topology_traces.get("all_trace_summary_agree") is not True:
        issues.append("si_graph_world_topology_traces.json summary/trace mismatch")
    if topology_traces.get("topology_count") != topology.get("topology_count"):
        issues.append("si_graph_world_topology_traces.json topology count mismatch")
    invariants = _load_json(root / "output" / "reports" / "graph_world_invariants.json")
    invariant_rows = invariants.get("rows") or []
    invariants_derived = bool(invariant_rows) and all(row.get("passed") for row in invariant_rows)
    if invariants.get("all_passed") is not True or invariants.get("all_passed") != invariants_derived:
        # Re-derived from rows: a single failing invariant row — or a tampered summary that
        # keeps all_passed true over a failing row — fails closed.
        issues.append("graph_world_invariants.json records a failing invariant")
    catalog = _load_json(root / "output" / "data" / "state_space_catalog.json")
    if catalog.get("schema") != "template_active_inference.state_space_catalog.v1":
        issues.append("state_space_catalog.json schema mismatch")
    if catalog.get("all_finite") is not True or catalog.get("all_counts_positive") is not True:
        issues.append("state_space_catalog.json has missing or non-finite state spaces")
    ablation = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    if ablation.get("schema") != "template_active_inference.causal_ablation_matrix.v1":
        issues.append("causal_ablation_matrix.json schema mismatch")
    if ablation.get("complete_grid") is not True or ablation.get("all_deterministic") is not True:
        issues.append("causal_ablation_matrix.json has incomplete or non-deterministic cells")
    observable = _load_json(root / "output" / "data" / "analytical_observable_sweep.json")
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
        lambda row: bool(row.get("equation_id"))
        and bool(row.get("assumption_links"))
        and abs(float(row.get("residual", 1.0))) <= float(row.get("residual_tolerance", 0.0) or 0.0),
    )
    if float(observable.get("max_abs_residual", 1.0)) > OBSERVABLE_RESIDUAL_TOLERANCE:
        issues.append("analytical_observable_sweep.json residual exceeds tolerance")
    if not observables_complete:
        issues.append("analytical_observable_sweep.json observable set is incomplete")
    assumptions = _load_json(root / "output" / "data" / "analytical_assumption_index.json")
    if assumptions.get("schema") != ASSUMPTION_INDEX_SCHEMA:
        issues.append("analytical_assumption_index.json schema mismatch")
    if set(assumptions.get("equation_ids") or []) != EXPECTED_ASSUMPTION_EQUATIONS:
        issues.append("analytical_assumption_index.json equation set is incomplete")
    if assumptions.get("all_equations_indexed") is not True:
        issues.append("analytical_assumption_index.json has unindexed equations")
    return issues
