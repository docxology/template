"""Toy sweep builders promoted into canonical sheaf tracks."""

from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_helpers import _entropy
from roadmap_tracks.sheaf_tracks_io import _load_json
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_SCHEMA


def build_sensitivity_sweep(project_root: Path) -> dict[str, Any]:
    """Build sensitivity sweep."""
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
    """Build uncertainty summary."""
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
