"""Statistics derived from pymdp simulation artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _adjacent_switch_count(values: list[Any]) -> int:
    return sum(1 for prev, cur in zip(values, values[1:], strict=False) if prev != cur)


def _entropy_stats(trace_steps: list[dict[str, Any]]) -> dict[str, float]:
    entropies = [float(step.get("belief_entropy", 0.0)) for step in trace_steps]
    if not entropies:
        return {
            "entropy_min": 0.0,
            "entropy_max": 0.0,
            "entropy_mean": 0.0,
            "entropy_initial": 0.0,
            "entropy_terminal": 0.0,
            "entropy_drop": 0.0,
            "entropy_span": 0.0,
            "entropy_auc": 0.0,
            "entropy_monotone_nonincreasing": True,
        }
    return {
        "entropy_min": min(entropies),
        "entropy_max": max(entropies),
        "entropy_mean": sum(entropies) / len(entropies),
        "entropy_initial": entropies[0],
        "entropy_terminal": entropies[-1],
        "entropy_drop": entropies[0] - entropies[-1],
        "entropy_span": max(entropies) - min(entropies),
        "entropy_auc": sum(entropies),
        "entropy_monotone_nonincreasing": all(
            cur <= prev + 1e-12 for prev, cur in zip(entropies, entropies[1:], strict=False)
        ),
    }


def summarize_si_trace(trace: Mapping[str, Any], summary: Mapping[str, Any]) -> dict[str, Any]:
    """Process summarize si trace."""
    steps = list(trace.get("steps") or [])
    actions = list(summary.get("actions") or [step.get("action") for step in steps if "action" in step])
    observations = list(summary.get("observations") or [step.get("obs") for step in steps if "obs" in step])
    goal_state = int((summary.get("config") or {}).get("tmaze", {}).get("num_obs", 2)) - 1
    goal_reached = bool(observations and int(observations[-1]) == goal_state)
    if "goal_reached" in summary:
        goal_reached = bool(summary["goal_reached"])
    step_count = int(summary.get("steps", len(steps)))
    action_switch_count = _adjacent_switch_count(actions)
    denominator = max(1, len(actions) - 1)
    stats = {
        "steps": step_count,
        "action_diversity": len(set(actions)),
        "action_switch_count": action_switch_count,
        "action_switch_rate": action_switch_count / denominator,
        "observation_diversity": len(set(observations)),
        "terminal_observation": int(observations[-1]) if observations else None,
        "goal_reached": goal_reached,
        "trace_step_count": len(steps),
        "trace_summary_steps_match": step_count == len(steps),
        "policy_posterior_available_steps": sum(1 for step in steps if step.get("policy_posterior_available")),
        "expected_free_energy_available_steps": sum(1 for step in steps if step.get("expected_free_energy_available")),
        "finite_trace": all(float(step.get("belief_entropy", 0.0)) >= 0.0 for step in steps),
        **_entropy_stats(steps),
    }
    return stats


def load_si_artifacts(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load si artifacts from a file."""
    root = project_root.resolve()
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    summary: dict[str, Any] = {}
    trace: dict[str, Any] = {"steps": []}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if trace_path.exists():
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    return summary, trace
