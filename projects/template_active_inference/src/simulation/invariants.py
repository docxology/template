"""Simulation-track invariants for pymdp T-maze artifacts."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

InvariantFn = Callable[[Path], bool]


def _load_summary(root: Path) -> dict[str, Any]:
    path = root / "output" / "data" / "si_tmaze_summary.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_trace(root: Path) -> list[dict[str, Any]]:
    path = root / "output" / "data" / "si_tmaze_trace.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("steps") or [])


def inv_belief_entropy_finite(root: Path) -> bool:
    summary = _load_summary(root)
    entropy = float(summary.get("mean_belief_entropy", -1.0))
    return np.isfinite(entropy) and entropy >= 0.0


def inv_actions_length_matches_steps(root: Path) -> bool:
    summary = _load_summary(root)
    steps = int(summary.get("steps", 0))
    actions = summary.get("actions") or []
    return steps >= 1 and len(actions) == steps


def inv_observations_in_obs_space(root: Path) -> bool:
    summary = _load_summary(root)
    config = summary.get("config") or {}
    n_obs = int((config.get("tmaze") or {}).get("num_obs", 2))
    observations = summary.get("observations") or []
    return all(0 <= int(obs) < n_obs for obs in observations)


def inv_policy_len_matches_config(root: Path) -> bool:
    summary = _load_summary(root)
    config = summary.get("config") or {}
    expected = int(config.get("policy_len", config.get("horizon", 2)))
    return int(summary.get("policy_len", expected)) == expected


def inv_goal_reached(root: Path) -> bool:
    summary = _load_summary(root)
    if "goal_reached" in summary:
        return bool(summary["goal_reached"])
    observations = summary.get("observations") or []
    if not observations:
        return False
    goal_state = int((summary.get("config") or {}).get("tmaze", {}).get("num_obs", 2)) - 1
    return int(observations[-1]) == goal_state


def inv_trace_step_count_matches_summary(root: Path) -> bool:
    summary = _load_summary(root)
    trace = _load_trace(root)
    return len(trace) == int(summary.get("steps", 0))


SIMULATION_INVARIANTS: dict[str, InvariantFn] = {
    "belief_entropy_finite": inv_belief_entropy_finite,
    "actions_length_matches_steps": inv_actions_length_matches_steps,
    "observations_in_obs_space": inv_observations_in_obs_space,
    "policy_len_matches_config": inv_policy_len_matches_config,
    "goal_reached": inv_goal_reached,
    "trace_step_count_matches_summary": inv_trace_step_count_matches_summary,
}


def run_simulation_invariants(project_root: Path) -> dict[str, bool]:
    root = project_root.resolve()
    return {name: fn(root) for name, fn in SIMULATION_INVARIANTS.items()}


def build_merged_invariants_payload(
    project_root: Path,
    *,
    analytical_results: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Single SSOT for merged analytical + simulation invariant reports."""
    from analytical.invariants import run_invariants

    root = project_root.resolve()
    inv_results = analytical_results if analytical_results is not None else run_invariants()
    payload: dict[str, Any] = {
        "invariants": inv_results,
        "all_pass": all(inv_results.values()),
    }
    inv_path = root / "output" / "reports" / "invariants.json"
    existing: dict[str, Any] = {}
    if inv_path.is_file():
        existing = json.loads(inv_path.read_text(encoding="utf-8"))
    si_summary = root / "output" / "data" / "si_tmaze_summary.json"
    if si_summary.is_file():
        simulation = run_simulation_invariants(root)
        payload["simulation"] = simulation
        payload["all_pass"] = all(inv_results.values()) and all(simulation.values())
    elif existing.get("simulation"):
        simulation = existing["simulation"]
        payload["simulation"] = simulation
        payload["all_pass"] = bool(payload["all_pass"]) and all(simulation.values())
    return payload


def write_simulation_invariants(project_root: Path) -> Path:
    root = project_root.resolve()
    results = run_simulation_invariants(root)
    out = root / "output" / "reports" / "si_invariants.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"invariants": results, "all_pass": all(results.values())}
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def merge_simulation_into_invariants_report(project_root: Path) -> Path:
    root = project_root.resolve()
    inv_path = root / "output" / "reports" / "invariants.json"
    analytical: dict[str, bool] | None = None
    if inv_path.exists():
        data = json.loads(inv_path.read_text(encoding="utf-8"))
        raw = data.get("invariants") or {}
        if raw:
            analytical = {str(k): bool(v) for k, v in raw.items()}
    payload = build_merged_invariants_payload(root, analytical_results=analytical)
    inv_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return inv_path
